import ast
import io
import os
import sys

import warnings
import functools
import importlib
from collections import defaultdict
from functools import partial
from functools import wraps
from glob import iglob
import contextlib

from distutils.errors import DistutilsOptionError, DistutilsFileError
from setuptools.extern.packaging.version import LegacyVersion, parse
from setuptools.extern.packaging.specifiers import SpecifierSet


class StaticModule:
    """
    Attempt to load the module by the name
    """

    def __init__(self, name):
        spec = importlib.util.find_spec(name)
        with open(spec.origin) as strm:
            src = strm.read()
        module = ast.parse(src)
        vars(self).update(locals())
        del self.self

    def __getattr__(self, attr):
        try:
            return next(
                ast.literal_eval(statement.value)
                for statement in self.module.body
                if isinstance(statement, ast.Assign)
                for target in statement.targets
                if isinstance(target, ast.Name) and target.id == attr
            )
        except Exception as e:
            raise AttributeError(
                "{self.name} has no attribute {attr}".format(**locals())
            ) from e


@contextlib.contextmanager
def patch_path(path):
    """
    Add path to front of sys.path for the duration of the context.
    """
    try:
        sys.path.insert(0, path)
        yield
    finally:
        sys.path.remove(path)


def read_configuration(filepath, find_others=False, ignore_option_errors=False):
    """Read given configuration file and returns options from it as a dict.

    :param str|unicode filepath: Path to configuration file
        to get options from.

    :param bool find_others: Whether to search for other configuration files
        which could be on in various places.

    :param bool ignore_option_errors: Whether to silently ignore
        options, values of which could not be resolved (e.g. due to exceptions
        in directives such as file:, attr:, etc.).
        If False exceptions are propagated as expected.

    :rtype: dict
    """
    from setuptools.dist import Distribution, _Distribution

    filepath = os.path.abspath(filepath)

    if not os.path.isfile(filepath):
        raise DistutilsFileError('Configuration file %s does not exist.' % filepath)

    current_directory = os.getcwd()
    os.chdir(os.path.dirname(filepath))

    try:
        dist = Distribution()

        filenames = dist.find_config_files() if find_others else []
        if filepath not in filenames:
            filenames.append(filepath)

        _Distribution.parse_config_files(dist, filenames=filenames)

        handlers = parse_configuration(
            dist, dist.command_options, ignore_option_errors=ignore_option_errors
        )

    finally:
        os.chdir(current_directory)

    return configuration_to_dict(handlers)


def _get_option(target_obj, key):
    """
    Given a target object and option key, get that option from
    the target object, either through a get_{key} method or
    from an attribute directly.
    """
    getter_name = 'get_{key}'.format(**locals())
    by_attribute = functools.partial(getattr, target_obj, key)
    getter = getattr(target_obj, getter_name, by_attribute)
    return getter()


def configuration_to_dict(handlers):
    """Returns configuration data gathered by given handlers as a dict.

    :param list[ConfigHandler] handlers: Handlers list,
        usually from parse_configuration()

    :rtype: dict
    """
    config_dict = defaultdict(dict)

    for handler in handlers:
        for option in handler.set_options:
            value = _get_option(handler.target_obj, option)
            config_dict[handler.section_prefix][option] = value

    return config_dict


def parse_configuration(distribution, command_options, ignore_option_errors=False):
    """Performs additional parsing of configuration options
    for a distribution.

    Returns a list of used option handlers.

    :param Distribution distribution:
    :param dict command_options:
    :param bool ignore_option_errors: Whether to silently ignore
        options, values of which could not be resolved (e.g. due to exceptions
        in directives such as file:, attr:, etc.).
        If False exceptions are propagated as expected.
    :rtype: list
    """
    options = ConfigOptionsHandler(distribution, command_options, ignore_option_errors)
    options.parse()

    meta = ConfigMetadataHandler(
        distribution.metadata,
        command_options,
        ignore_option_errors,
        distribution.package_dir,
    )
    meta.parse()

    return meta, options


class ConfigHandler:
    """Handles metadata supplied in configuration files."""

    section_prefix = None
    """Prefix for config sections handled by this handler.
    Must be provided by class heirs.

    """

    aliases = {}
    """Options aliases.
    For compatibility with various packages. E.g.: d2to1 and pbr.
    Note: `-` in keys is replaced with `_` by config parser.

    """

    def __init__(self, target_obj, options, ignore_option_errors=False):
        sections = {}

        section_prefix = self.section_prefix
        for section_name, section_options in options.items():
            if not section_name.startswith(section_prefix):
                continue

            section_name = section_name.replace(section_prefix, '').strip('.')
            sections[section_name] = section_options

        self.ignore_option_errors = ignore_option_errors
        self.target_obj = target_obj
        self.sections = sections
        self.set_options = []

    @property
    def parsers(self):
        """Metadata item name to parser function mapping."""
        raise NotImplementedError(
            '%s must provide .parsers property' % self.__class__.__name__
        )

    def __setitem__(self, option_name, value):
        unknown = tuple()
        target_obj = self.target_obj

        # Translate alias into real name.
        option_name = self.aliases.get(option_name, option_name)

        current_value = getattr(target_obj, option_name, unknown)

        if current_value is unknown:
            raise KeyError(option_name)

        if current_value:
            # Already inhabited. Skipping.
            return

        skip_option = False
        parser = self.parsers.get(option_name)
        if parser:
            try:
                value = parser(value)

            except Exception:
                skip_option = True
                if not self.ignore_option_errors:
                    raise

        if skip_option:
            return

        setter = getattr(target_obj, 'set_%s' % option_name, None)
        if setter is None:
            setattr(target_obj, option_name, value)
        else:
            setter(value)

        self.set_options.append(option_name)

    @classmethod
    def _parse_list(cls, value, separator=','):
        """Represents value as a list.

        Value is split either by separator (defaults to comma) or by lines.

        :param value:
        :param separator: List items separator character.
        :rtype: list
        """
        if isinstance(value, list):  # _get_parser_compound case
            return value

        if '\n' in value:
            value = value.splitlines()
        else:
            value = value.split(separator)

        return [chunk.strip() for chunk in value if chunk.strip()]

    @classmethod
    def _parse_list_glob(cls, value, separator=','):
        """Equivalent to _parse_list() but expands any glob patterns using glob().

        However, unlike with glob() calls, the results remain relative paths.

        :param value:
        :param separator: List items separator character.
        :rtype: list
        """
        glob_characters = ('*', '?', '[', ']', '{', '}')
        values = cls._parse_list(value, separator=separator)
        expanded_values = []
        for value in values:

            # Has globby characters?
            if any(char in value for char in glob_characters):
                # then expand the glob pattern while keeping paths *relative*:
                expanded_values.extend(sorted(
                    os.path.relpath(path, os.getcwd())
                    for path in iglob(os.path.abspath(value))))

            else:
                # take the value as-is:
                expanded_values.append(value)

        return expanded_values

    @classmethod
    def _parse_dict(cls, value):
        """Represents value as a dict.

        :param value:
        :rtype: dict
        """
        separator = '='
        result = {}
        for line in cls._parse_list(value):
            key, sep, val = line.partition(separator)
            if sep != separator:
                raise DistutilsOptionError(
                    'Unable to parse option value to dict: %s' % value
                )
            result[key.strip()] = val.strip()

        return result

    @classmethod
    def _parse_bool(cls, value):
        """Represents value as boolean.

        :param value:
        :rtype: bool
        """
        value = value.lower()
        return value in ('1', 'true', 'yes')

    @classmethod
    def _exclude_files_parser(cls, key):
        """Returns a parser function to make sure field inputs
        are not files.

        Parses a value after getting the key so error messages are
        more informative.

        :param key:
        :rtype: callable
        """

        def parser(value):
            exclude_directive = 'file:'
            if value.startswith(exclude_directive):
                raise ValueError(
                    'Only strings are accepted for the {0} field, '
                    'files are not accepted'.format(key)
                )
            return value

        return parser

    @classmethod
    def _parse_file(cls, value):
        """Represents value as a string, allowing including text
        from nearest files using `file:` directive.

        Directive is sandboxed and won't reach anything outside
        directory with setup.py.

        Examples:
            file: README.rst, CHANGELOG.md, src/file.txt

        :param str value:
        :rtype: str
        """
        include_directive = 'file:'

        if not isinstance(value, str):
            return value

        if not value.startswith(include_directive):
            return value

        spec = value[len(include_directive) :]
        filepaths = (os.path.abspath(path.strip()) for path in spec.split(','))
        return '\n'.join(
            cls._read_file(path)
            for path in filepaths
            if (cls._assert_local(path) or True) and os.path.isfile(path)
        )

    @staticmethod
    def _assert_local(filepath):
        if not filepath.startswith(os.getcwd()):
            raise DistutilsOptionError('`file:` directive can not access %s' % filepath)

    @staticmethod
    def _read_file(filepath):
        with io.open(filepath, encoding='utf-8') as f:
            return f.read()

    @classmethod
    def _parse_attr(cls, value, package_dir=None):
        """Represents value as a module attribute.

        Examples:
            attr: package.attr
            attr: package.module.attr

        :param str value:
        :rtype: str
        """
        attr_directive = 'attr:'
        if not value.startswith(attr_directive):
            return value

        attrs_path = value.replace(attr_directive, '').strip().split('.')
        attr_name = attrs_path.pop()

        module_name = '.'.join(attrs_path)
        module_name = module_name or '__init__'

        parent_path = os.getcwd()
        if package_dir:
            if attrs_path[0] in package_dir:
                # A custom path was specified for the module we want to import
                custom_path = package_dir[attrs_path[0]]
                parts = custom_path.rsplit('/', 1)
                if len(parts) > 1:
                    parent_path = os.path.join(os.getcwd(), parts[0])
                    module_name = parts[1]
                else:
                    module_name = custom_path
            elif '' in package_dir:
                # A custom parent directory was specified for all root modules
                parent_path = os.path.join(os.getcwd(), package_dir[''])

        with patch_path(parent_path):
            try:
                # attempt to load value statically
                return getattr(StaticModule(module_name), attr_name)
            except Exception:
                # fallback to simple import
                module = importlib.import_module(module_name)

        return getattr(module, attr_name)

    @classmethod
    def _get_parser_compound(cls, *parse_methods):
        """Returns parser function to represents value as a list.

        Parses a value applying given methods one after another.

        :param parse_methods:
        :rtype: callable
        """

        def parse(value):
            parsed = value

            for method in parse_methods:
                parsed = method(parsed)

            return parsed

        return parse

    @classmethod
    def _parse_section_to_dict(cls, section_options, values_parser=None):
        """Parses section options into a dictionary.

        Optionally applies a given parser to values.

        :param dict section_options:
        :param callable values_parser:
        :rtype: dict
        """
        value = {}
        values_parser = values_parser or (lambda val: val)
        for key, (_, val) in section_options.items():
            value[key] = values_parser(val)
        return value

    def parse_section(self, section_options):
        """Parses configuration file section.

        :param dict section_options:
        """
        for (name, (_, value)) in section_options.items():
            try:
                self[name] = value

            except KeyError:
                pass  # Keep silent for a new option may appear anytime.

    def parse(self):
        """Parses configuration file items from one
        or more related sections.

        """
        for section_name, section_options in self.sections.items():

            method_postfix = ''
            if section_name:  # [section.option] variant
                method_postfix = '_%s' % section_name

            section_parser_method = getattr(
                self,
                # Dots in section names are translated into dunderscores.
                ('parse_section%s' % method_postfix).replace('.', '__'),
                None,
            )

            if section_parser_method is None:
                raise DistutilsOptionError(
                    'Unsupported distribution option section: [%s.%s]'
                    % (self.section_prefix, section_name)
                )

            section_parser_method(section_options)

    def _deprecated_config_handler(self, func, msg, warning_class):
        """this function will wrap around parameters that are deprecated

        :param msg: deprecation message
        :param warning_class: class of warning exception to be raised
        :param func: function to be wrapped around
        """

        @wraps(func)
        def config_handler(*args, **kwargs):
            warnings.warn(msg, warning_class)
            return func(*args, **kwargs)

        return config_handler


class ConfigMetadataHandler(ConfigHandler):

    section_prefix = 'metadata'

    aliases = {
        'home_page': 'url',
        'summary': 'description',
        'classifier': 'classifiers',
        'platform': 'platforms',
    }

    strict_mode = False
    """We need to keep it loose, to be partially compatible with
    `pbr` and `d2to1` packages which also uses `metadata` section.

    """

    def __init__(
        self, target_obj, options, ignore_option_errors=False, package_dir=None
    ):
        super(ConfigMetadataHandler, self).__init__(
            target_obj, options, ignore_option_errors
        )
        self.package_dir = package_dir

    @property
    def parsers(self):
        """Metadata item name to parser function mapping."""
        parse_list = self._parse_list
        parse_file = self._parse_file
        parse_dict = self._parse_dict
        exclude_files_parser = self._exclude_files_parser

        return {
            'platforms': parse_list,
            'keywords': parse_list,
            'provides': parse_list,
            'requires': self._deprecated_config_handler(
                parse_list,
                "The requires parameter is deprecated, please use "
                "install_requires for runtime dependencies.",
                DeprecationWarning,
            ),
            'obsoletes': parse_list,
            'classifiers': self._get_parser_compound(parse_file, parse_list),
            'license': exclude_files_parser('license'),
            'license_file': self._deprecated_config_handler(
                exclude_files_parser('license_file'),
                "The license_file parameter is deprecated, "
                "use license_files instead.",
                DeprecationWarning,
            ),
            'license_files': parse_list,
            'description': parse_file,
            'long_description': parse_file,
            'version': self._parse_version,
            'project_urls': parse_dict,
        }

    def _parse_version(self, value):
        """Parses `version` option value.

        :param value:
        :rtype: str

        """
        version = self._parse_file(value)

        if version != value:
            version = version.strip()
            # Be strict about versions loaded from file because it's easy to
            # accidentally include newlines and other unintended content
            if isinstance(parse(version), LegacyVersion):
                tmpl = (
                    'Version loaded from {value} does not '
                    'comply with PEP 440: {version}'
                )
                raise DistutilsOptionError(tmpl.format(**locals()))

            return version

        version = self._parse_attr(value, self.package_dir)

        if callable(version):
            version = version()

        if not isinstance(version, str):
            if hasattr(version, '__iter__'):
                version = '.'.join(map(str, version))
            else:
                version = '%s' % version

        return version


class ConfigOptionsHandler(ConfigHandler):

    section_prefix = 'options'

    @property
    def parsers(self):
        """Metadata item name to parser function mapping."""
        parse_list = self._parse_list
        parse_list_semicolon = partial(self._parse_list, separator=';')
        parse_bool = self._parse_bool
        parse_dict = self._parse_dict
        parse_cmdclass = self._parse_cmdclass

        return {
            'zip_safe': parse_bool,
            'include_package_data': parse_bool,
            'package_dir': parse_dict,
            'scripts': parse_list,
            'eager_resources': parse_list,
            'dependency_links': parse_list,
            'namespace_packages': parse_list,
            'install_requires': parse_list_semicolon,
            'setup_requires': parse_list_semicolon,
            'tests_require': parse_list_semicolon,
            'packages': self._parse_packages,
            'entry_points': self._parse_file,
            'py_modules': parse_list,
            'python_requires': SpecifierSet,
            'cmdclass': parse_cmdclass,
        }

    def _parse_cmdclass(self, value):
        def resolve_class(qualified_class_name):
            idx = qualified_class_name.rfind('.')
            class_name = qualified_class_name[idx + 1 :]
            pkg_name = qualified_class_name[:idx]

            module = __import__(pkg_name)

            return getattr(module, class_name)

        return {k: resolve_class(v) for k, v in self._parse_dict(value).items()}

    def _parse_packages(self, value):
        """Parses `packages` option value.

        :param value:
        :rtype: list
        """
        find_directives = ['find:', 'find_namespace:']
        trimmed_value = value.strip()

        if trimmed_value not in find_directives:
            return self._parse_list(value)

        findns = trimmed_value == find_directives[1]

        # Read function arguments from a dedicated section.
        find_kwargs = self.parse_section_packages__find(
            self.sections.get('packages.find', {})
        )

        if findns:
            from setuptools import find_namespace_packages as find_packages
        else:
            from setuptools import find_packages

        return find_packages(**find_kwargs)

    def parse_section_packages__find(self, section_options):
        """Parses `packages.find` configuration file section.

        To be used in conjunction with _parse_packages().

        :param dict section_options:
        """
        section_data = self._parse_section_to_dict(section_options, self._parse_list)

        valid_keys = ['where', 'include', 'exclude']

        find_kwargs = dict(
            [(k, v) for k, v in section_data.items() if k in valid_keys and v]
        )

        where = find_kwargs.get('where')
        if where is not None:
            find_kwargs['where'] = where[0]  # cast list to single val

        return find_kwargs

    def parse_section_entry_points(self, section_options):
        """Parses `entry_points` configuration file section.

        :param dict section_options:
        """
        parsed = self._parse_section_to_dict(section_options, self._parse_list)
        self['entry_points'] = parsed

    def _parse_package_data(self, section_options):
        parsed = self._parse_section_to_dict(section_options, self._parse_list)

        root = parsed.get('*')
        if root:
            parsed[''] = root
            del parsed['*']

        return parsed

    def parse_section_package_data(self, section_options):
        """Parses `package_data` configuration file section.

        :param dict section_options:
        """
        self['package_data'] = self._parse_package_data(section_options)

    def parse_section_exclude_package_data(self, section_options):
        """Parses `exclude_package_data` configuration file section.

        :param dict section_options:
        """
        self['exclude_package_data'] = self._parse_package_data(section_options)

    def parse_section_extras_require(self, section_options):
        """Parses `extras_require` configuration file section.

        :param dict section_options:
        """
        parse_list = partial(self._parse_list, separator=';')
        self['extras_require'] = self._parse_section_to_dict(
            section_options, parse_list
        )

    def parse_section_data_files(self, section_options):
        """Parses `data_files` configuration file section.

        :param dict section_options:
        """
        parsed = self._parse_section_to_dict(section_options, self._parse_list_glob)
        self['data_files'] = [(k, v) for k, v in parsed.items()]
