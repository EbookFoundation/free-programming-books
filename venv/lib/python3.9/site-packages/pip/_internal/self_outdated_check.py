from __future__ import annotations

import datetime
import functools
import hashlib
import json
import logging
import optparse
import os.path
import sys
from dataclasses import dataclass
from typing import Any, Callable

from pip._vendor.packaging.version import Version
from pip._vendor.packaging.version import parse as parse_version
from pip._vendor.rich.console import Group
from pip._vendor.rich.markup import escape
from pip._vendor.rich.text import Text

from pip._internal.index.collector import LinkCollector
from pip._internal.index.package_finder import PackageFinder
from pip._internal.metadata import get_default_environment
from pip._internal.models.selection_prefs import SelectionPreferences
from pip._internal.network.session import PipSession
from pip._internal.utils.compat import WINDOWS
from pip._internal.utils.entrypoints import (
    get_best_invocation_for_this_pip,
    get_best_invocation_for_this_python,
)
from pip._internal.utils.filesystem import adjacent_tmp_file, check_path_owner, replace
from pip._internal.utils.misc import (
    ExternallyManagedEnvironment,
    check_externally_managed,
    ensure_dir,
)

_WEEK = datetime.timedelta(days=7)

logger = logging.getLogger(__name__)


def _get_statefile_name(key: str) -> str:
    key_bytes = key.encode()
    name = hashlib.sha224(key_bytes).hexdigest()
    return name


def _convert_date(isodate: str) -> datetime.datetime:
    """Convert an ISO format string to a date.

    Handles the format 2020-01-22T14:24:01Z (trailing Z)
    which is not supported by older versions of fromisoformat.
    """
    return datetime.datetime.fromisoformat(isodate.replace("Z", "+00:00"))


class SelfCheckState:
    def __init__(self, cache_dir: str) -> None:
        self._state: dict[str, Any] = {}
        self._statefile_path = None

        # Try to load the existing state
        if cache_dir:
            self._statefile_path = os.path.join(
                cache_dir, "selfcheck", _get_statefile_name(self.key)
            )
            try:
                with open(self._statefile_path, encoding="utf-8") as statefile:
                    self._state = json.load(statefile)
            except (OSError, ValueError, KeyError):
                # Explicitly suppressing exceptions, since we don't want to
                # error out if the cache file is invalid.
                pass

    @property
    def key(self) -> str:
        return sys.prefix

    def get(self, current_time: datetime.datetime) -> str | None:
        """Check if we have a not-outdated version loaded already."""
        if not self._state:
            return None

        if "last_check" not in self._state:
            return None

        if "pypi_version" not in self._state:
            return None

        # Determine if we need to refresh the state
        last_check = _convert_date(self._state["last_check"])
        time_since_last_check = current_time - last_check
        if time_since_last_check > _WEEK:
            return None

        return self._state["pypi_version"]

    def set(self, pypi_version: str, current_time: datetime.datetime) -> None:
        # If we do not have a path to cache in, don't bother saving.
        if not self._statefile_path:
            return

        # Check to make sure that we own the directory
        if not check_path_owner(os.path.dirname(self._statefile_path)):
            return

        # Now that we've ensured the directory is owned by this user, we'll go
        # ahead and make sure that all our directories are created.
        ensure_dir(os.path.dirname(self._statefile_path))

        state = {
            # Include the key so it's easy to tell which pip wrote the
            # file.
            "key": self.key,
            "last_check": current_time.isoformat(),
            "pypi_version": pypi_version,
        }

        text = json.dumps(state, sort_keys=True, separators=(",", ":"))

        with adjacent_tmp_file(self._statefile_path) as f:
            f.write(text.encode())

        try:
            # Since we have a prefix-specific state file, we can just
            # overwrite whatever is there, no need to check.
            replace(f.name, self._statefile_path)
        except OSError:
            # Best effort.
            pass


@dataclass
class UpgradePrompt:
    old: str
    new: str

    def __rich__(self) -> Group:
        if WINDOWS:
            pip_cmd = f"{get_best_invocation_for_this_python()} -m pip"
        else:
            pip_cmd = get_best_invocation_for_this_pip()

        notice = "[bold][[reset][blue]notice[reset][bold]][reset]"
        return Group(
            Text(),
            Text.from_markup(
                f"{notice} A new release of pip is available: "
                f"[red]{self.old}[reset] -> [green]{self.new}[reset]"
            ),
            Text.from_markup(
                f"{notice} To update, run: "
                f"[green]{escape(pip_cmd)} install --upgrade pip"
            ),
        )


def was_installed_by_pip(pkg: str) -> bool:
    """Checks whether pkg was installed by pip

    This is used not to display the upgrade message when pip is in fact
    installed by system package manager, such as dnf on Fedora.
    """
    dist = get_default_environment().get_distribution(pkg)
    return dist is not None and "pip" == dist.installer


def _get_current_remote_pip_version(
    session: PipSession, options: optparse.Values
) -> str | None:
    # Lets use PackageFinder to see what the latest pip version is
    link_collector = LinkCollector.create(
        session,
        options=options,
        suppress_no_index=True,
    )

    # Pass allow_yanked=False so we don't suggest upgrading to a
    # yanked version.
    selection_prefs = SelectionPreferences(
        allow_yanked=False,
        allow_all_prereleases=False,  # Explicitly set to False
    )

    finder = PackageFinder.create(
        link_collector=link_collector,
        selection_prefs=selection_prefs,
    )
    best_candidate = finder.find_best_candidate("pip").best_candidate
    if best_candidate is None:
        return None

    return str(best_candidate.version)


def _self_version_check_logic(
    *,
    state: SelfCheckState,
    current_time: datetime.datetime,
    local_version: Version,
    get_remote_version: Callable[[], str | None],
) -> UpgradePrompt | None:
    remote_version_str = state.get(current_time)
    if remote_version_str is None:
        remote_version_str = get_remote_version()
        if remote_version_str is None:
            logger.debug("No remote pip version found")
            return None
        state.set(remote_version_str, current_time)

    remote_version = parse_version(remote_version_str)
    logger.debug("Remote version of pip: %s", remote_version)
    logger.debug("Local version of pip:  %s", local_version)

    pip_installed_by_pip = was_installed_by_pip("pip")
    logger.debug("Was pip installed by pip? %s", pip_installed_by_pip)
    if not pip_installed_by_pip:
        return None  # Only suggest upgrade if pip is installed by pip.

    local_version_is_older = (
        local_version < remote_version
        and local_version.base_version != remote_version.base_version
    )
    if local_version_is_older:
        return UpgradePrompt(old=str(local_version), new=remote_version_str)

    return None


def pip_self_version_check(session: PipSession, options: optparse.Values) -> None:
    """Check for an update for pip.

    Limit the frequency of checks to once per week. State is stored either in
    the active virtualenv or in the user's USER_CACHE_DIR keyed off the prefix
    of the pip script path.
    """
    installed_dist = get_default_environment().get_distribution("pip")
    if not installed_dist:
        return
    try:
        check_externally_managed()
    except ExternallyManagedEnvironment:
        return

    upgrade_prompt = _self_version_check_logic(
        state=SelfCheckState(cache_dir=options.cache_dir),
        current_time=datetime.datetime.now(datetime.timezone.utc),
        local_version=installed_dist.version,
        get_remote_version=functools.partial(
            _get_current_remote_pip_version, session, options
        ),
    )
    if upgrade_prompt is not None:
        logger.warning("%s", upgrade_prompt, extra={"rich": True})
