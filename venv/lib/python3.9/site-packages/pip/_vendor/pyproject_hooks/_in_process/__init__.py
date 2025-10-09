"""This is a subpackage because the directory is on sys.path for _in_process.py

The subpackage should stay as empty as possible to avoid shadowing modules that
the backend might import.
"""

import importlib.resources as resources

try:
    resources.files
except AttributeError:
    # Python 3.8 compatibility
    def _in_proc_script_path():
        return resources.path(__package__, "_in_process.py")

else:

    def _in_proc_script_path():
        return resources.as_file(
            resources.files(__package__).joinpath("_in_process.py")
        )
