import bisect
import re
import unicodedata
from typing import Optional, Union

from . import idnadata
from .intranges import intranges_contain

_virama_combining_class = 9
_alabel_prefix = b"xn--"
_unicode_dots_re = re.compile("[\u002e\u3002\uff0e\uff61]")


class IDNAError(UnicodeError):
    """Base exception for all IDNA-encoding related problems"""

    pass


class IDNABidiError(IDNAError):
    """Exception when bidirectional requirements are not satisfied"""

    pass


class InvalidCodepoint(IDNAError):
    """Exception when a disallowed or unallocated codepoint is used"""

    pass


class InvalidCodepointContext(IDNAError):
    """Exception when the codepoint is not valid in the context it is used"""

    pass


def _combining_class(cp: int) -> int:
    v = unicodedata.combining(chr(cp))
    if v == 0:
        if not unicodedata.name(chr(cp)):
            raise ValueError("Unknown character in unicodedata")
    return v


def _is_script(cp: str, script: str) -> bool:
    return intranges_contain(ord(cp), idnadata.scripts[script])


def _punycode(s: str) -> bytes:
    return s.encode("punycode")


def _unot(s: int) -> str:
    return "U+{:04X}".format(s)


def valid_label_length(label: Union[bytes, str]) -> bool:
    if len(label) > 63:
        return False
    return True


def valid_string_length(label: Union[bytes, str], trailing_dot: bool) -> bool:
    if len(label) > (254 if trailing_dot else 253):
        return False
    return True


def check_bidi(label: str, check_ltr: bool = False) -> bool:
    # Bidi rules should only be applied if string contains RTL characters
    bidi_label = False
    for idx, cp in enumerate(label, 1):
        direction = unicodedata.bidirectional(cp)
        if direction == "":
            # String likely comes from a newer version of Unicode
            raise IDNABidiError("Unknown directionality in label {} at position {}".format(repr(label), idx))
        if direction in ["R", "AL", "AN"]:
            bidi_label = True
    if not bidi_label and not check_ltr:
        return True

    # Bidi rule 1
    direction = unicodedata.bidirectional(label[0])
    if direction in ["R", "AL"]:
        rtl = True
    elif direction == "L":
        rtl = False
    else:
        raise IDNABidiError("First codepoint in label {} must be directionality L, R or AL".format(repr(label)))

    valid_ending = False
    number_type: Optional[str] = None
    for idx, cp in enumerate(label, 1):
        direction = unicodedata.bidirectional(cp)

        if rtl:
            # Bidi rule 2
            if direction not in [
                "R",
                "AL",
                "AN",
                "EN",
                "ES",
                "CS",
                "ET",
                "ON",
                "BN",
                "NSM",
            ]:
                raise IDNABidiError("Invalid direction for codepoint at position {} in a right-to-left label".format(idx))
            # Bidi rule 3
            if direction in ["R", "AL", "EN", "AN"]:
                valid_ending = True
            elif direction != "NSM":
                valid_ending = False
            # Bidi rule 4
            if direction in ["AN", "EN"]:
                if not number_type:
                    number_type = direction
                else:
                    if number_type != direction:
                        raise IDNABidiError("Can not mix numeral types in a right-to-left label")
        else:
            # Bidi rule 5
            if direction not in ["L", "EN", "ES", "CS", "ET", "ON", "BN", "NSM"]:
                raise IDNABidiError("Invalid direction for codepoint at position {} in a left-to-right label".format(idx))
            # Bidi rule 6
            if direction in ["L", "EN"]:
                valid_ending = True
            elif direction != "NSM":
                valid_ending = False

    if not valid_ending:
        raise IDNABidiError("Label ends with illegal codepoint directionality")

    return True


def check_initial_combiner(label: str) -> bool:
    if unicodedata.category(label[0])[0] == "M":
        raise IDNAError("Label begins with an illegal combining character")
    return True


def check_hyphen_ok(label: str) -> bool:
    if label[2:4] == "--":
        raise IDNAError("Label has disallowed hyphens in 3rd and 4th position")
    if label[0] == "-" or label[-1] == "-":
        raise IDNAError("Label must not start or end with a hyphen")
    return True


def check_nfc(label: str) -> None:
    if unicodedata.normalize("NFC", label) != label:
        raise IDNAError("Label must be in Normalization Form C")


def valid_contextj(label: str, pos: int) -> bool:
    cp_value = ord(label[pos])

    if cp_value == 0x200C:
        if pos > 0:
            if _combining_class(ord(label[pos - 1])) == _virama_combining_class:
                return True

        ok = False
        for i in range(pos - 1, -1, -1):
            joining_type = idnadata.joining_types.get(ord(label[i]))
            if joining_type == ord("T"):
                continue
            elif joining_type in [ord("L"), ord("D")]:
                ok = True
                break
            else:
                break

        if not ok:
            return False

        ok = False
        for i in range(pos + 1, len(label)):
            joining_type = idnadata.joining_types.get(ord(label[i]))
            if joining_type == ord("T"):
                continue
            elif joining_type in [ord("R"), ord("D")]:
                ok = True
                break
            else:
                break
        return ok

    if cp_value == 0x200D:
        if pos > 0:
            if _combining_class(ord(label[pos - 1])) == _virama_combining_class:
                return True
        return False

    else:
        return False


def valid_contexto(label: str, pos: int, exception: bool = False) -> bool:
    cp_value = ord(label[pos])

    if cp_value == 0x00B7:
        if 0 < pos < len(label) - 1:
            if ord(label[pos - 1]) == 0x006C and ord(label[pos + 1]) == 0x006C:
                return True
        return False

    elif cp_value == 0x0375:
        if pos < len(label) - 1 and len(label) > 1:
            return _is_script(label[pos + 1], "Greek")
        return False

    elif cp_value == 0x05F3 or cp_value == 0x05F4:
        if pos > 0:
            return _is_script(label[pos - 1], "Hebrew")
        return False

    elif cp_value == 0x30FB:
        for cp in label:
            if cp == "\u30fb":
                continue
            if _is_script(cp, "Hiragana") or _is_script(cp, "Katakana") or _is_script(cp, "Han"):
                return True
        return False

    elif 0x660 <= cp_value <= 0x669:
        for cp in label:
            if 0x6F0 <= ord(cp) <= 0x06F9:
                return False
        return True

    elif 0x6F0 <= cp_value <= 0x6F9:
        for cp in label:
            if 0x660 <= ord(cp) <= 0x0669:
                return False
        return True

    return False


def check_label(label: Union[str, bytes, bytearray]) -> None:
    if isinstance(label, (bytes, bytearray)):
        label = label.decode("utf-8")
    if len(label) == 0:
        raise IDNAError("Empty Label")

    check_nfc(label)
    check_hyphen_ok(label)
    check_initial_combiner(label)

    for pos, cp in enumerate(label):
        cp_value = ord(cp)
        if intranges_contain(cp_value, idnadata.codepoint_classes["PVALID"]):
            continue
        elif intranges_contain(cp_value, idnadata.codepoint_classes["CONTEXTJ"]):
            try:
                if not valid_contextj(label, pos):
                    raise InvalidCodepointContext(
                        "Joiner {} not allowed at position {} in {}".format(_unot(cp_value), pos + 1, repr(label))
                    )
            except ValueError:
                raise IDNAError(
                    "Unknown codepoint adjacent to joiner {} at position {} in {}".format(
                        _unot(cp_value), pos + 1, repr(label)
                    )
                )
        elif intranges_contain(cp_value, idnadata.codepoint_classes["CONTEXTO"]):
            if not valid_contexto(label, pos):
                raise InvalidCodepointContext(
                    "Codepoint {} not allowed at position {} in {}".format(_unot(cp_value), pos + 1, repr(label))
                )
        else:
            raise InvalidCodepoint(
                "Codepoint {} at position {} of {} not allowed".format(_unot(cp_value), pos + 1, repr(label))
            )

    check_bidi(label)


def alabel(label: str) -> bytes:
    try:
        label_bytes = label.encode("ascii")
        ulabel(label_bytes)
        if not valid_label_length(label_bytes):
            raise IDNAError("Label too long")
        return label_bytes
    except UnicodeEncodeError:
        pass

    check_label(label)
    label_bytes = _alabel_prefix + _punycode(label)

    if not valid_label_length(label_bytes):
        raise IDNAError("Label too long")

    return label_bytes


def ulabel(label: Union[str, bytes, bytearray]) -> str:
    if not isinstance(label, (bytes, bytearray)):
        try:
            label_bytes = label.encode("ascii")
        except UnicodeEncodeError:
            check_label(label)
            return label
    else:
        label_bytes = label

    label_bytes = label_bytes.lower()
    if label_bytes.startswith(_alabel_prefix):
        label_bytes = label_bytes[len(_alabel_prefix) :]
        if not label_bytes:
            raise IDNAError("Malformed A-label, no Punycode eligible content found")
        if label_bytes.decode("ascii")[-1] == "-":
            raise IDNAError("A-label must not end with a hyphen")
    else:
        check_label(label_bytes)
        return label_bytes.decode("ascii")

    try:
        label = label_bytes.decode("punycode")
    except UnicodeError:
        raise IDNAError("Invalid A-label")
    check_label(label)
    return label


def uts46_remap(domain: str, std3_rules: bool = True, transitional: bool = False) -> str:
    """Re-map the characters in the string according to UTS46 processing."""
    from .uts46data import uts46data

    output = ""

    for pos, char in enumerate(domain):
        code_point = ord(char)
        try:
            uts46row = uts46data[code_point if code_point < 256 else bisect.bisect_left(uts46data, (code_point, "Z")) - 1]
            status = uts46row[1]
            replacement: Optional[str] = None
            if len(uts46row) == 3:
                replacement = uts46row[2]
            if (
                status == "V"
                or (status == "D" and not transitional)
                or (status == "3" and not std3_rules and replacement is None)
            ):
                output += char
            elif replacement is not None and (
                status == "M" or (status == "3" and not std3_rules) or (status == "D" and transitional)
            ):
                output += replacement
            elif status != "I":
                raise IndexError()
        except IndexError:
            raise InvalidCodepoint(
                "Codepoint {} not allowed at position {} in {}".format(_unot(code_point), pos + 1, repr(domain))
            )

    return unicodedata.normalize("NFC", output)


def encode(
    s: Union[str, bytes, bytearray],
    strict: bool = False,
    uts46: bool = False,
    std3_rules: bool = False,
    transitional: bool = False,
) -> bytes:
    if not isinstance(s, str):
        try:
            s = str(s, "ascii")
        except UnicodeDecodeError:
            raise IDNAError("should pass a unicode string to the function rather than a byte string.")
    if uts46:
        s = uts46_remap(s, std3_rules, transitional)
    trailing_dot = False
    result = []
    if strict:
        labels = s.split(".")
    else:
        labels = _unicode_dots_re.split(s)
    if not labels or labels == [""]:
        raise IDNAError("Empty domain")
    if labels[-1] == "":
        del labels[-1]
        trailing_dot = True
    for label in labels:
        s = alabel(label)
        if s:
            result.append(s)
        else:
            raise IDNAError("Empty label")
    if trailing_dot:
        result.append(b"")
    s = b".".join(result)
    if not valid_string_length(s, trailing_dot):
        raise IDNAError("Domain too long")
    return s


def decode(
    s: Union[str, bytes, bytearray],
    strict: bool = False,
    uts46: bool = False,
    std3_rules: bool = False,
) -> str:
    try:
        if not isinstance(s, str):
            s = str(s, "ascii")
    except UnicodeDecodeError:
        raise IDNAError("Invalid ASCII in A-label")
    if uts46:
        s = uts46_remap(s, std3_rules, False)
    trailing_dot = False
    result = []
    if not strict:
        labels = _unicode_dots_re.split(s)
    else:
        labels = s.split(".")
    if not labels or labels == [""]:
        raise IDNAError("Empty domain")
    if not labels[-1]:
        del labels[-1]
        trailing_dot = True
    for label in labels:
        s = ulabel(label)
        if s:
            result.append(s)
        else:
            raise IDNAError("Empty label")
    if trailing_dot:
        result.append("")
    return ".".join(result)
