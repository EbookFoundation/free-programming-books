"""
Low-level helpers for the SecureTransport bindings.

These are Python functions that are not directly related to the high-level APIs
but are necessary to get them to work. They include a whole bunch of low-level
CoreFoundation messing about and memory management. The concerns in this module
are almost entirely about trying to avoid memory leaks and providing
appropriate and useful assistance to the higher-level code.
"""
import base64
import ctypes
import itertools
import os
import re
import ssl
import struct
import tempfile

from .bindings import CFConst, CoreFoundation, Security

# This regular expression is used to grab PEM data out of a PEM bundle.
_PEM_CERTS_RE = re.compile(
    b"-----BEGIN CERTIFICATE-----\n(.*?)\n-----END CERTIFICATE-----", re.DOTALL
)


def _cf_data_from_bytes(bytestring):
    """
    Given a bytestring, create a CFData object from it. This CFData object must
    be CFReleased by the caller.
    """
    return CoreFoundation.CFDataCreate(
        CoreFoundation.kCFAllocatorDefault, bytestring, len(bytestring)
    )


def _cf_dictionary_from_tuples(tuples):
    """
    Given a list of Python tuples, create an associated CFDictionary.
    """
    dictionary_size = len(tuples)

    # We need to get the dictionary keys and values out in the same order.
    keys = (t[0] for t in tuples)
    values = (t[1] for t in tuples)
    cf_keys = (CoreFoundation.CFTypeRef * dictionary_size)(*keys)
    cf_values = (CoreFoundation.CFTypeRef * dictionary_size)(*values)

    return CoreFoundation.CFDictionaryCreate(
        CoreFoundation.kCFAllocatorDefault,
        cf_keys,
        cf_values,
        dictionary_size,
        CoreFoundation.kCFTypeDictionaryKeyCallBacks,
        CoreFoundation.kCFTypeDictionaryValueCallBacks,
    )


def _cfstr(py_bstr):
    """
    Given a Python binary data, create a CFString.
    The string must be CFReleased by the caller.
    """
    c_str = ctypes.c_char_p(py_bstr)
    cf_str = CoreFoundation.CFStringCreateWithCString(
        CoreFoundation.kCFAllocatorDefault,
        c_str,
        CFConst.kCFStringEncodingUTF8,
    )
    return cf_str


def _create_cfstring_array(lst):
    """
    Given a list of Python binary data, create an associated CFMutableArray.
    The array must be CFReleased by the caller.

    Raises an ssl.SSLError on failure.
    """
    cf_arr = None
    try:
        cf_arr = CoreFoundation.CFArrayCreateMutable(
            CoreFoundation.kCFAllocatorDefault,
            0,
            ctypes.byref(CoreFoundation.kCFTypeArrayCallBacks),
        )
        if not cf_arr:
            raise MemoryError("Unable to allocate memory!")
        for item in lst:
            cf_str = _cfstr(item)
            if not cf_str:
                raise MemoryError("Unable to allocate memory!")
            try:
                CoreFoundation.CFArrayAppendValue(cf_arr, cf_str)
            finally:
                CoreFoundation.CFRelease(cf_str)
    except BaseException as e:
        if cf_arr:
            CoreFoundation.CFRelease(cf_arr)
        raise ssl.SSLError("Unable to allocate array: %s" % (e,))
    return cf_arr


def _cf_string_to_unicode(value):
    """
    Creates a Unicode string from a CFString object. Used entirely for error
    reporting.

    Yes, it annoys me quite a lot that this function is this complex.
    """
    value_as_void_p = ctypes.cast(value, ctypes.POINTER(ctypes.c_void_p))

    string = CoreFoundation.CFStringGetCStringPtr(
        value_as_void_p, CFConst.kCFStringEncodingUTF8
    )
    if string is None:
        buffer = ctypes.create_string_buffer(1024)
        result = CoreFoundation.CFStringGetCString(
            value_as_void_p, buffer, 1024, CFConst.kCFStringEncodingUTF8
        )
        if not result:
            raise OSError("Error copying C string from CFStringRef")
        string = buffer.value
    if string is not None:
        string = string.decode("utf-8")
    return string


def _assert_no_error(error, exception_class=None):
    """
    Checks the return code and throws an exception if there is an error to
    report
    """
    if error == 0:
        return

    cf_error_string = Security.SecCopyErrorMessageString(error, None)
    output = _cf_string_to_unicode(cf_error_string)
    CoreFoundation.CFRelease(cf_error_string)

    if output is None or output == u"":
        output = u"OSStatus %s" % error

    if exception_class is None:
        exception_class = ssl.SSLError

    raise exception_class(output)


def _cert_array_from_pem(pem_bundle):
    """
    Given a bundle of certs in PEM format, turns them into a CFArray of certs
    that can be used to validate a cert chain.
    """
    # Normalize the PEM bundle's line endings.
    pem_bundle = pem_bundle.replace(b"\r\n", b"\n")

    der_certs = [
        base64.b64decode(match.group(1)) for match in _PEM_CERTS_RE.finditer(pem_bundle)
    ]
    if not der_certs:
        raise ssl.SSLError("No root certificates specified")

    cert_array = CoreFoundation.CFArrayCreateMutable(
        CoreFoundation.kCFAllocatorDefault,
        0,
        ctypes.byref(CoreFoundation.kCFTypeArrayCallBacks),
    )
    if not cert_array:
        raise ssl.SSLError("Unable to allocate memory!")

    try:
        for der_bytes in der_certs:
            certdata = _cf_data_from_bytes(der_bytes)
            if not certdata:
                raise ssl.SSLError("Unable to allocate memory!")
            cert = Security.SecCertificateCreateWithData(
                CoreFoundation.kCFAllocatorDefault, certdata
            )
            CoreFoundation.CFRelease(certdata)
            if not cert:
                raise ssl.SSLError("Unable to build cert object!")

            CoreFoundation.CFArrayAppendValue(cert_array, cert)
            CoreFoundation.CFRelease(cert)
    except Exception:
        # We need to free the array before the exception bubbles further.
        # We only want to do that if an error occurs: otherwise, the caller
        # should free.
        CoreFoundation.CFRelease(cert_array)
        raise

    return cert_array


def _is_cert(item):
    """
    Returns True if a given CFTypeRef is a certificate.
    """
    expected = Security.SecCertificateGetTypeID()
    return CoreFoundation.CFGetTypeID(item) == expected


def _is_identity(item):
    """
    Returns True if a given CFTypeRef is an identity.
    """
    expected = Security.SecIdentityGetTypeID()
    return CoreFoundation.CFGetTypeID(item) == expected


def _temporary_keychain():
    """
    This function creates a temporary Mac keychain that we can use to work with
    credentials. This keychain uses a one-time password and a temporary file to
    store the data. We expect to have one keychain per socket. The returned
    SecKeychainRef must be freed by the caller, including calling
    SecKeychainDelete.

    Returns a tuple of the SecKeychainRef and the path to the temporary
    directory that contains it.
    """
    # Unfortunately, SecKeychainCreate requires a path to a keychain. This
    # means we cannot use mkstemp to use a generic temporary file. Instead,
    # we're going to create a temporary directory and a filename to use there.
    # This filename will be 8 random bytes expanded into base64. We also need
    # some random bytes to password-protect the keychain we're creating, so we
    # ask for 40 random bytes.
    random_bytes = os.urandom(40)
    filename = base64.b16encode(random_bytes[:8]).decode("utf-8")
    password = base64.b16encode(random_bytes[8:])  # Must be valid UTF-8
    tempdirectory = tempfile.mkdtemp()

    keychain_path = os.path.join(tempdirectory, filename).encode("utf-8")

    # We now want to create the keychain itself.
    keychain = Security.SecKeychainRef()
    status = Security.SecKeychainCreate(
        keychain_path, len(password), password, False, None, ctypes.byref(keychain)
    )
    _assert_no_error(status)

    # Having created the keychain, we want to pass it off to the caller.
    return keychain, tempdirectory


def _load_items_from_file(keychain, path):
    """
    Given a single file, loads all the trust objects from it into arrays and
    the keychain.
    Returns a tuple of lists: the first list is a list of identities, the
    second a list of certs.
    """
    certificates = []
    identities = []
    result_array = None

    with open(path, "rb") as f:
        raw_filedata = f.read()

    try:
        filedata = CoreFoundation.CFDataCreate(
            CoreFoundation.kCFAllocatorDefault, raw_filedata, len(raw_filedata)
        )
        result_array = CoreFoundation.CFArrayRef()
        result = Security.SecItemImport(
            filedata,  # cert data
            None,  # Filename, leaving it out for now
            None,  # What the type of the file is, we don't care
            None,  # what's in the file, we don't care
            0,  # import flags
            None,  # key params, can include passphrase in the future
            keychain,  # The keychain to insert into
            ctypes.byref(result_array),  # Results
        )
        _assert_no_error(result)

        # A CFArray is not very useful to us as an intermediary
        # representation, so we are going to extract the objects we want
        # and then free the array. We don't need to keep hold of keys: the
        # keychain already has them!
        result_count = CoreFoundation.CFArrayGetCount(result_array)
        for index in range(result_count):
            item = CoreFoundation.CFArrayGetValueAtIndex(result_array, index)
            item = ctypes.cast(item, CoreFoundation.CFTypeRef)

            if _is_cert(item):
                CoreFoundation.CFRetain(item)
                certificates.append(item)
            elif _is_identity(item):
                CoreFoundation.CFRetain(item)
                identities.append(item)
    finally:
        if result_array:
            CoreFoundation.CFRelease(result_array)

        CoreFoundation.CFRelease(filedata)

    return (identities, certificates)


def _load_client_cert_chain(keychain, *paths):
    """
    Load certificates and maybe keys from a number of files. Has the end goal
    of returning a CFArray containing one SecIdentityRef, and then zero or more
    SecCertificateRef objects, suitable for use as a client certificate trust
    chain.
    """
    # Ok, the strategy.
    #
    # This relies on knowing that macOS will not give you a SecIdentityRef
    # unless you have imported a key into a keychain. This is a somewhat
    # artificial limitation of macOS (for example, it doesn't necessarily
    # affect iOS), but there is nothing inside Security.framework that lets you
    # get a SecIdentityRef without having a key in a keychain.
    #
    # So the policy here is we take all the files and iterate them in order.
    # Each one will use SecItemImport to have one or more objects loaded from
    # it. We will also point at a keychain that macOS can use to work with the
    # private key.
    #
    # Once we have all the objects, we'll check what we actually have. If we
    # already have a SecIdentityRef in hand, fab: we'll use that. Otherwise,
    # we'll take the first certificate (which we assume to be our leaf) and
    # ask the keychain to give us a SecIdentityRef with that cert's associated
    # key.
    #
    # We'll then return a CFArray containing the trust chain: one
    # SecIdentityRef and then zero-or-more SecCertificateRef objects. The
    # responsibility for freeing this CFArray will be with the caller. This
    # CFArray must remain alive for the entire connection, so in practice it
    # will be stored with a single SSLSocket, along with the reference to the
    # keychain.
    certificates = []
    identities = []

    # Filter out bad paths.
    paths = (path for path in paths if path)

    try:
        for file_path in paths:
            new_identities, new_certs = _load_items_from_file(keychain, file_path)
            identities.extend(new_identities)
            certificates.extend(new_certs)

        # Ok, we have everything. The question is: do we have an identity? If
        # not, we want to grab one from the first cert we have.
        if not identities:
            new_identity = Security.SecIdentityRef()
            status = Security.SecIdentityCreateWithCertificate(
                keychain, certificates[0], ctypes.byref(new_identity)
            )
            _assert_no_error(status)
            identities.append(new_identity)

            # We now want to release the original certificate, as we no longer
            # need it.
            CoreFoundation.CFRelease(certificates.pop(0))

        # We now need to build a new CFArray that holds the trust chain.
        trust_chain = CoreFoundation.CFArrayCreateMutable(
            CoreFoundation.kCFAllocatorDefault,
            0,
            ctypes.byref(CoreFoundation.kCFTypeArrayCallBacks),
        )
        for item in itertools.chain(identities, certificates):
            # ArrayAppendValue does a CFRetain on the item. That's fine,
            # because the finally block will release our other refs to them.
            CoreFoundation.CFArrayAppendValue(trust_chain, item)

        return trust_chain
    finally:
        for obj in itertools.chain(identities, certificates):
            CoreFoundation.CFRelease(obj)


TLS_PROTOCOL_VERSIONS = {
    "SSLv2": (0, 2),
    "SSLv3": (3, 0),
    "TLSv1": (3, 1),
    "TLSv1.1": (3, 2),
    "TLSv1.2": (3, 3),
}


def _build_tls_unknown_ca_alert(version):
    """
    Builds a TLS alert record for an unknown CA.
    """
    ver_maj, ver_min = TLS_PROTOCOL_VERSIONS[version]
    severity_fatal = 0x02
    description_unknown_ca = 0x30
    msg = struct.pack(">BB", severity_fatal, description_unknown_ca)
    msg_len = len(msg)
    record_type_alert = 0x15
    record = struct.pack(">BBBH", record_type_alert, ver_maj, ver_min, msg_len) + msg
    return record
