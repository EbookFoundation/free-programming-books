import os
import operator
import sys
import contextlib
import itertools
import unittest
from distutils.errors import DistutilsError, DistutilsOptionError
from distutils import log
from unittest import TestLoader

from pkg_resources import (
    resource_listdir,
    resource_exists,
    normalize_path,
    working_set,
    evaluate_marker,
    add_activation_listener,
    require,
    EntryPoint,
)
from setuptools import Command
from setuptools.extern.more_itertools import unique_everseen


class ScanningLoader(TestLoader):
    def __init__(self):
        TestLoader.__init__(self)
        self._visited = set()

    def loadTestsFromModule(self, module, pattern=None):
        """Return a suite of all tests cases contained in the given module

        If the module is a package, load tests from all the modules in it.
        If the module has an ``additional_tests`` function, call it and add
        the return value to the tests.
        """
        if module in self._visited:
            return None
        self._visited.add(module)

        tests = []
        tests.append(TestLoader.loadTestsFromModule(self, module))

        if hasattr(module, "additional_tests"):
            tests.append(module.additional_tests())

        if hasattr(module, '__path__'):
            for file in resource_listdir(module.__name__, ''):
                if file.endswith('.py') and file != '__init__.py':
                    submodule = module.__name__ + '.' + file[:-3]
                else:
                    if resource_exists(module.__name__, file + '/__init__.py'):
                        submodule = module.__name__ + '.' + file
                    else:
                        continue
                tests.append(self.loadTestsFromName(submodule))

        if len(tests) != 1:
            return self.suiteClass(tests)
        else:
            return tests[0]  # don't create a nested suite for only one return


# adapted from jaraco.classes.properties:NonDataProperty
class NonDataProperty:
    def __init__(self, fget):
        self.fget = fget

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return self.fget(obj)


class test(Command):
    """Command to run unit tests after in-place build"""

    description = "run unit tests after in-place build (deprecated)"

    user_options = [
        ('test-module=', 'm', "Run 'test_suite' in specified module"),
        (
            'test-suite=',
            's',
            "Run single test, case or suite (e.g. 'module.test_suite')",
        ),
        ('test-runner=', 'r', "Test runner to use"),
    ]

    def initialize_options(self):
        self.test_suite = None
        self.test_module = None
        self.test_loader = None
        self.test_runner = None

    def finalize_options(self):

        if self.test_suite and self.test_module:
            msg = "You may specify a module or a suite, but not both"
            raise DistutilsOptionError(msg)

        if self.test_suite is None:
            if self.test_module is None:
                self.test_suite = self.distribution.test_suite
            else:
                self.test_suite = self.test_module + ".test_suite"

        if self.test_loader is None:
            self.test_loader = getattr(self.distribution, 'test_loader', None)
        if self.test_loader is None:
            self.test_loader = "setuptools.command.test:ScanningLoader"
        if self.test_runner is None:
            self.test_runner = getattr(self.distribution, 'test_runner', None)

    @NonDataProperty
    def test_args(self):
        return list(self._test_args())

    def _test_args(self):
        if not self.test_suite and sys.version_info >= (2, 7):
            yield 'discover'
        if self.verbose:
            yield '--verbose'
        if self.test_suite:
            yield self.test_suite

    def with_project_on_sys_path(self, func):
        """
        Backward compatibility for project_on_sys_path context.
        """
        with self.project_on_sys_path():
            func()

    @contextlib.contextmanager
    def project_on_sys_path(self, include_dists=[]):
        self.run_command('egg_info')

        # Build extensions in-place
        self.reinitialize_command('build_ext', inplace=1)
        self.run_command('build_ext')

        ei_cmd = self.get_finalized_command("egg_info")

        old_path = sys.path[:]
        old_modules = sys.modules.copy()

        try:
            project_path = normalize_path(ei_cmd.egg_base)
            sys.path.insert(0, project_path)
            working_set.__init__()
            add_activation_listener(lambda dist: dist.activate())
            require('%s==%s' % (ei_cmd.egg_name, ei_cmd.egg_version))
            with self.paths_on_pythonpath([project_path]):
                yield
        finally:
            sys.path[:] = old_path
            sys.modules.clear()
            sys.modules.update(old_modules)
            working_set.__init__()

    @staticmethod
    @contextlib.contextmanager
    def paths_on_pythonpath(paths):
        """
        Add the indicated paths to the head of the PYTHONPATH environment
        variable so that subprocesses will also see the packages at
        these paths.

        Do this in a context that restores the value on exit.
        """
        nothing = object()
        orig_pythonpath = os.environ.get('PYTHONPATH', nothing)
        current_pythonpath = os.environ.get('PYTHONPATH', '')
        try:
            prefix = os.pathsep.join(unique_everseen(paths))
            to_join = filter(None, [prefix, current_pythonpath])
            new_path = os.pathsep.join(to_join)
            if new_path:
                os.environ['PYTHONPATH'] = new_path
            yield
        finally:
            if orig_pythonpath is nothing:
                os.environ.pop('PYTHONPATH', None)
            else:
                os.environ['PYTHONPATH'] = orig_pythonpath

    @staticmethod
    def install_dists(dist):
        """
        Install the requirements indicated by self.distribution and
        return an iterable of the dists that were built.
        """
        ir_d = dist.fetch_build_eggs(dist.install_requires)
        tr_d = dist.fetch_build_eggs(dist.tests_require or [])
        er_d = dist.fetch_build_eggs(
            v
            for k, v in dist.extras_require.items()
            if k.startswith(':') and evaluate_marker(k[1:])
        )
        return itertools.chain(ir_d, tr_d, er_d)

    def run(self):
        self.announce(
            "WARNING: Testing via this command is deprecated and will be "
            "removed in a future version. Users looking for a generic test "
            "entry point independent of test runner are encouraged to use "
            "tox.",
            log.WARN,
        )

        installed_dists = self.install_dists(self.distribution)

        cmd = ' '.join(self._argv)
        if self.dry_run:
            self.announce('skipping "%s" (dry run)' % cmd)
            return

        self.announce('running "%s"' % cmd)

        paths = map(operator.attrgetter('location'), installed_dists)
        with self.paths_on_pythonpath(paths):
            with self.project_on_sys_path():
                self.run_tests()

    def run_tests(self):
        test = unittest.main(
            None,
            None,
            self._argv,
            testLoader=self._resolve_as_ep(self.test_loader),
            testRunner=self._resolve_as_ep(self.test_runner),
            exit=False,
        )
        if not test.result.wasSuccessful():
            msg = 'Test failed: %s' % test.result
            self.announce(msg, log.ERROR)
            raise DistutilsError(msg)

    @property
    def _argv(self):
        return ['unittest'] + self.test_args

    @staticmethod
    def _resolve_as_ep(val):
        """
        Load the indicated attribute value, called, as a as if it were
        specified as an entry point.
        """
        if val is None:
            return
        parsed = EntryPoint.parse("x=" + val)
        return parsed.resolve()()
