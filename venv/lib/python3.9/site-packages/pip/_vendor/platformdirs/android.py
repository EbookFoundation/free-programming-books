"""Android."""

from __future__ import annotations

import os
import re
import sys
from functools import lru_cache
from typing import TYPE_CHECKING, cast

from .api import PlatformDirsABC


class Android(PlatformDirsABC):
    """
    Follows the guidance `from here <https://android.stackexchange.com/a/216132>`_.

    Makes use of the `appname <platformdirs.api.PlatformDirsABC.appname>`, `version
    <platformdirs.api.PlatformDirsABC.version>`, `ensure_exists <platformdirs.api.PlatformDirsABC.ensure_exists>`.

    """

    @property
    def user_data_dir(self) -> str:
        """:return: data directory tied to the user, e.g. ``/data/user/<userid>/<packagename>/files/<AppName>``"""
        return self._append_app_name_and_version(cast("str", _android_folder()), "files")

    @property
    def site_data_dir(self) -> str:
        """:return: data directory shared by users, same as `user_data_dir`"""
        return self.user_data_dir

    @property
    def user_config_dir(self) -> str:
        """
        :return: config directory tied to the user, e.g. \
        ``/data/user/<userid>/<packagename>/shared_prefs/<AppName>``
        """
        return self._append_app_name_and_version(cast("str", _android_folder()), "shared_prefs")

    @property
    def site_config_dir(self) -> str:
        """:return: config directory shared by the users, same as `user_config_dir`"""
        return self.user_config_dir

    @property
    def user_cache_dir(self) -> str:
        """:return: cache directory tied to the user, e.g.,``/data/user/<userid>/<packagename>/cache/<AppName>``"""
        return self._append_app_name_and_version(cast("str", _android_folder()), "cache")

    @property
    def site_cache_dir(self) -> str:
        """:return: cache directory shared by users, same as `user_cache_dir`"""
        return self.user_cache_dir

    @property
    def user_state_dir(self) -> str:
        """:return: state directory tied to the user, same as `user_data_dir`"""
        return self.user_data_dir

    @property
    def user_log_dir(self) -> str:
        """
        :return: log directory tied to the user, same as `user_cache_dir` if not opinionated else ``log`` in it,
          e.g. ``/data/user/<userid>/<packagename>/cache/<AppName>/log``
        """
        path = self.user_cache_dir
        if self.opinion:
            path = os.path.join(path, "log")  # noqa: PTH118
        return path

    @property
    def user_documents_dir(self) -> str:
        """:return: documents directory tied to the user e.g. ``/storage/emulated/0/Documents``"""
        return _android_documents_folder()

    @property
    def user_downloads_dir(self) -> str:
        """:return: downloads directory tied to the user e.g. ``/storage/emulated/0/Downloads``"""
        return _android_downloads_folder()

    @property
    def user_pictures_dir(self) -> str:
        """:return: pictures directory tied to the user e.g. ``/storage/emulated/0/Pictures``"""
        return _android_pictures_folder()

    @property
    def user_videos_dir(self) -> str:
        """:return: videos directory tied to the user e.g. ``/storage/emulated/0/DCIM/Camera``"""
        return _android_videos_folder()

    @property
    def user_music_dir(self) -> str:
        """:return: music directory tied to the user e.g. ``/storage/emulated/0/Music``"""
        return _android_music_folder()

    @property
    def user_desktop_dir(self) -> str:
        """:return: desktop directory tied to the user e.g. ``/storage/emulated/0/Desktop``"""
        return "/storage/emulated/0/Desktop"

    @property
    def user_runtime_dir(self) -> str:
        """
        :return: runtime directory tied to the user, same as `user_cache_dir` if not opinionated else ``tmp`` in it,
          e.g. ``/data/user/<userid>/<packagename>/cache/<AppName>/tmp``
        """
        path = self.user_cache_dir
        if self.opinion:
            path = os.path.join(path, "tmp")  # noqa: PTH118
        return path

    @property
    def site_runtime_dir(self) -> str:
        """:return: runtime directory shared by users, same as `user_runtime_dir`"""
        return self.user_runtime_dir


@lru_cache(maxsize=1)
def _android_folder() -> str | None:  # noqa: C901
    """:return: base folder for the Android OS or None if it cannot be found"""
    result: str | None = None
    # type checker isn't happy with our "import android", just don't do this when type checking see
    # https://stackoverflow.com/a/61394121
    if not TYPE_CHECKING:
        try:
            # First try to get a path to android app using python4android (if available)...
            from android import mActivity  # noqa: PLC0415

            context = cast("android.content.Context", mActivity.getApplicationContext())  # noqa: F821
            result = context.getFilesDir().getParentFile().getAbsolutePath()
        except Exception:  # noqa: BLE001
            result = None
    if result is None:
        try:
            # ...and fall back to using plain pyjnius, if python4android isn't available or doesn't deliver any useful
            # result...
            from jnius import autoclass  # noqa: PLC0415

            context = autoclass("android.content.Context")
            result = context.getFilesDir().getParentFile().getAbsolutePath()
        except Exception:  # noqa: BLE001
            result = None
    if result is None:
        # and if that fails, too, find an android folder looking at path on the sys.path
        # warning: only works for apps installed under /data, not adopted storage etc.
        pattern = re.compile(r"/data/(data|user/\d+)/(.+)/files")
        for path in sys.path:
            if pattern.match(path):
                result = path.split("/files")[0]
                break
        else:
            result = None
    if result is None:
        # one last try: find an android folder looking at path on the sys.path taking adopted storage paths into
        # account
        pattern = re.compile(r"/mnt/expand/[a-fA-F0-9-]{36}/(data|user/\d+)/(.+)/files")
        for path in sys.path:
            if pattern.match(path):
                result = path.split("/files")[0]
                break
        else:
            result = None
    return result


@lru_cache(maxsize=1)
def _android_documents_folder() -> str:
    """:return: documents folder for the Android OS"""
    # Get directories with pyjnius
    try:
        from jnius import autoclass  # noqa: PLC0415

        context = autoclass("android.content.Context")
        environment = autoclass("android.os.Environment")
        documents_dir: str = context.getExternalFilesDir(environment.DIRECTORY_DOCUMENTS).getAbsolutePath()
    except Exception:  # noqa: BLE001
        documents_dir = "/storage/emulated/0/Documents"

    return documents_dir


@lru_cache(maxsize=1)
def _android_downloads_folder() -> str:
    """:return: downloads folder for the Android OS"""
    # Get directories with pyjnius
    try:
        from jnius import autoclass  # noqa: PLC0415

        context = autoclass("android.content.Context")
        environment = autoclass("android.os.Environment")
        downloads_dir: str = context.getExternalFilesDir(environment.DIRECTORY_DOWNLOADS).getAbsolutePath()
    except Exception:  # noqa: BLE001
        downloads_dir = "/storage/emulated/0/Downloads"

    return downloads_dir


@lru_cache(maxsize=1)
def _android_pictures_folder() -> str:
    """:return: pictures folder for the Android OS"""
    # Get directories with pyjnius
    try:
        from jnius import autoclass  # noqa: PLC0415

        context = autoclass("android.content.Context")
        environment = autoclass("android.os.Environment")
        pictures_dir: str = context.getExternalFilesDir(environment.DIRECTORY_PICTURES).getAbsolutePath()
    except Exception:  # noqa: BLE001
        pictures_dir = "/storage/emulated/0/Pictures"

    return pictures_dir


@lru_cache(maxsize=1)
def _android_videos_folder() -> str:
    """:return: videos folder for the Android OS"""
    # Get directories with pyjnius
    try:
        from jnius import autoclass  # noqa: PLC0415

        context = autoclass("android.content.Context")
        environment = autoclass("android.os.Environment")
        videos_dir: str = context.getExternalFilesDir(environment.DIRECTORY_DCIM).getAbsolutePath()
    except Exception:  # noqa: BLE001
        videos_dir = "/storage/emulated/0/DCIM/Camera"

    return videos_dir


@lru_cache(maxsize=1)
def _android_music_folder() -> str:
    """:return: music folder for the Android OS"""
    # Get directories with pyjnius
    try:
        from jnius import autoclass  # noqa: PLC0415

        context = autoclass("android.content.Context")
        environment = autoclass("android.os.Environment")
        music_dir: str = context.getExternalFilesDir(environment.DIRECTORY_MUSIC).getAbsolutePath()
    except Exception:  # noqa: BLE001
        music_dir = "/storage/emulated/0/Music"

    return music_dir


__all__ = [
    "Android",
]
