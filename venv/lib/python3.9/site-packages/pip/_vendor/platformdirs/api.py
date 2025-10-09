"""Base API."""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Literal


class PlatformDirsABC(ABC):  # noqa: PLR0904
    """Abstract base class for platform directories."""

    def __init__(  # noqa: PLR0913, PLR0917
        self,
        appname: str | None = None,
        appauthor: str | Literal[False] | None = None,
        version: str | None = None,
        roaming: bool = False,  # noqa: FBT001, FBT002
        multipath: bool = False,  # noqa: FBT001, FBT002
        opinion: bool = True,  # noqa: FBT001, FBT002
        ensure_exists: bool = False,  # noqa: FBT001, FBT002
    ) -> None:
        """
        Create a new platform directory.

        :param appname: See `appname`.
        :param appauthor: See `appauthor`.
        :param version: See `version`.
        :param roaming: See `roaming`.
        :param multipath: See `multipath`.
        :param opinion: See `opinion`.
        :param ensure_exists: See `ensure_exists`.

        """
        self.appname = appname  #: The name of application.
        self.appauthor = appauthor
        """
        The name of the app author or distributing body for this application.

        Typically, it is the owning company name. Defaults to `appname`. You may pass ``False`` to disable it.

        """
        self.version = version
        """
        An optional version path element to append to the path.

        You might want to use this if you want multiple versions of your app to be able to run independently. If used,
        this would typically be ``<major>.<minor>``.

        """
        self.roaming = roaming
        """
        Whether to use the roaming appdata directory on Windows.

        That means that for users on a Windows network setup for roaming profiles, this user data will be synced on
        login (see
        `here <https://technet.microsoft.com/en-us/library/cc766489(WS.10).aspx>`_).

        """
        self.multipath = multipath
        """
        An optional parameter which indicates that the entire list of data dirs should be returned.

        By default, the first item would only be returned.

        """
        self.opinion = opinion  #: A flag to indicating to use opinionated values.
        self.ensure_exists = ensure_exists
        """
        Optionally create the directory (and any missing parents) upon access if it does not exist.

        By default, no directories are created.

        """

    def _append_app_name_and_version(self, *base: str) -> str:
        params = list(base[1:])
        if self.appname:
            params.append(self.appname)
            if self.version:
                params.append(self.version)
        path = os.path.join(base[0], *params)  # noqa: PTH118
        self._optionally_create_directory(path)
        return path

    def _optionally_create_directory(self, path: str) -> None:
        if self.ensure_exists:
            Path(path).mkdir(parents=True, exist_ok=True)

    def _first_item_as_path_if_multipath(self, directory: str) -> Path:
        if self.multipath:
            # If multipath is True, the first path is returned.
            directory = directory.split(os.pathsep)[0]
        return Path(directory)

    @property
    @abstractmethod
    def user_data_dir(self) -> str:
        """:return: data directory tied to the user"""

    @property
    @abstractmethod
    def site_data_dir(self) -> str:
        """:return: data directory shared by users"""

    @property
    @abstractmethod
    def user_config_dir(self) -> str:
        """:return: config directory tied to the user"""

    @property
    @abstractmethod
    def site_config_dir(self) -> str:
        """:return: config directory shared by the users"""

    @property
    @abstractmethod
    def user_cache_dir(self) -> str:
        """:return: cache directory tied to the user"""

    @property
    @abstractmethod
    def site_cache_dir(self) -> str:
        """:return: cache directory shared by users"""

    @property
    @abstractmethod
    def user_state_dir(self) -> str:
        """:return: state directory tied to the user"""

    @property
    @abstractmethod
    def user_log_dir(self) -> str:
        """:return: log directory tied to the user"""

    @property
    @abstractmethod
    def user_documents_dir(self) -> str:
        """:return: documents directory tied to the user"""

    @property
    @abstractmethod
    def user_downloads_dir(self) -> str:
        """:return: downloads directory tied to the user"""

    @property
    @abstractmethod
    def user_pictures_dir(self) -> str:
        """:return: pictures directory tied to the user"""

    @property
    @abstractmethod
    def user_videos_dir(self) -> str:
        """:return: videos directory tied to the user"""

    @property
    @abstractmethod
    def user_music_dir(self) -> str:
        """:return: music directory tied to the user"""

    @property
    @abstractmethod
    def user_desktop_dir(self) -> str:
        """:return: desktop directory tied to the user"""

    @property
    @abstractmethod
    def user_runtime_dir(self) -> str:
        """:return: runtime directory tied to the user"""

    @property
    @abstractmethod
    def site_runtime_dir(self) -> str:
        """:return: runtime directory shared by users"""

    @property
    def user_data_path(self) -> Path:
        """:return: data path tied to the user"""
        return Path(self.user_data_dir)

    @property
    def site_data_path(self) -> Path:
        """:return: data path shared by users"""
        return Path(self.site_data_dir)

    @property
    def user_config_path(self) -> Path:
        """:return: config path tied to the user"""
        return Path(self.user_config_dir)

    @property
    def site_config_path(self) -> Path:
        """:return: config path shared by the users"""
        return Path(self.site_config_dir)

    @property
    def user_cache_path(self) -> Path:
        """:return: cache path tied to the user"""
        return Path(self.user_cache_dir)

    @property
    def site_cache_path(self) -> Path:
        """:return: cache path shared by users"""
        return Path(self.site_cache_dir)

    @property
    def user_state_path(self) -> Path:
        """:return: state path tied to the user"""
        return Path(self.user_state_dir)

    @property
    def user_log_path(self) -> Path:
        """:return: log path tied to the user"""
        return Path(self.user_log_dir)

    @property
    def user_documents_path(self) -> Path:
        """:return: documents a path tied to the user"""
        return Path(self.user_documents_dir)

    @property
    def user_downloads_path(self) -> Path:
        """:return: downloads path tied to the user"""
        return Path(self.user_downloads_dir)

    @property
    def user_pictures_path(self) -> Path:
        """:return: pictures path tied to the user"""
        return Path(self.user_pictures_dir)

    @property
    def user_videos_path(self) -> Path:
        """:return: videos path tied to the user"""
        return Path(self.user_videos_dir)

    @property
    def user_music_path(self) -> Path:
        """:return: music path tied to the user"""
        return Path(self.user_music_dir)

    @property
    def user_desktop_path(self) -> Path:
        """:return: desktop path tied to the user"""
        return Path(self.user_desktop_dir)

    @property
    def user_runtime_path(self) -> Path:
        """:return: runtime path tied to the user"""
        return Path(self.user_runtime_dir)

    @property
    def site_runtime_path(self) -> Path:
        """:return: runtime path shared by users"""
        return Path(self.site_runtime_dir)

    def iter_config_dirs(self) -> Iterator[str]:
        """:yield: all user and site configuration directories."""
        yield self.user_config_dir
        yield self.site_config_dir

    def iter_data_dirs(self) -> Iterator[str]:
        """:yield: all user and site data directories."""
        yield self.user_data_dir
        yield self.site_data_dir

    def iter_cache_dirs(self) -> Iterator[str]:
        """:yield: all user and site cache directories."""
        yield self.user_cache_dir
        yield self.site_cache_dir

    def iter_runtime_dirs(self) -> Iterator[str]:
        """:yield: all user and site runtime directories."""
        yield self.user_runtime_dir
        yield self.site_runtime_dir

    def iter_config_paths(self) -> Iterator[Path]:
        """:yield: all user and site configuration paths."""
        for path in self.iter_config_dirs():
            yield Path(path)

    def iter_data_paths(self) -> Iterator[Path]:
        """:yield: all user and site data paths."""
        for path in self.iter_data_dirs():
            yield Path(path)

    def iter_cache_paths(self) -> Iterator[Path]:
        """:yield: all user and site cache paths."""
        for path in self.iter_cache_dirs():
            yield Path(path)

    def iter_runtime_paths(self) -> Iterator[Path]:
        """:yield: all user and site runtime paths."""
        for path in self.iter_runtime_dirs():
            yield Path(path)
