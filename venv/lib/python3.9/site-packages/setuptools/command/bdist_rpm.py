import distutils.command.bdist_rpm as orig


class bdist_rpm(orig.bdist_rpm):
    """
    Override the default bdist_rpm behavior to do the following:

    1. Run egg_info to ensure the name and version are properly calculated.
    2. Always run 'install' using --single-version-externally-managed to
       disable eggs in RPM distributions.
    """

    def run(self):
        # ensure distro name is up-to-date
        self.run_command('egg_info')

        orig.bdist_rpm.run(self)

    def _make_spec_file(self):
        spec = orig.bdist_rpm._make_spec_file(self)
        spec = [
            line.replace(
                "setup.py install ",
                "setup.py install --single-version-externally-managed "
            ).replace(
                "%setup",
                "%setup -n %{name}-%{unmangled_version}"
            )
            for line in spec
        ]
        return spec
