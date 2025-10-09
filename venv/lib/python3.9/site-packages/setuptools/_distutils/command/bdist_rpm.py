"""distutils.command.bdist_rpm

Implements the Distutils 'bdist_rpm' command (create RPM source and binary
distributions)."""

import subprocess, sys, os
from distutils.core import Command
from distutils.debug import DEBUG
from distutils.file_util import write_file
from distutils.errors import *
from distutils.sysconfig import get_python_version
from distutils import log

class bdist_rpm(Command):

    description = "create an RPM distribution"

    user_options = [
        ('bdist-base=', None,
         "base directory for creating built distributions"),
        ('rpm-base=', None,
         "base directory for creating RPMs (defaults to \"rpm\" under "
         "--bdist-base; must be specified for RPM 2)"),
        ('dist-dir=', 'd',
         "directory to put final RPM files in "
         "(and .spec files if --spec-only)"),
        ('python=', None,
         "path to Python interpreter to hard-code in the .spec file "
         "(default: \"python\")"),
        ('fix-python', None,
         "hard-code the exact path to the current Python interpreter in "
         "the .spec file"),
        ('spec-only', None,
         "only regenerate spec file"),
        ('source-only', None,
         "only generate source RPM"),
        ('binary-only', None,
         "only generate binary RPM"),
        ('use-bzip2', None,
         "use bzip2 instead of gzip to create source distribution"),

        # More meta-data: too RPM-specific to put in the setup script,
        # but needs to go in the .spec file -- so we make these options
        # to "bdist_rpm".  The idea is that packagers would put this
        # info in setup.cfg, although they are of course free to
        # supply it on the command line.
        ('distribution-name=', None,
         "name of the (Linux) distribution to which this "
         "RPM applies (*not* the name of the module distribution!)"),
        ('group=', None,
         "package classification [default: \"Development/Libraries\"]"),
        ('release=', None,
         "RPM release number"),
        ('serial=', None,
         "RPM serial number"),
        ('vendor=', None,
         "RPM \"vendor\" (eg. \"Joe Blow <joe@example.com>\") "
         "[default: maintainer or author from setup script]"),
        ('packager=', None,
         "RPM packager (eg. \"Jane Doe <jane@example.net>\") "
         "[default: vendor]"),
        ('doc-files=', None,
         "list of documentation files (space or comma-separated)"),
        ('changelog=', None,
         "RPM changelog"),
        ('icon=', None,
         "name of icon file"),
        ('provides=', None,
         "capabilities provided by this package"),
        ('requires=', None,
         "capabilities required by this package"),
        ('conflicts=', None,
         "capabilities which conflict with this package"),
        ('build-requires=', None,
         "capabilities required to build this package"),
        ('obsoletes=', None,
         "capabilities made obsolete by this package"),
        ('no-autoreq', None,
         "do not automatically calculate dependencies"),

        # Actions to take when building RPM
        ('keep-temp', 'k',
         "don't clean up RPM build directory"),
        ('no-keep-temp', None,
         "clean up RPM build directory [default]"),
        ('use-rpm-opt-flags', None,
         "compile with RPM_OPT_FLAGS when building from source RPM"),
        ('no-rpm-opt-flags', None,
         "do not pass any RPM CFLAGS to compiler"),
        ('rpm3-mode', None,
         "RPM 3 compatibility mode (default)"),
        ('rpm2-mode', None,
         "RPM 2 compatibility mode"),

        # Add the hooks necessary for specifying custom scripts
        ('prep-script=', None,
         "Specify a script for the PREP phase of RPM building"),
        ('build-script=', None,
         "Specify a script for the BUILD phase of RPM building"),

        ('pre-install=', None,
         "Specify a script for the pre-INSTALL phase of RPM building"),
        ('install-script=', None,
         "Specify a script for the INSTALL phase of RPM building"),
        ('post-install=', None,
         "Specify a script for the post-INSTALL phase of RPM building"),

        ('pre-uninstall=', None,
         "Specify a script for the pre-UNINSTALL phase of RPM building"),
        ('post-uninstall=', None,
         "Specify a script for the post-UNINSTALL phase of RPM building"),

        ('clean-script=', None,
         "Specify a script for the CLEAN phase of RPM building"),

        ('verify-script=', None,
         "Specify a script for the VERIFY phase of the RPM build"),

        # Allow a packager to explicitly force an architecture
        ('force-arch=', None,
         "Force an architecture onto the RPM build process"),

        ('quiet', 'q',
         "Run the INSTALL phase of RPM building in quiet mode"),
        ]

    boolean_options = ['keep-temp', 'use-rpm-opt-flags', 'rpm3-mode',
                       'no-autoreq', 'quiet']

    negative_opt = {'no-keep-temp': 'keep-temp',
                    'no-rpm-opt-flags': 'use-rpm-opt-flags',
                    'rpm2-mode': 'rpm3-mode'}


    def initialize_options(self):
        self.bdist_base = None
        self.rpm_base = None
        self.dist_dir = None
        self.python = None
        self.fix_python = None
        self.spec_only = None
        self.binary_only = None
        self.source_only = None
        self.use_bzip2 = None

        self.distribution_name = None
        self.group = None
        self.release = None
        self.serial = None
        self.vendor = None
        self.packager = None
        self.doc_files = None
        self.changelog = None
        self.icon = None

        self.prep_script = None
        self.build_script = None
        self.install_script = None
        self.clean_script = None
        self.verify_script = None
        self.pre_install = None
        self.post_install = None
        self.pre_uninstall = None
        self.post_uninstall = None
        self.prep = None
        self.provides = None
        self.requires = None
        self.conflicts = None
        self.build_requires = None
        self.obsoletes = None

        self.keep_temp = 0
        self.use_rpm_opt_flags = 1
        self.rpm3_mode = 1
        self.no_autoreq = 0

        self.force_arch = None
        self.quiet = 0

    def finalize_options(self):
        self.set_undefined_options('bdist', ('bdist_base', 'bdist_base'))
        if self.rpm_base is None:
            if not self.rpm3_mode:
                raise DistutilsOptionError(
                      "you must specify --rpm-base in RPM 2 mode")
            self.rpm_base = os.path.join(self.bdist_base, "rpm")

        if self.python is None:
            if self.fix_python:
                self.python = sys.executable
            else:
                self.python = "python3"
        elif self.fix_python:
            raise DistutilsOptionError(
                  "--python and --fix-python are mutually exclusive options")

        if os.name != 'posix':
            raise DistutilsPlatformError("don't know how to create RPM "
                   "distributions on platform %s" % os.name)
        if self.binary_only and self.source_only:
            raise DistutilsOptionError(
                  "cannot supply both '--source-only' and '--binary-only'")

        # don't pass CFLAGS to pure python distributions
        if not self.distribution.has_ext_modules():
            self.use_rpm_opt_flags = 0

        self.set_undefined_options('bdist', ('dist_dir', 'dist_dir'))
        self.finalize_package_data()

    def finalize_package_data(self):
        self.ensure_string('group', "Development/Libraries")
        self.ensure_string('vendor',
                           "%s <%s>" % (self.distribution.get_contact(),
                                        self.distribution.get_contact_email()))
        self.ensure_string('packager')
        self.ensure_string_list('doc_files')
        if isinstance(self.doc_files, list):
            for readme in ('README', 'README.txt'):
                if os.path.exists(readme) and readme not in self.doc_files:
                    self.doc_files.append(readme)

        self.ensure_string('release', "1")
        self.ensure_string('serial')   # should it be an int?

        self.ensure_string('distribution_name')

        self.ensure_string('changelog')
          # Format changelog correctly
        self.changelog = self._format_changelog(self.changelog)

        self.ensure_filename('icon')

        self.ensure_filename('prep_script')
        self.ensure_filename('build_script')
        self.ensure_filename('install_script')
        self.ensure_filename('clean_script')
        self.ensure_filename('verify_script')
        self.ensure_filename('pre_install')
        self.ensure_filename('post_install')
        self.ensure_filename('pre_uninstall')
        self.ensure_filename('post_uninstall')

        # XXX don't forget we punted on summaries and descriptions -- they
        # should be handled here eventually!

        # Now *this* is some meta-data that belongs in the setup script...
        self.ensure_string_list('provides')
        self.ensure_string_list('requires')
        self.ensure_string_list('conflicts')
        self.ensure_string_list('build_requires')
        self.ensure_string_list('obsoletes')

        self.ensure_string('force_arch')

    def run(self):
        if DEBUG:
            print("before _get_package_data():")
            print("vendor =", self.vendor)
            print("packager =", self.packager)
            print("doc_files =", self.doc_files)
            print("changelog =", self.changelog)

        # make directories
        if self.spec_only:
            spec_dir = self.dist_dir
            self.mkpath(spec_dir)
        else:
            rpm_dir = {}
            for d in ('SOURCES', 'SPECS', 'BUILD', 'RPMS', 'SRPMS'):
                rpm_dir[d] = os.path.join(self.rpm_base, d)
                self.mkpath(rpm_dir[d])
            spec_dir = rpm_dir['SPECS']

        # Spec file goes into 'dist_dir' if '--spec-only specified',
        # build/rpm.<plat> otherwise.
        spec_path = os.path.join(spec_dir,
                                 "%s.spec" % self.distribution.get_name())
        self.execute(write_file,
                     (spec_path,
                      self._make_spec_file()),
                     "writing '%s'" % spec_path)

        if self.spec_only: # stop if requested
            return

        # Make a source distribution and copy to SOURCES directory with
        # optional icon.
        saved_dist_files = self.distribution.dist_files[:]
        sdist = self.reinitialize_command('sdist')
        if self.use_bzip2:
            sdist.formats = ['bztar']
        else:
            sdist.formats = ['gztar']
        self.run_command('sdist')
        self.distribution.dist_files = saved_dist_files

        source = sdist.get_archive_files()[0]
        source_dir = rpm_dir['SOURCES']
        self.copy_file(source, source_dir)

        if self.icon:
            if os.path.exists(self.icon):
                self.copy_file(self.icon, source_dir)
            else:
                raise DistutilsFileError(
                      "icon file '%s' does not exist" % self.icon)

        # build package
        log.info("building RPMs")
        rpm_cmd = ['rpmbuild']

        if self.source_only: # what kind of RPMs?
            rpm_cmd.append('-bs')
        elif self.binary_only:
            rpm_cmd.append('-bb')
        else:
            rpm_cmd.append('-ba')
        rpm_cmd.extend(['--define', '__python %s' % self.python])
        if self.rpm3_mode:
            rpm_cmd.extend(['--define',
                             '_topdir %s' % os.path.abspath(self.rpm_base)])
        if not self.keep_temp:
            rpm_cmd.append('--clean')

        if self.quiet:
            rpm_cmd.append('--quiet')

        rpm_cmd.append(spec_path)
        # Determine the binary rpm names that should be built out of this spec
        # file
        # Note that some of these may not be really built (if the file
        # list is empty)
        nvr_string = "%{name}-%{version}-%{release}"
        src_rpm = nvr_string + ".src.rpm"
        non_src_rpm = "%{arch}/" + nvr_string + ".%{arch}.rpm"
        q_cmd = r"rpm -q --qf '%s %s\n' --specfile '%s'" % (
            src_rpm, non_src_rpm, spec_path)

        out = os.popen(q_cmd)
        try:
            binary_rpms = []
            source_rpm = None
            while True:
                line = out.readline()
                if not line:
                    break
                l = line.strip().split()
                assert(len(l) == 2)
                binary_rpms.append(l[1])
                # The source rpm is named after the first entry in the spec file
                if source_rpm is None:
                    source_rpm = l[0]

            status = out.close()
            if status:
                raise DistutilsExecError("Failed to execute: %s" % repr(q_cmd))

        finally:
            out.close()

        self.spawn(rpm_cmd)

        if not self.dry_run:
            if self.distribution.has_ext_modules():
                pyversion = get_python_version()
            else:
                pyversion = 'any'

            if not self.binary_only:
                srpm = os.path.join(rpm_dir['SRPMS'], source_rpm)
                assert(os.path.exists(srpm))
                self.move_file(srpm, self.dist_dir)
                filename = os.path.join(self.dist_dir, source_rpm)
                self.distribution.dist_files.append(
                    ('bdist_rpm', pyversion, filename))

            if not self.source_only:
                for rpm in binary_rpms:
                    rpm = os.path.join(rpm_dir['RPMS'], rpm)
                    if os.path.exists(rpm):
                        self.move_file(rpm, self.dist_dir)
                        filename = os.path.join(self.dist_dir,
                                                os.path.basename(rpm))
                        self.distribution.dist_files.append(
                            ('bdist_rpm', pyversion, filename))

    def _dist_path(self, path):
        return os.path.join(self.dist_dir, os.path.basename(path))

    def _make_spec_file(self):
        """Generate the text of an RPM spec file and return it as a
        list of strings (one per line).
        """
        # definitions and headers
        spec_file = [
            '%define name ' + self.distribution.get_name(),
            '%define version ' + self.distribution.get_version().replace('-','_'),
            '%define unmangled_version ' + self.distribution.get_version(),
            '%define release ' + self.release.replace('-','_'),
            '',
            'Summary: ' + self.distribution.get_description(),
            ]

        # Workaround for #14443 which affects some RPM based systems such as
        # RHEL6 (and probably derivatives)
        vendor_hook = subprocess.getoutput('rpm --eval %{__os_install_post}')
        # Generate a potential replacement value for __os_install_post (whilst
        # normalizing the whitespace to simplify the test for whether the
        # invocation of brp-python-bytecompile passes in __python):
        vendor_hook = '\n'.join(['  %s \\' % line.strip()
                                 for line in vendor_hook.splitlines()])
        problem = "brp-python-bytecompile \\\n"
        fixed = "brp-python-bytecompile %{__python} \\\n"
        fixed_hook = vendor_hook.replace(problem, fixed)
        if fixed_hook != vendor_hook:
            spec_file.append('# Workaround for http://bugs.python.org/issue14443')
            spec_file.append('%define __os_install_post ' + fixed_hook + '\n')

        # put locale summaries into spec file
        # XXX not supported for now (hard to put a dictionary
        # in a config file -- arg!)
        #for locale in self.summaries.keys():
        #    spec_file.append('Summary(%s): %s' % (locale,
        #                                          self.summaries[locale]))

        spec_file.extend([
            'Name: %{name}',
            'Version: %{version}',
            'Release: %{release}',])

        # XXX yuck! this filename is available from the "sdist" command,
        # but only after it has run: and we create the spec file before
        # running "sdist", in case of --spec-only.
        if self.use_bzip2:
            spec_file.append('Source0: %{name}-%{unmangled_version}.tar.bz2')
        else:
            spec_file.append('Source0: %{name}-%{unmangled_version}.tar.gz')

        spec_file.extend([
            'License: ' + self.distribution.get_license(),
            'Group: ' + self.group,
            'BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot',
            'Prefix: %{_prefix}', ])

        if not self.force_arch:
            # noarch if no extension modules
            if not self.distribution.has_ext_modules():
                spec_file.append('BuildArch: noarch')
        else:
            spec_file.append( 'BuildArch: %s' % self.force_arch )

        for field in ('Vendor',
                      'Packager',
                      'Provides',
                      'Requires',
                      'Conflicts',
                      'Obsoletes',
                      ):
            val = getattr(self, field.lower())
            if isinstance(val, list):
                spec_file.append('%s: %s' % (field, ' '.join(val)))
            elif val is not None:
                spec_file.append('%s: %s' % (field, val))


        if self.distribution.get_url() != 'UNKNOWN':
            spec_file.append('Url: ' + self.distribution.get_url())

        if self.distribution_name:
            spec_file.append('Distribution: ' + self.distribution_name)

        if self.build_requires:
            spec_file.append('BuildRequires: ' +
                             ' '.join(self.build_requires))

        if self.icon:
            spec_file.append('Icon: ' + os.path.basename(self.icon))

        if self.no_autoreq:
            spec_file.append('AutoReq: 0')

        spec_file.extend([
            '',
            '%description',
            self.distribution.get_long_description()
            ])

        # put locale descriptions into spec file
        # XXX again, suppressed because config file syntax doesn't
        # easily support this ;-(
        #for locale in self.descriptions.keys():
        #    spec_file.extend([
        #        '',
        #        '%description -l ' + locale,
        #        self.descriptions[locale],
        #        ])

        # rpm scripts
        # figure out default build script
        def_setup_call = "%s %s" % (self.python,os.path.basename(sys.argv[0]))
        def_build = "%s build" % def_setup_call
        if self.use_rpm_opt_flags:
            def_build = 'env CFLAGS="$RPM_OPT_FLAGS" ' + def_build

        # insert contents of files

        # XXX this is kind of misleading: user-supplied options are files
        # that we open and interpolate into the spec file, but the defaults
        # are just text that we drop in as-is.  Hmmm.

        install_cmd = ('%s install -O1 --root=$RPM_BUILD_ROOT '
                       '--record=INSTALLED_FILES') % def_setup_call

        script_options = [
            ('prep', 'prep_script', "%setup -n %{name}-%{unmangled_version}"),
            ('build', 'build_script', def_build),
            ('install', 'install_script', install_cmd),
            ('clean', 'clean_script', "rm -rf $RPM_BUILD_ROOT"),
            ('verifyscript', 'verify_script', None),
            ('pre', 'pre_install', None),
            ('post', 'post_install', None),
            ('preun', 'pre_uninstall', None),
            ('postun', 'post_uninstall', None),
        ]

        for (rpm_opt, attr, default) in script_options:
            # Insert contents of file referred to, if no file is referred to
            # use 'default' as contents of script
            val = getattr(self, attr)
            if val or default:
                spec_file.extend([
                    '',
                    '%' + rpm_opt,])
                if val:
                    with open(val) as f:
                        spec_file.extend(f.read().split('\n'))
                else:
                    spec_file.append(default)


        # files section
        spec_file.extend([
            '',
            '%files -f INSTALLED_FILES',
            '%defattr(-,root,root)',
            ])

        if self.doc_files:
            spec_file.append('%doc ' + ' '.join(self.doc_files))

        if self.changelog:
            spec_file.extend([
                '',
                '%changelog',])
            spec_file.extend(self.changelog)

        return spec_file

    def _format_changelog(self, changelog):
        """Format the changelog correctly and convert it to a list of strings
        """
        if not changelog:
            return changelog
        new_changelog = []
        for line in changelog.strip().split('\n'):
            line = line.strip()
            if line[0] == '*':
                new_changelog.extend(['', line])
            elif line[0] == '-':
                new_changelog.append(line)
            else:
                new_changelog.append('  ' + line)

        # strip trailing newline inserted by first changelog entry
        if not new_changelog[0]:
            del new_changelog[0]

        return new_changelog
