"""Exceptions used throughout package.

This module MUST NOT try to import from anything within `pip._internal` to
operate. This is expected to be importable from any/all files within the
subpackage and, thus, should not depend on them.
"""

from __future__ import annotations

import configparser
import contextlib
import locale
import logging
import pathlib
import re
import sys
from collections.abc import Iterator
from itertools import chain, groupby, repeat
from typing import TYPE_CHECKING, Literal

from pip._vendor.packaging.requirements import InvalidRequirement
from pip._vendor.packaging.version import InvalidVersion
from pip._vendor.rich.console import Console, ConsoleOptions, RenderResult
from pip._vendor.rich.markup import escape
from pip._vendor.rich.text import Text

if TYPE_CHECKING:
    from hashlib import _Hash

    from pip._vendor.requests.models import Request, Response

    from pip._internal.metadata import BaseDistribution
    from pip._internal.network.download import _FileDownload
    from pip._internal.req.req_install import InstallRequirement

logger = logging.getLogger(__name__)


#
# Scaffolding
#
def _is_kebab_case(s: str) -> bool:
    return re.match(r"^[a-z]+(-[a-z]+)*$", s) is not None


def _prefix_with_indent(
    s: Text | str,
    console: Console,
    *,
    prefix: str,
    indent: str,
) -> Text:
    if isinstance(s, Text):
        text = s
    else:
        text = console.render_str(s)

    return console.render_str(prefix, overflow="ignore") + console.render_str(
        f"\n{indent}", overflow="ignore"
    ).join(text.split(allow_blank=True))


class PipError(Exception):
    """The base pip error."""


class DiagnosticPipError(PipError):
    """An error, that presents diagnostic information to the user.

    This contains a bunch of logic, to enable pretty presentation of our error
    messages. Each error gets a unique reference. Each error can also include
    additional context, a hint and/or a note -- which are presented with the
    main error message in a consistent style.

    This is adapted from the error output styling in `sphinx-theme-builder`.
    """

    reference: str

    def __init__(
        self,
        *,
        kind: Literal["error", "warning"] = "error",
        reference: str | None = None,
        message: str | Text,
        context: str | Text | None,
        hint_stmt: str | Text | None,
        note_stmt: str | Text | None = None,
        link: str | None = None,
    ) -> None:
        # Ensure a proper reference is provided.
        if reference is None:
            assert hasattr(self, "reference"), "error reference not provided!"
            reference = self.reference
        assert _is_kebab_case(reference), "error reference must be kebab-case!"

        self.kind = kind
        self.reference = reference

        self.message = message
        self.context = context

        self.note_stmt = note_stmt
        self.hint_stmt = hint_stmt

        self.link = link

        super().__init__(f"<{self.__class__.__name__}: {self.reference}>")

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__}("
            f"reference={self.reference!r}, "
            f"message={self.message!r}, "
            f"context={self.context!r}, "
            f"note_stmt={self.note_stmt!r}, "
            f"hint_stmt={self.hint_stmt!r}"
            ")>"
        )

    def __rich_console__(
        self,
        console: Console,
        options: ConsoleOptions,
    ) -> RenderResult:
        colour = "red" if self.kind == "error" else "yellow"

        yield f"[{colour} bold]{self.kind}[/]: [bold]{self.reference}[/]"
        yield ""

        if not options.ascii_only:
            # Present the main message, with relevant context indented.
            if self.context is not None:
                yield _prefix_with_indent(
                    self.message,
                    console,
                    prefix=f"[{colour}]×[/] ",
                    indent=f"[{colour}]│[/] ",
                )
                yield _prefix_with_indent(
                    self.context,
                    console,
                    prefix=f"[{colour}]╰─>[/] ",
                    indent=f"[{colour}]   [/] ",
                )
            else:
                yield _prefix_with_indent(
                    self.message,
                    console,
                    prefix="[red]×[/] ",
                    indent="  ",
                )
        else:
            yield self.message
            if self.context is not None:
                yield ""
                yield self.context

        if self.note_stmt is not None or self.hint_stmt is not None:
            yield ""

        if self.note_stmt is not None:
            yield _prefix_with_indent(
                self.note_stmt,
                console,
                prefix="[magenta bold]note[/]: ",
                indent="      ",
            )
        if self.hint_stmt is not None:
            yield _prefix_with_indent(
                self.hint_stmt,
                console,
                prefix="[cyan bold]hint[/]: ",
                indent="      ",
            )

        if self.link is not None:
            yield ""
            yield f"Link: {self.link}"


#
# Actual Errors
#
class ConfigurationError(PipError):
    """General exception in configuration"""


class InstallationError(PipError):
    """General exception during installation"""


class MissingPyProjectBuildRequires(DiagnosticPipError):
    """Raised when pyproject.toml has `build-system`, but no `build-system.requires`."""

    reference = "missing-pyproject-build-system-requires"

    def __init__(self, *, package: str) -> None:
        super().__init__(
            message=f"Can not process {escape(package)}",
            context=Text(
                "This package has an invalid pyproject.toml file.\n"
                "The [build-system] table is missing the mandatory `requires` key."
            ),
            note_stmt="This is an issue with the package mentioned above, not pip.",
            hint_stmt=Text("See PEP 518 for the detailed specification."),
        )


class InvalidPyProjectBuildRequires(DiagnosticPipError):
    """Raised when pyproject.toml an invalid `build-system.requires`."""

    reference = "invalid-pyproject-build-system-requires"

    def __init__(self, *, package: str, reason: str) -> None:
        super().__init__(
            message=f"Can not process {escape(package)}",
            context=Text(
                "This package has an invalid `build-system.requires` key in "
                f"pyproject.toml.\n{reason}"
            ),
            note_stmt="This is an issue with the package mentioned above, not pip.",
            hint_stmt=Text("See PEP 518 for the detailed specification."),
        )


class NoneMetadataError(PipError):
    """Raised when accessing a Distribution's "METADATA" or "PKG-INFO".

    This signifies an inconsistency, when the Distribution claims to have
    the metadata file (if not, raise ``FileNotFoundError`` instead), but is
    not actually able to produce its content. This may be due to permission
    errors.
    """

    def __init__(
        self,
        dist: BaseDistribution,
        metadata_name: str,
    ) -> None:
        """
        :param dist: A Distribution object.
        :param metadata_name: The name of the metadata being accessed
            (can be "METADATA" or "PKG-INFO").
        """
        self.dist = dist
        self.metadata_name = metadata_name

    def __str__(self) -> str:
        # Use `dist` in the error message because its stringification
        # includes more information, like the version and location.
        return f"None {self.metadata_name} metadata found for distribution: {self.dist}"


class UserInstallationInvalid(InstallationError):
    """A --user install is requested on an environment without user site."""

    def __str__(self) -> str:
        return "User base directory is not specified"


class InvalidSchemeCombination(InstallationError):
    def __str__(self) -> str:
        before = ", ".join(str(a) for a in self.args[:-1])
        return f"Cannot set {before} and {self.args[-1]} together"


class DistributionNotFound(InstallationError):
    """Raised when a distribution cannot be found to satisfy a requirement"""


class RequirementsFileParseError(InstallationError):
    """Raised when a general error occurs parsing a requirements file line."""


class BestVersionAlreadyInstalled(PipError):
    """Raised when the most up-to-date version of a package is already
    installed."""


class BadCommand(PipError):
    """Raised when virtualenv or a command is not found"""


class CommandError(PipError):
    """Raised when there is an error in command-line arguments"""


class PreviousBuildDirError(PipError):
    """Raised when there's a previous conflicting build directory"""


class NetworkConnectionError(PipError):
    """HTTP connection error"""

    def __init__(
        self,
        error_msg: str,
        response: Response | None = None,
        request: Request | None = None,
    ) -> None:
        """
        Initialize NetworkConnectionError with  `request` and `response`
        objects.
        """
        self.response = response
        self.request = request
        self.error_msg = error_msg
        if (
            self.response is not None
            and not self.request
            and hasattr(response, "request")
        ):
            self.request = self.response.request
        super().__init__(error_msg, response, request)

    def __str__(self) -> str:
        return str(self.error_msg)


class InvalidWheelFilename(InstallationError):
    """Invalid wheel filename."""


class UnsupportedWheel(InstallationError):
    """Unsupported wheel."""


class InvalidWheel(InstallationError):
    """Invalid (e.g. corrupt) wheel."""

    def __init__(self, location: str, name: str):
        self.location = location
        self.name = name

    def __str__(self) -> str:
        return f"Wheel '{self.name}' located at {self.location} is invalid."


class MetadataInconsistent(InstallationError):
    """Built metadata contains inconsistent information.

    This is raised when the metadata contains values (e.g. name and version)
    that do not match the information previously obtained from sdist filename,
    user-supplied ``#egg=`` value, or an install requirement name.
    """

    def __init__(
        self, ireq: InstallRequirement, field: str, f_val: str, m_val: str
    ) -> None:
        self.ireq = ireq
        self.field = field
        self.f_val = f_val
        self.m_val = m_val

    def __str__(self) -> str:
        return (
            f"Requested {self.ireq} has inconsistent {self.field}: "
            f"expected {self.f_val!r}, but metadata has {self.m_val!r}"
        )


class MetadataInvalid(InstallationError):
    """Metadata is invalid."""

    def __init__(self, ireq: InstallRequirement, error: str) -> None:
        self.ireq = ireq
        self.error = error

    def __str__(self) -> str:
        return f"Requested {self.ireq} has invalid metadata: {self.error}"


class InstallationSubprocessError(DiagnosticPipError, InstallationError):
    """A subprocess call failed."""

    reference = "subprocess-exited-with-error"

    def __init__(
        self,
        *,
        command_description: str,
        exit_code: int,
        output_lines: list[str] | None,
    ) -> None:
        if output_lines is None:
            output_prompt = Text("See above for output.")
        else:
            output_prompt = (
                Text.from_markup(f"[red][{len(output_lines)} lines of output][/]\n")
                + Text("".join(output_lines))
                + Text.from_markup(R"[red]\[end of output][/]")
            )

        super().__init__(
            message=(
                f"[green]{escape(command_description)}[/] did not run successfully.\n"
                f"exit code: {exit_code}"
            ),
            context=output_prompt,
            hint_stmt=None,
            note_stmt=(
                "This error originates from a subprocess, and is likely not a "
                "problem with pip."
            ),
        )

        self.command_description = command_description
        self.exit_code = exit_code

    def __str__(self) -> str:
        return f"{self.command_description} exited with {self.exit_code}"


class MetadataGenerationFailed(InstallationSubprocessError, InstallationError):
    reference = "metadata-generation-failed"

    def __init__(
        self,
        *,
        package_details: str,
    ) -> None:
        super(InstallationSubprocessError, self).__init__(
            message="Encountered error while generating package metadata.",
            context=escape(package_details),
            hint_stmt="See above for details.",
            note_stmt="This is an issue with the package mentioned above, not pip.",
        )

    def __str__(self) -> str:
        return "metadata generation failed"


class HashErrors(InstallationError):
    """Multiple HashError instances rolled into one for reporting"""

    def __init__(self) -> None:
        self.errors: list[HashError] = []

    def append(self, error: HashError) -> None:
        self.errors.append(error)

    def __str__(self) -> str:
        lines = []
        self.errors.sort(key=lambda e: e.order)
        for cls, errors_of_cls in groupby(self.errors, lambda e: e.__class__):
            lines.append(cls.head)
            lines.extend(e.body() for e in errors_of_cls)
        if lines:
            return "\n".join(lines)
        return ""

    def __bool__(self) -> bool:
        return bool(self.errors)


class HashError(InstallationError):
    """
    A failure to verify a package against known-good hashes

    :cvar order: An int sorting hash exception classes by difficulty of
        recovery (lower being harder), so the user doesn't bother fretting
        about unpinned packages when he has deeper issues, like VCS
        dependencies, to deal with. Also keeps error reports in a
        deterministic order.
    :cvar head: A section heading for display above potentially many
        exceptions of this kind
    :ivar req: The InstallRequirement that triggered this error. This is
        pasted on after the exception is instantiated, because it's not
        typically available earlier.

    """

    req: InstallRequirement | None = None
    head = ""
    order: int = -1

    def body(self) -> str:
        """Return a summary of me for display under the heading.

        This default implementation simply prints a description of the
        triggering requirement.

        :param req: The InstallRequirement that provoked this error, with
            its link already populated by the resolver's _populate_link().

        """
        return f"    {self._requirement_name()}"

    def __str__(self) -> str:
        return f"{self.head}\n{self.body()}"

    def _requirement_name(self) -> str:
        """Return a description of the requirement that triggered me.

        This default implementation returns long description of the req, with
        line numbers

        """
        return str(self.req) if self.req else "unknown package"


class VcsHashUnsupported(HashError):
    """A hash was provided for a version-control-system-based requirement, but
    we don't have a method for hashing those."""

    order = 0
    head = (
        "Can't verify hashes for these requirements because we don't "
        "have a way to hash version control repositories:"
    )


class DirectoryUrlHashUnsupported(HashError):
    """A hash was provided for a version-control-system-based requirement, but
    we don't have a method for hashing those."""

    order = 1
    head = (
        "Can't verify hashes for these file:// requirements because they "
        "point to directories:"
    )


class HashMissing(HashError):
    """A hash was needed for a requirement but is absent."""

    order = 2
    head = (
        "Hashes are required in --require-hashes mode, but they are "
        "missing from some requirements. Here is a list of those "
        "requirements along with the hashes their downloaded archives "
        "actually had. Add lines like these to your requirements files to "
        "prevent tampering. (If you did not enable --require-hashes "
        "manually, note that it turns on automatically when any package "
        "has a hash.)"
    )

    def __init__(self, gotten_hash: str) -> None:
        """
        :param gotten_hash: The hash of the (possibly malicious) archive we
            just downloaded
        """
        self.gotten_hash = gotten_hash

    def body(self) -> str:
        # Dodge circular import.
        from pip._internal.utils.hashes import FAVORITE_HASH

        package = None
        if self.req:
            # In the case of URL-based requirements, display the original URL
            # seen in the requirements file rather than the package name,
            # so the output can be directly copied into the requirements file.
            package = (
                self.req.original_link
                if self.req.is_direct
                # In case someone feeds something downright stupid
                # to InstallRequirement's constructor.
                else getattr(self.req, "req", None)
            )
        return "    {} --hash={}:{}".format(
            package or "unknown package", FAVORITE_HASH, self.gotten_hash
        )


class HashUnpinned(HashError):
    """A requirement had a hash specified but was not pinned to a specific
    version."""

    order = 3
    head = (
        "In --require-hashes mode, all requirements must have their "
        "versions pinned with ==. These do not:"
    )


class HashMismatch(HashError):
    """
    Distribution file hash values don't match.

    :ivar package_name: The name of the package that triggered the hash
        mismatch. Feel free to write to this after the exception is raise to
        improve its error message.

    """

    order = 4
    head = (
        "THESE PACKAGES DO NOT MATCH THE HASHES FROM THE REQUIREMENTS "
        "FILE. If you have updated the package versions, please update "
        "the hashes. Otherwise, examine the package contents carefully; "
        "someone may have tampered with them."
    )

    def __init__(self, allowed: dict[str, list[str]], gots: dict[str, _Hash]) -> None:
        """
        :param allowed: A dict of algorithm names pointing to lists of allowed
            hex digests
        :param gots: A dict of algorithm names pointing to hashes we
            actually got from the files under suspicion
        """
        self.allowed = allowed
        self.gots = gots

    def body(self) -> str:
        return f"    {self._requirement_name()}:\n{self._hash_comparison()}"

    def _hash_comparison(self) -> str:
        """
        Return a comparison of actual and expected hash values.

        Example::

               Expected sha256 abcdeabcdeabcdeabcdeabcdeabcdeabcdeabcdeabcde
                            or 123451234512345123451234512345123451234512345
                    Got        bcdefbcdefbcdefbcdefbcdefbcdefbcdefbcdefbcdef

        """

        def hash_then_or(hash_name: str) -> chain[str]:
            # For now, all the decent hashes have 6-char names, so we can get
            # away with hard-coding space literals.
            return chain([hash_name], repeat("    or"))

        lines: list[str] = []
        for hash_name, expecteds in self.allowed.items():
            prefix = hash_then_or(hash_name)
            lines.extend((f"        Expected {next(prefix)} {e}") for e in expecteds)
            lines.append(
                f"             Got        {self.gots[hash_name].hexdigest()}\n"
            )
        return "\n".join(lines)


class UnsupportedPythonVersion(InstallationError):
    """Unsupported python version according to Requires-Python package
    metadata."""


class ConfigurationFileCouldNotBeLoaded(ConfigurationError):
    """When there are errors while loading a configuration file"""

    def __init__(
        self,
        reason: str = "could not be loaded",
        fname: str | None = None,
        error: configparser.Error | None = None,
    ) -> None:
        super().__init__(error)
        self.reason = reason
        self.fname = fname
        self.error = error

    def __str__(self) -> str:
        if self.fname is not None:
            message_part = f" in {self.fname}."
        else:
            assert self.error is not None
            message_part = f".\n{self.error}\n"
        return f"Configuration file {self.reason}{message_part}"


_DEFAULT_EXTERNALLY_MANAGED_ERROR = f"""\
The Python environment under {sys.prefix} is managed externally, and may not be
manipulated by the user. Please use specific tooling from the distributor of
the Python installation to interact with this environment instead.
"""


class ExternallyManagedEnvironment(DiagnosticPipError):
    """The current environment is externally managed.

    This is raised when the current environment is externally managed, as
    defined by `PEP 668`_. The ``EXTERNALLY-MANAGED`` configuration is checked
    and displayed when the error is bubbled up to the user.

    :param error: The error message read from ``EXTERNALLY-MANAGED``.
    """

    reference = "externally-managed-environment"

    def __init__(self, error: str | None) -> None:
        if error is None:
            context = Text(_DEFAULT_EXTERNALLY_MANAGED_ERROR)
        else:
            context = Text(error)
        super().__init__(
            message="This environment is externally managed",
            context=context,
            note_stmt=(
                "If you believe this is a mistake, please contact your "
                "Python installation or OS distribution provider. "
                "You can override this, at the risk of breaking your Python "
                "installation or OS, by passing --break-system-packages."
            ),
            hint_stmt=Text("See PEP 668 for the detailed specification."),
        )

    @staticmethod
    def _iter_externally_managed_error_keys() -> Iterator[str]:
        # LC_MESSAGES is in POSIX, but not the C standard. The most common
        # platform that does not implement this category is Windows, where
        # using other categories for console message localization is equally
        # unreliable, so we fall back to the locale-less vendor message. This
        # can always be re-evaluated when a vendor proposes a new alternative.
        try:
            category = locale.LC_MESSAGES
        except AttributeError:
            lang: str | None = None
        else:
            lang, _ = locale.getlocale(category)
        if lang is not None:
            yield f"Error-{lang}"
            for sep in ("-", "_"):
                before, found, _ = lang.partition(sep)
                if not found:
                    continue
                yield f"Error-{before}"
        yield "Error"

    @classmethod
    def from_config(
        cls,
        config: pathlib.Path | str,
    ) -> ExternallyManagedEnvironment:
        parser = configparser.ConfigParser(interpolation=None)
        try:
            parser.read(config, encoding="utf-8")
            section = parser["externally-managed"]
            for key in cls._iter_externally_managed_error_keys():
                with contextlib.suppress(KeyError):
                    return cls(section[key])
        except KeyError:
            pass
        except (OSError, UnicodeDecodeError, configparser.ParsingError):
            from pip._internal.utils._log import VERBOSE

            exc_info = logger.isEnabledFor(VERBOSE)
            logger.warning("Failed to read %s", config, exc_info=exc_info)
        return cls(None)


class UninstallMissingRecord(DiagnosticPipError):
    reference = "uninstall-no-record-file"

    def __init__(self, *, distribution: BaseDistribution) -> None:
        installer = distribution.installer
        if not installer or installer == "pip":
            dep = f"{distribution.raw_name}=={distribution.version}"
            hint = Text.assemble(
                "You might be able to recover from this via: ",
                (f"pip install --force-reinstall --no-deps {dep}", "green"),
            )
        else:
            hint = Text(
                f"The package was installed by {installer}. "
                "You should check if it can uninstall the package."
            )

        super().__init__(
            message=Text(f"Cannot uninstall {distribution}"),
            context=(
                "The package's contents are unknown: "
                f"no RECORD file was found for {distribution.raw_name}."
            ),
            hint_stmt=hint,
        )


class LegacyDistutilsInstall(DiagnosticPipError):
    reference = "uninstall-distutils-installed-package"

    def __init__(self, *, distribution: BaseDistribution) -> None:
        super().__init__(
            message=Text(f"Cannot uninstall {distribution}"),
            context=(
                "It is a distutils installed project and thus we cannot accurately "
                "determine which files belong to it which would lead to only a partial "
                "uninstall."
            ),
            hint_stmt=None,
        )


class InvalidInstalledPackage(DiagnosticPipError):
    reference = "invalid-installed-package"

    def __init__(
        self,
        *,
        dist: BaseDistribution,
        invalid_exc: InvalidRequirement | InvalidVersion,
    ) -> None:
        installed_location = dist.installed_location

        if isinstance(invalid_exc, InvalidRequirement):
            invalid_type = "requirement"
        else:
            invalid_type = "version"

        super().__init__(
            message=Text(
                f"Cannot process installed package {dist} "
                + (f"in {installed_location!r} " if installed_location else "")
                + f"because it has an invalid {invalid_type}:\n{invalid_exc.args[0]}"
            ),
            context=(
                "Starting with pip 24.1, packages with invalid "
                f"{invalid_type}s can not be processed."
            ),
            hint_stmt="To proceed this package must be uninstalled.",
        )


class IncompleteDownloadError(DiagnosticPipError):
    """Raised when the downloader receives fewer bytes than advertised
    in the Content-Length header."""

    reference = "incomplete-download"

    def __init__(self, download: _FileDownload) -> None:
        # Dodge circular import.
        from pip._internal.utils.misc import format_size

        assert download.size is not None
        download_status = (
            f"{format_size(download.bytes_received)}/{format_size(download.size)}"
        )
        if download.reattempts:
            retry_status = f"after {download.reattempts + 1} attempts "
            hint = "Use --resume-retries to configure resume attempt limit."
        else:
            # Download retrying is not enabled.
            retry_status = ""
            hint = "Consider using --resume-retries to enable download resumption."
        message = Text(
            f"Download failed {retry_status}because not enough bytes "
            f"were received ({download_status})"
        )

        super().__init__(
            message=message,
            context=f"URL: {download.link.redacted_url}",
            hint_stmt=hint,
            note_stmt="This is an issue with network connectivity, not pip.",
        )


class ResolutionTooDeepError(DiagnosticPipError):
    """Raised when the dependency resolver exceeds the maximum recursion depth."""

    reference = "resolution-too-deep"

    def __init__(self) -> None:
        super().__init__(
            message="Dependency resolution exceeded maximum depth",
            context=(
                "Pip cannot resolve the current dependencies as the dependency graph "
                "is too complex for pip to solve efficiently."
            ),
            hint_stmt=(
                "Try adding lower bounds to constrain your dependencies, "
                "for example: 'package>=2.0.0' instead of just 'package'. "
            ),
            link="https://pip.pypa.io/en/stable/topics/dependency-resolution/#handling-resolution-too-deep-errors",
        )


class InstallWheelBuildError(DiagnosticPipError):
    reference = "failed-wheel-build-for-install"

    def __init__(self, failed: list[InstallRequirement]) -> None:
        super().__init__(
            message=(
                "Failed to build installable wheels for some "
                "pyproject.toml based projects"
            ),
            context=", ".join(r.name for r in failed),  # type: ignore
            hint_stmt=None,
        )
