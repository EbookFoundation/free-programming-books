import sys
from dataclasses import dataclass


@dataclass
class WindowsConsoleFeatures:
    """Windows features available."""

    vt: bool = False
    """The console supports VT codes."""
    truecolor: bool = False
    """The console supports truecolor."""


try:
    import ctypes
    from ctypes import LibraryLoader

    if sys.platform == "win32":
        windll = LibraryLoader(ctypes.WinDLL)
    else:
        windll = None
        raise ImportError("Not windows")

    from pip._vendor.rich._win32_console import (
        ENABLE_VIRTUAL_TERMINAL_PROCESSING,
        GetConsoleMode,
        GetStdHandle,
        LegacyWindowsError,
    )

except (AttributeError, ImportError, ValueError):
    # Fallback if we can't load the Windows DLL
    def get_windows_console_features() -> WindowsConsoleFeatures:
        features = WindowsConsoleFeatures()
        return features

else:

    def get_windows_console_features() -> WindowsConsoleFeatures:
        """Get windows console features.

        Returns:
            WindowsConsoleFeatures: An instance of WindowsConsoleFeatures.
        """
        handle = GetStdHandle()
        try:
            console_mode = GetConsoleMode(handle)
            success = True
        except LegacyWindowsError:
            console_mode = 0
            success = False
        vt = bool(success and console_mode & ENABLE_VIRTUAL_TERMINAL_PROCESSING)
        truecolor = False
        if vt:
            win_version = sys.getwindowsversion()
            truecolor = win_version.major > 10 or (
                win_version.major == 10 and win_version.build >= 15063
            )
        features = WindowsConsoleFeatures(vt=vt, truecolor=truecolor)
        return features


if __name__ == "__main__":
    import platform

    features = get_windows_console_features()
    from pip._vendor.rich import print

    print(f'platform="{platform.system()}"')
    print(repr(features))
