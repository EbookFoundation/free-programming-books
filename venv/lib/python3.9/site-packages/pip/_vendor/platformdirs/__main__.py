"""Main entry point."""

from __future__ import annotations

from pip._vendor.platformdirs import PlatformDirs, __version__

PROPS = (
    "user_data_dir",
    "user_config_dir",
    "user_cache_dir",
    "user_state_dir",
    "user_log_dir",
    "user_documents_dir",
    "user_downloads_dir",
    "user_pictures_dir",
    "user_videos_dir",
    "user_music_dir",
    "user_runtime_dir",
    "site_data_dir",
    "site_config_dir",
    "site_cache_dir",
    "site_runtime_dir",
)


def main() -> None:
    """Run the main entry point."""
    app_name = "MyApp"
    app_author = "MyCompany"

    print(f"-- platformdirs {__version__} --")  # noqa: T201

    print("-- app dirs (with optional 'version')")  # noqa: T201
    dirs = PlatformDirs(app_name, app_author, version="1.0")
    for prop in PROPS:
        print(f"{prop}: {getattr(dirs, prop)}")  # noqa: T201

    print("\n-- app dirs (without optional 'version')")  # noqa: T201
    dirs = PlatformDirs(app_name, app_author)
    for prop in PROPS:
        print(f"{prop}: {getattr(dirs, prop)}")  # noqa: T201

    print("\n-- app dirs (without optional 'appauthor')")  # noqa: T201
    dirs = PlatformDirs(app_name)
    for prop in PROPS:
        print(f"{prop}: {getattr(dirs, prop)}")  # noqa: T201

    print("\n-- app dirs (with disabled 'appauthor')")  # noqa: T201
    dirs = PlatformDirs(app_name, appauthor=False)
    for prop in PROPS:
        print(f"{prop}: {getattr(dirs, prop)}")  # noqa: T201


if __name__ == "__main__":
    main()
