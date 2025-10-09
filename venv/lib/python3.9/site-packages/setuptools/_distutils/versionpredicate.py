"""Module for parsing and testing package version predicate strings.
"""
import re
import distutils.version
import operator


re_validPackage = re.compile(r"(?i)^\s*([a-z_]\w*(?:\.[a-z_]\w*)*)(.*)",
    re.ASCII)
# (package) (rest)

re_paren = re.compile(r"^\s*\((.*)\)\s*$") # (list) inside of parentheses
re_splitComparison = re.compile(r"^\s*(<=|>=|<|>|!=|==)\s*([^\s,]+)\s*$")
# (comp) (version)


def splitUp(pred):
    """Parse a single version comparison.

    Return (comparison string, StrictVersion)
    """
    res = re_splitComparison.match(pred)
    if not res:
        raise ValueError("bad package restriction syntax: %r" % pred)
    comp, verStr = res.groups()
    return (comp, distutils.version.StrictVersion(verStr))

compmap = {"<": operator.lt, "<=": operator.le, "==": operator.eq,
           ">": operator.gt, ">=": operator.ge, "!=": operator.ne}

class VersionPredicate:
    """Parse and test package version predicates.

    >>> v = VersionPredicate('pyepat.abc (>1.0, <3333.3a1, !=1555.1b3)')

    The `name` attribute provides the full dotted name that is given::

    >>> v.name
    'pyepat.abc'

    The str() of a `VersionPredicate` provides a normalized
    human-readable version of the expression::

    >>> print(v)
    pyepat.abc (> 1.0, < 3333.3a1, != 1555.1b3)

    The `satisfied_by()` method can be used to determine with a given
    version number is included in the set described by the version
    restrictions::

    >>> v.satisfied_by('1.1')
    True
    >>> v.satisfied_by('1.4')
    True
    >>> v.satisfied_by('1.0')
    False
    >>> v.satisfied_by('4444.4')
    False
    >>> v.satisfied_by('1555.1b3')
    False

    `VersionPredicate` is flexible in accepting extra whitespace::

    >>> v = VersionPredicate(' pat( ==  0.1  )  ')
    >>> v.name
    'pat'
    >>> v.satisfied_by('0.1')
    True
    >>> v.satisfied_by('0.2')
    False

    If any version numbers passed in do not conform to the
    restrictions of `StrictVersion`, a `ValueError` is raised::

    >>> v = VersionPredicate('p1.p2.p3.p4(>=1.0, <=1.3a1, !=1.2zb3)')
    Traceback (most recent call last):
      ...
    ValueError: invalid version number '1.2zb3'

    It the module or package name given does not conform to what's
    allowed as a legal module or package name, `ValueError` is
    raised::

    >>> v = VersionPredicate('foo-bar')
    Traceback (most recent call last):
      ...
    ValueError: expected parenthesized list: '-bar'

    >>> v = VersionPredicate('foo bar (12.21)')
    Traceback (most recent call last):
      ...
    ValueError: expected parenthesized list: 'bar (12.21)'

    """

    def __init__(self, versionPredicateStr):
        """Parse a version predicate string.
        """
        # Fields:
        #    name:  package name
        #    pred:  list of (comparison string, StrictVersion)

        versionPredicateStr = versionPredicateStr.strip()
        if not versionPredicateStr:
            raise ValueError("empty package restriction")
        match = re_validPackage.match(versionPredicateStr)
        if not match:
            raise ValueError("bad package name in %r" % versionPredicateStr)
        self.name, paren = match.groups()
        paren = paren.strip()
        if paren:
            match = re_paren.match(paren)
            if not match:
                raise ValueError("expected parenthesized list: %r" % paren)
            str = match.groups()[0]
            self.pred = [splitUp(aPred) for aPred in str.split(",")]
            if not self.pred:
                raise ValueError("empty parenthesized list in %r"
                                 % versionPredicateStr)
        else:
            self.pred = []

    def __str__(self):
        if self.pred:
            seq = [cond + " " + str(ver) for cond, ver in self.pred]
            return self.name + " (" + ", ".join(seq) + ")"
        else:
            return self.name

    def satisfied_by(self, version):
        """True if version is compatible with all the predicates in self.
        The parameter version must be acceptable to the StrictVersion
        constructor.  It may be either a string or StrictVersion.
        """
        for cond, ver in self.pred:
            if not compmap[cond](version, ver):
                return False
        return True


_provision_rx = None

def split_provision(value):
    """Return the name and optional version number of a provision.

    The version number, if given, will be returned as a `StrictVersion`
    instance, otherwise it will be `None`.

    >>> split_provision('mypkg')
    ('mypkg', None)
    >>> split_provision(' mypkg( 1.2 ) ')
    ('mypkg', StrictVersion ('1.2'))
    """
    global _provision_rx
    if _provision_rx is None:
        _provision_rx = re.compile(
            r"([a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)*)(?:\s*\(\s*([^)\s]+)\s*\))?$",
            re.ASCII)
    value = value.strip()
    m = _provision_rx.match(value)
    if not m:
        raise ValueError("illegal provides specification: %r" % value)
    ver = m.group(2) or None
    if ver:
        ver = distutils.version.StrictVersion(ver)
    return m.group(1), ver
