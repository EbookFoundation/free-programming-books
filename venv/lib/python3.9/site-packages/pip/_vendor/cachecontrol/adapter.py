# SPDX-FileCopyrightText: 2015 Eric Larson
#
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import functools
import types
import weakref
import zlib
from typing import TYPE_CHECKING, Any, Collection, Mapping

from pip._vendor.requests.adapters import HTTPAdapter

from pip._vendor.cachecontrol.cache import DictCache
from pip._vendor.cachecontrol.controller import PERMANENT_REDIRECT_STATUSES, CacheController
from pip._vendor.cachecontrol.filewrapper import CallbackFileWrapper

if TYPE_CHECKING:
    from pip._vendor.requests import PreparedRequest, Response
    from pip._vendor.urllib3 import HTTPResponse

    from pip._vendor.cachecontrol.cache import BaseCache
    from pip._vendor.cachecontrol.heuristics import BaseHeuristic
    from pip._vendor.cachecontrol.serialize import Serializer


class CacheControlAdapter(HTTPAdapter):
    invalidating_methods = {"PUT", "PATCH", "DELETE"}

    def __init__(
        self,
        cache: BaseCache | None = None,
        cache_etags: bool = True,
        controller_class: type[CacheController] | None = None,
        serializer: Serializer | None = None,
        heuristic: BaseHeuristic | None = None,
        cacheable_methods: Collection[str] | None = None,
        *args: Any,
        **kw: Any,
    ) -> None:
        super().__init__(*args, **kw)
        self.cache = DictCache() if cache is None else cache
        self.heuristic = heuristic
        self.cacheable_methods = cacheable_methods or ("GET",)

        controller_factory = controller_class or CacheController
        self.controller = controller_factory(
            self.cache, cache_etags=cache_etags, serializer=serializer
        )

    def send(
        self,
        request: PreparedRequest,
        stream: bool = False,
        timeout: None | float | tuple[float, float] | tuple[float, None] = None,
        verify: bool | str = True,
        cert: (None | bytes | str | tuple[bytes | str, bytes | str]) = None,
        proxies: Mapping[str, str] | None = None,
        cacheable_methods: Collection[str] | None = None,
    ) -> Response:
        """
        Send a request. Use the request information to see if it
        exists in the cache and cache the response if we need to and can.
        """
        cacheable = cacheable_methods or self.cacheable_methods
        if request.method in cacheable:
            try:
                cached_response = self.controller.cached_request(request)
            except zlib.error:
                cached_response = None
            if cached_response:
                return self.build_response(request, cached_response, from_cache=True)

            # check for etags and add headers if appropriate
            request.headers.update(self.controller.conditional_headers(request))

        resp = super().send(request, stream, timeout, verify, cert, proxies)

        return resp

    def build_response(  # type: ignore[override]
        self,
        request: PreparedRequest,
        response: HTTPResponse,
        from_cache: bool = False,
        cacheable_methods: Collection[str] | None = None,
    ) -> Response:
        """
        Build a response by making a request or using the cache.

        This will end up calling send and returning a potentially
        cached response
        """
        cacheable = cacheable_methods or self.cacheable_methods
        if not from_cache and request.method in cacheable:
            # Check for any heuristics that might update headers
            # before trying to cache.
            if self.heuristic:
                response = self.heuristic.apply(response)

            # apply any expiration heuristics
            if response.status == 304:
                # We must have sent an ETag request. This could mean
                # that we've been expired already or that we simply
                # have an etag. In either case, we want to try and
                # update the cache if that is the case.
                cached_response = self.controller.update_cached_response(
                    request, response
                )

                if cached_response is not response:
                    from_cache = True

                # We are done with the server response, read a
                # possible response body (compliant servers will
                # not return one, but we cannot be 100% sure) and
                # release the connection back to the pool.
                response.read(decode_content=False)
                response.release_conn()

                response = cached_response

            # We always cache the 301 responses
            elif int(response.status) in PERMANENT_REDIRECT_STATUSES:
                self.controller.cache_response(request, response)
            else:
                # Wrap the response file with a wrapper that will cache the
                #   response when the stream has been consumed.
                response._fp = CallbackFileWrapper(  # type: ignore[assignment]
                    response._fp,  # type: ignore[arg-type]
                    functools.partial(
                        self.controller.cache_response, request, weakref.ref(response)
                    ),
                )
                if response.chunked:
                    super_update_chunk_length = response.__class__._update_chunk_length

                    def _update_chunk_length(
                        weak_self: weakref.ReferenceType[HTTPResponse],
                    ) -> None:
                        self = weak_self()
                        if self is None:
                            return

                        super_update_chunk_length(self)
                        if self.chunk_left == 0:
                            self._fp._close()  # type: ignore[union-attr]

                    response._update_chunk_length = functools.partial(  # type: ignore[method-assign]
                        _update_chunk_length, weakref.ref(response)
                    )

        resp: Response = super().build_response(request, response)

        # See if we should invalidate the cache.
        if request.method in self.invalidating_methods and resp.ok:
            assert request.url is not None
            cache_url = self.controller.cache_url(request.url)
            self.cache.delete(cache_url)

        # Give the request a from_cache attr to let people use it
        resp.from_cache = from_cache  # type: ignore[attr-defined]

        return resp

    def close(self) -> None:
        self.cache.close()
        super().close()  # type: ignore[no-untyped-call]
