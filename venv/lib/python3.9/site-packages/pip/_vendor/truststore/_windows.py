import contextlib
import ssl
import typing
from ctypes import WinDLL  # type: ignore
from ctypes import WinError  # type: ignore
from ctypes import (
    POINTER,
    Structure,
    c_char_p,
    c_ulong,
    c_void_p,
    c_wchar_p,
    cast,
    create_unicode_buffer,
    pointer,
    sizeof,
)
from ctypes.wintypes import (
    BOOL,
    DWORD,
    HANDLE,
    LONG,
    LPCSTR,
    LPCVOID,
    LPCWSTR,
    LPFILETIME,
    LPSTR,
    LPWSTR,
)
from typing import TYPE_CHECKING, Any

from ._ssl_constants import _set_ssl_context_verify_mode

HCERTCHAINENGINE = HANDLE
HCERTSTORE = HANDLE
HCRYPTPROV_LEGACY = HANDLE


class CERT_CONTEXT(Structure):
    _fields_ = (
        ("dwCertEncodingType", DWORD),
        ("pbCertEncoded", c_void_p),
        ("cbCertEncoded", DWORD),
        ("pCertInfo", c_void_p),
        ("hCertStore", HCERTSTORE),
    )


PCERT_CONTEXT = POINTER(CERT_CONTEXT)
PCCERT_CONTEXT = POINTER(PCERT_CONTEXT)


class CERT_ENHKEY_USAGE(Structure):
    _fields_ = (
        ("cUsageIdentifier", DWORD),
        ("rgpszUsageIdentifier", POINTER(LPSTR)),
    )


PCERT_ENHKEY_USAGE = POINTER(CERT_ENHKEY_USAGE)


class CERT_USAGE_MATCH(Structure):
    _fields_ = (
        ("dwType", DWORD),
        ("Usage", CERT_ENHKEY_USAGE),
    )


class CERT_CHAIN_PARA(Structure):
    _fields_ = (
        ("cbSize", DWORD),
        ("RequestedUsage", CERT_USAGE_MATCH),
        ("RequestedIssuancePolicy", CERT_USAGE_MATCH),
        ("dwUrlRetrievalTimeout", DWORD),
        ("fCheckRevocationFreshnessTime", BOOL),
        ("dwRevocationFreshnessTime", DWORD),
        ("pftCacheResync", LPFILETIME),
        ("pStrongSignPara", c_void_p),
        ("dwStrongSignFlags", DWORD),
    )


if TYPE_CHECKING:
    PCERT_CHAIN_PARA = pointer[CERT_CHAIN_PARA]  # type: ignore[misc]
else:
    PCERT_CHAIN_PARA = POINTER(CERT_CHAIN_PARA)


class CERT_TRUST_STATUS(Structure):
    _fields_ = (
        ("dwErrorStatus", DWORD),
        ("dwInfoStatus", DWORD),
    )


class CERT_CHAIN_ELEMENT(Structure):
    _fields_ = (
        ("cbSize", DWORD),
        ("pCertContext", PCERT_CONTEXT),
        ("TrustStatus", CERT_TRUST_STATUS),
        ("pRevocationInfo", c_void_p),
        ("pIssuanceUsage", PCERT_ENHKEY_USAGE),
        ("pApplicationUsage", PCERT_ENHKEY_USAGE),
        ("pwszExtendedErrorInfo", LPCWSTR),
    )


PCERT_CHAIN_ELEMENT = POINTER(CERT_CHAIN_ELEMENT)


class CERT_SIMPLE_CHAIN(Structure):
    _fields_ = (
        ("cbSize", DWORD),
        ("TrustStatus", CERT_TRUST_STATUS),
        ("cElement", DWORD),
        ("rgpElement", POINTER(PCERT_CHAIN_ELEMENT)),
        ("pTrustListInfo", c_void_p),
        ("fHasRevocationFreshnessTime", BOOL),
        ("dwRevocationFreshnessTime", DWORD),
    )


PCERT_SIMPLE_CHAIN = POINTER(CERT_SIMPLE_CHAIN)


class CERT_CHAIN_CONTEXT(Structure):
    _fields_ = (
        ("cbSize", DWORD),
        ("TrustStatus", CERT_TRUST_STATUS),
        ("cChain", DWORD),
        ("rgpChain", POINTER(PCERT_SIMPLE_CHAIN)),
        ("cLowerQualityChainContext", DWORD),
        ("rgpLowerQualityChainContext", c_void_p),
        ("fHasRevocationFreshnessTime", BOOL),
        ("dwRevocationFreshnessTime", DWORD),
    )


PCERT_CHAIN_CONTEXT = POINTER(CERT_CHAIN_CONTEXT)
PCCERT_CHAIN_CONTEXT = POINTER(PCERT_CHAIN_CONTEXT)


class SSL_EXTRA_CERT_CHAIN_POLICY_PARA(Structure):
    _fields_ = (
        ("cbSize", DWORD),
        ("dwAuthType", DWORD),
        ("fdwChecks", DWORD),
        ("pwszServerName", LPCWSTR),
    )


class CERT_CHAIN_POLICY_PARA(Structure):
    _fields_ = (
        ("cbSize", DWORD),
        ("dwFlags", DWORD),
        ("pvExtraPolicyPara", c_void_p),
    )


PCERT_CHAIN_POLICY_PARA = POINTER(CERT_CHAIN_POLICY_PARA)


class CERT_CHAIN_POLICY_STATUS(Structure):
    _fields_ = (
        ("cbSize", DWORD),
        ("dwError", DWORD),
        ("lChainIndex", LONG),
        ("lElementIndex", LONG),
        ("pvExtraPolicyStatus", c_void_p),
    )


PCERT_CHAIN_POLICY_STATUS = POINTER(CERT_CHAIN_POLICY_STATUS)


class CERT_CHAIN_ENGINE_CONFIG(Structure):
    _fields_ = (
        ("cbSize", DWORD),
        ("hRestrictedRoot", HCERTSTORE),
        ("hRestrictedTrust", HCERTSTORE),
        ("hRestrictedOther", HCERTSTORE),
        ("cAdditionalStore", DWORD),
        ("rghAdditionalStore", c_void_p),
        ("dwFlags", DWORD),
        ("dwUrlRetrievalTimeout", DWORD),
        ("MaximumCachedCertificates", DWORD),
        ("CycleDetectionModulus", DWORD),
        ("hExclusiveRoot", HCERTSTORE),
        ("hExclusiveTrustedPeople", HCERTSTORE),
        ("dwExclusiveFlags", DWORD),
    )


PCERT_CHAIN_ENGINE_CONFIG = POINTER(CERT_CHAIN_ENGINE_CONFIG)
PHCERTCHAINENGINE = POINTER(HCERTCHAINENGINE)

X509_ASN_ENCODING = 0x00000001
PKCS_7_ASN_ENCODING = 0x00010000
CERT_STORE_PROV_MEMORY = b"Memory"
CERT_STORE_ADD_USE_EXISTING = 2
USAGE_MATCH_TYPE_OR = 1
OID_PKIX_KP_SERVER_AUTH = c_char_p(b"1.3.6.1.5.5.7.3.1")
CERT_CHAIN_REVOCATION_CHECK_END_CERT = 0x10000000
CERT_CHAIN_REVOCATION_CHECK_CHAIN = 0x20000000
CERT_CHAIN_POLICY_IGNORE_ALL_NOT_TIME_VALID_FLAGS = 0x00000007
CERT_CHAIN_POLICY_IGNORE_INVALID_BASIC_CONSTRAINTS_FLAG = 0x00000008
CERT_CHAIN_POLICY_ALLOW_UNKNOWN_CA_FLAG = 0x00000010
CERT_CHAIN_POLICY_IGNORE_INVALID_NAME_FLAG = 0x00000040
CERT_CHAIN_POLICY_IGNORE_WRONG_USAGE_FLAG = 0x00000020
CERT_CHAIN_POLICY_IGNORE_INVALID_POLICY_FLAG = 0x00000080
CERT_CHAIN_POLICY_IGNORE_ALL_REV_UNKNOWN_FLAGS = 0x00000F00
CERT_CHAIN_POLICY_ALLOW_TESTROOT_FLAG = 0x00008000
CERT_CHAIN_POLICY_TRUST_TESTROOT_FLAG = 0x00004000
SECURITY_FLAG_IGNORE_CERT_CN_INVALID = 0x00001000
AUTHTYPE_SERVER = 2
CERT_CHAIN_POLICY_SSL = 4
FORMAT_MESSAGE_FROM_SYSTEM = 0x00001000
FORMAT_MESSAGE_IGNORE_INSERTS = 0x00000200

# Flags to set for SSLContext.verify_mode=CERT_NONE
CERT_CHAIN_POLICY_VERIFY_MODE_NONE_FLAGS = (
    CERT_CHAIN_POLICY_IGNORE_ALL_NOT_TIME_VALID_FLAGS
    | CERT_CHAIN_POLICY_IGNORE_INVALID_BASIC_CONSTRAINTS_FLAG
    | CERT_CHAIN_POLICY_ALLOW_UNKNOWN_CA_FLAG
    | CERT_CHAIN_POLICY_IGNORE_INVALID_NAME_FLAG
    | CERT_CHAIN_POLICY_IGNORE_WRONG_USAGE_FLAG
    | CERT_CHAIN_POLICY_IGNORE_INVALID_POLICY_FLAG
    | CERT_CHAIN_POLICY_IGNORE_ALL_REV_UNKNOWN_FLAGS
    | CERT_CHAIN_POLICY_ALLOW_TESTROOT_FLAG
    | CERT_CHAIN_POLICY_TRUST_TESTROOT_FLAG
)

wincrypt = WinDLL("crypt32.dll")
kernel32 = WinDLL("kernel32.dll")


def _handle_win_error(result: bool, _: Any, args: Any) -> Any:
    if not result:
        # Note, actually raises OSError after calling GetLastError and FormatMessage
        raise WinError()
    return args


CertCreateCertificateChainEngine = wincrypt.CertCreateCertificateChainEngine
CertCreateCertificateChainEngine.argtypes = (
    PCERT_CHAIN_ENGINE_CONFIG,
    PHCERTCHAINENGINE,
)
CertCreateCertificateChainEngine.errcheck = _handle_win_error

CertOpenStore = wincrypt.CertOpenStore
CertOpenStore.argtypes = (LPCSTR, DWORD, HCRYPTPROV_LEGACY, DWORD, c_void_p)
CertOpenStore.restype = HCERTSTORE
CertOpenStore.errcheck = _handle_win_error

CertAddEncodedCertificateToStore = wincrypt.CertAddEncodedCertificateToStore
CertAddEncodedCertificateToStore.argtypes = (
    HCERTSTORE,
    DWORD,
    c_char_p,
    DWORD,
    DWORD,
    PCCERT_CONTEXT,
)
CertAddEncodedCertificateToStore.restype = BOOL

CertCreateCertificateContext = wincrypt.CertCreateCertificateContext
CertCreateCertificateContext.argtypes = (DWORD, c_char_p, DWORD)
CertCreateCertificateContext.restype = PCERT_CONTEXT
CertCreateCertificateContext.errcheck = _handle_win_error

CertGetCertificateChain = wincrypt.CertGetCertificateChain
CertGetCertificateChain.argtypes = (
    HCERTCHAINENGINE,
    PCERT_CONTEXT,
    LPFILETIME,
    HCERTSTORE,
    PCERT_CHAIN_PARA,
    DWORD,
    c_void_p,
    PCCERT_CHAIN_CONTEXT,
)
CertGetCertificateChain.restype = BOOL
CertGetCertificateChain.errcheck = _handle_win_error

CertVerifyCertificateChainPolicy = wincrypt.CertVerifyCertificateChainPolicy
CertVerifyCertificateChainPolicy.argtypes = (
    c_ulong,
    PCERT_CHAIN_CONTEXT,
    PCERT_CHAIN_POLICY_PARA,
    PCERT_CHAIN_POLICY_STATUS,
)
CertVerifyCertificateChainPolicy.restype = BOOL

CertCloseStore = wincrypt.CertCloseStore
CertCloseStore.argtypes = (HCERTSTORE, DWORD)
CertCloseStore.restype = BOOL
CertCloseStore.errcheck = _handle_win_error

CertFreeCertificateChain = wincrypt.CertFreeCertificateChain
CertFreeCertificateChain.argtypes = (PCERT_CHAIN_CONTEXT,)

CertFreeCertificateContext = wincrypt.CertFreeCertificateContext
CertFreeCertificateContext.argtypes = (PCERT_CONTEXT,)

CertFreeCertificateChainEngine = wincrypt.CertFreeCertificateChainEngine
CertFreeCertificateChainEngine.argtypes = (HCERTCHAINENGINE,)

FormatMessageW = kernel32.FormatMessageW
FormatMessageW.argtypes = (
    DWORD,
    LPCVOID,
    DWORD,
    DWORD,
    LPWSTR,
    DWORD,
    c_void_p,
)
FormatMessageW.restype = DWORD


def _verify_peercerts_impl(
    ssl_context: ssl.SSLContext,
    cert_chain: list[bytes],
    server_hostname: str | None = None,
) -> None:
    """Verify the cert_chain from the server using Windows APIs."""

    # If the peer didn't send any certificates then
    # we can't do verification. Raise an error.
    if not cert_chain:
        raise ssl.SSLCertVerificationError("Peer sent no certificates to verify")

    pCertContext = None
    hIntermediateCertStore = CertOpenStore(CERT_STORE_PROV_MEMORY, 0, None, 0, None)
    try:
        # Add intermediate certs to an in-memory cert store
        for cert_bytes in cert_chain[1:]:
            CertAddEncodedCertificateToStore(
                hIntermediateCertStore,
                X509_ASN_ENCODING | PKCS_7_ASN_ENCODING,
                cert_bytes,
                len(cert_bytes),
                CERT_STORE_ADD_USE_EXISTING,
                None,
            )

        # Cert context for leaf cert
        leaf_cert = cert_chain[0]
        pCertContext = CertCreateCertificateContext(
            X509_ASN_ENCODING | PKCS_7_ASN_ENCODING, leaf_cert, len(leaf_cert)
        )

        # Chain params to match certs for serverAuth extended usage
        cert_enhkey_usage = CERT_ENHKEY_USAGE()
        cert_enhkey_usage.cUsageIdentifier = 1
        cert_enhkey_usage.rgpszUsageIdentifier = (c_char_p * 1)(OID_PKIX_KP_SERVER_AUTH)
        cert_usage_match = CERT_USAGE_MATCH()
        cert_usage_match.Usage = cert_enhkey_usage
        chain_params = CERT_CHAIN_PARA()
        chain_params.RequestedUsage = cert_usage_match
        chain_params.cbSize = sizeof(chain_params)
        pChainPara = pointer(chain_params)

        if ssl_context.verify_flags & ssl.VERIFY_CRL_CHECK_CHAIN:
            chain_flags = CERT_CHAIN_REVOCATION_CHECK_CHAIN
        elif ssl_context.verify_flags & ssl.VERIFY_CRL_CHECK_LEAF:
            chain_flags = CERT_CHAIN_REVOCATION_CHECK_END_CERT
        else:
            chain_flags = 0

        try:
            # First attempt to verify using the default Windows system trust roots
            # (default chain engine).
            _get_and_verify_cert_chain(
                ssl_context,
                None,
                hIntermediateCertStore,
                pCertContext,
                pChainPara,
                server_hostname,
                chain_flags=chain_flags,
            )
        except ssl.SSLCertVerificationError as e:
            # If that fails but custom CA certs have been added
            # to the SSLContext using load_verify_locations,
            # try verifying using a custom chain engine
            # that trusts the custom CA certs.
            custom_ca_certs: list[bytes] | None = ssl_context.get_ca_certs(
                binary_form=True
            )
            if custom_ca_certs:
                try:
                    _verify_using_custom_ca_certs(
                        ssl_context,
                        custom_ca_certs,
                        hIntermediateCertStore,
                        pCertContext,
                        pChainPara,
                        server_hostname,
                        chain_flags=chain_flags,
                    )
                # Raise the original error, not the new error.
                except ssl.SSLCertVerificationError:
                    raise e from None
            else:
                raise
    finally:
        CertCloseStore(hIntermediateCertStore, 0)
        if pCertContext:
            CertFreeCertificateContext(pCertContext)


def _get_and_verify_cert_chain(
    ssl_context: ssl.SSLContext,
    hChainEngine: HCERTCHAINENGINE | None,
    hIntermediateCertStore: HCERTSTORE,
    pPeerCertContext: c_void_p,
    pChainPara: PCERT_CHAIN_PARA,  # type: ignore[valid-type]
    server_hostname: str | None,
    chain_flags: int,
) -> None:
    ppChainContext = None
    try:
        # Get cert chain
        ppChainContext = pointer(PCERT_CHAIN_CONTEXT())
        CertGetCertificateChain(
            hChainEngine,  # chain engine
            pPeerCertContext,  # leaf cert context
            None,  # current system time
            hIntermediateCertStore,  # additional in-memory cert store
            pChainPara,  # chain-building parameters
            chain_flags,
            None,  # reserved
            ppChainContext,  # the resulting chain context
        )
        pChainContext = ppChainContext.contents

        # Verify cert chain
        ssl_extra_cert_chain_policy_para = SSL_EXTRA_CERT_CHAIN_POLICY_PARA()
        ssl_extra_cert_chain_policy_para.cbSize = sizeof(
            ssl_extra_cert_chain_policy_para
        )
        ssl_extra_cert_chain_policy_para.dwAuthType = AUTHTYPE_SERVER
        ssl_extra_cert_chain_policy_para.fdwChecks = 0
        if ssl_context.check_hostname is False:
            ssl_extra_cert_chain_policy_para.fdwChecks = (
                SECURITY_FLAG_IGNORE_CERT_CN_INVALID
            )
        if server_hostname:
            ssl_extra_cert_chain_policy_para.pwszServerName = c_wchar_p(server_hostname)

        chain_policy = CERT_CHAIN_POLICY_PARA()
        chain_policy.pvExtraPolicyPara = cast(
            pointer(ssl_extra_cert_chain_policy_para), c_void_p
        )
        if ssl_context.verify_mode == ssl.CERT_NONE:
            chain_policy.dwFlags |= CERT_CHAIN_POLICY_VERIFY_MODE_NONE_FLAGS
        chain_policy.cbSize = sizeof(chain_policy)

        pPolicyPara = pointer(chain_policy)
        policy_status = CERT_CHAIN_POLICY_STATUS()
        policy_status.cbSize = sizeof(policy_status)
        pPolicyStatus = pointer(policy_status)
        CertVerifyCertificateChainPolicy(
            CERT_CHAIN_POLICY_SSL,
            pChainContext,
            pPolicyPara,
            pPolicyStatus,
        )

        # Check status
        error_code = policy_status.dwError
        if error_code:
            # Try getting a human readable message for an error code.
            error_message_buf = create_unicode_buffer(1024)
            error_message_chars = FormatMessageW(
                FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS,
                None,
                error_code,
                0,
                error_message_buf,
                sizeof(error_message_buf),
                None,
            )

            # See if we received a message for the error,
            # otherwise we use a generic error with the
            # error code and hope that it's search-able.
            if error_message_chars <= 0:
                error_message = f"Certificate chain policy error {error_code:#x} [{policy_status.lElementIndex}]"
            else:
                error_message = error_message_buf.value.strip()

            err = ssl.SSLCertVerificationError(error_message)
            err.verify_message = error_message
            err.verify_code = error_code
            raise err from None
    finally:
        if ppChainContext:
            CertFreeCertificateChain(ppChainContext.contents)


def _verify_using_custom_ca_certs(
    ssl_context: ssl.SSLContext,
    custom_ca_certs: list[bytes],
    hIntermediateCertStore: HCERTSTORE,
    pPeerCertContext: c_void_p,
    pChainPara: PCERT_CHAIN_PARA,  # type: ignore[valid-type]
    server_hostname: str | None,
    chain_flags: int,
) -> None:
    hChainEngine = None
    hRootCertStore = CertOpenStore(CERT_STORE_PROV_MEMORY, 0, None, 0, None)
    try:
        # Add custom CA certs to an in-memory cert store
        for cert_bytes in custom_ca_certs:
            CertAddEncodedCertificateToStore(
                hRootCertStore,
                X509_ASN_ENCODING | PKCS_7_ASN_ENCODING,
                cert_bytes,
                len(cert_bytes),
                CERT_STORE_ADD_USE_EXISTING,
                None,
            )

        # Create a custom cert chain engine which exclusively trusts
        # certs from our hRootCertStore
        cert_chain_engine_config = CERT_CHAIN_ENGINE_CONFIG()
        cert_chain_engine_config.cbSize = sizeof(cert_chain_engine_config)
        cert_chain_engine_config.hExclusiveRoot = hRootCertStore
        pConfig = pointer(cert_chain_engine_config)
        phChainEngine = pointer(HCERTCHAINENGINE())
        CertCreateCertificateChainEngine(
            pConfig,
            phChainEngine,
        )
        hChainEngine = phChainEngine.contents

        # Get and verify a cert chain using the custom chain engine
        _get_and_verify_cert_chain(
            ssl_context,
            hChainEngine,
            hIntermediateCertStore,
            pPeerCertContext,
            pChainPara,
            server_hostname,
            chain_flags,
        )
    finally:
        if hChainEngine:
            CertFreeCertificateChainEngine(hChainEngine)
        CertCloseStore(hRootCertStore, 0)


@contextlib.contextmanager
def _configure_context(ctx: ssl.SSLContext) -> typing.Iterator[None]:
    check_hostname = ctx.check_hostname
    verify_mode = ctx.verify_mode
    ctx.check_hostname = False
    _set_ssl_context_verify_mode(ctx, ssl.CERT_NONE)
    try:
        yield
    finally:
        ctx.check_hostname = check_hostname
        _set_ssl_context_verify_mode(ctx, verify_mode)
