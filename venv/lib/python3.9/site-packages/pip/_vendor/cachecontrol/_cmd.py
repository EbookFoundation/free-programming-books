# SPDX-FileCopyrightText: 2015 Eric Larson
#
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import logging
from argparse import ArgumentParser
from typing import TYPE_CHECKING

from pip._vendor import requests

from pip._vendor.cachecontrol.adapter import CacheControlAdapter
from pip._vendor.cachecontrol.cache import DictCache
from pip._vendor.cachecontrol.controller import logger

if TYPE_CHECKING:
    from argparse import Namespace

    from pip._vendor.cachecontrol.controller import CacheController


def setup_logging() -> None:
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    logger.addHandler(handler)


def get_session() -> requests.Session:
    adapter = CacheControlAdapter(
        DictCache(), cache_etags=True, serializer=None, heuristic=None
    )
    sess = requests.Session()
    sess.mount("http://", adapter)
    sess.mount("https://", adapter)

    sess.cache_controller = adapter.controller  # type: ignore[attr-defined]
    return sess


def get_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument("url", help="The URL to try and cache")
    return parser.parse_args()


def main() -> None:
    args = get_args()
    sess = get_session()

    # Make a request to get a response
    resp = sess.get(args.url)

    # Turn on logging
    setup_logging()

    # try setting the cache
    cache_controller: CacheController = (
        sess.cache_controller  # type: ignore[attr-defined]
    )
    cache_controller.cache_response(resp.request, resp.raw)

    # Now try to get it
    if cache_controller.cached_request(resp.request):
        print("Cached!")
    else:
        print("Not cached :(")


if __name__ == "__main__":
    main()
