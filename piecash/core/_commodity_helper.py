import json
import logging
import os
from collections import namedtuple

__author__ = "sdementen"


def quandl_fx(fx_mnemonic, base_mnemonic, start_date):
    """Retrieve exchange rate of commodity fx in function of base.

    API KEY will be retrieved from the environment variable QUANDL_API_KEY
    """
    import requests

    PUBLIC_API_URL = "https://www.quandl.com/api/v1/datasets/CURRFX/{}{}.json".format(
        fx_mnemonic, base_mnemonic
    )
    params = {
        "request_source": "python",
        "request_version": 2,
        "trim_start": "{:%Y-%m-%d}".format(start_date),
    }

    # adapt quandl parameters  with apikey if given in environment variable QUANDL_API_KEY
    apikey = os.environ.get("QUANDL_API_KEY")
    if apikey:
        params["api_key"] = apikey

    text_result = requests.get(PUBLIC_API_URL, params=params).text
    try:
        query_result = json.loads(text_result)
    except ValueError:
        logging.error("issue when retrieving info from quandl.com : '{}'".format(text_result))
        return []
    if "error" in query_result:
        logging.error(
            "issue when retrieving info from quandl.com : '{}'".format(query_result["error"])
        )
        return []
    if "quandl_error" in query_result:
        logging.error(
            "issue when retrieving info from quandl.com : '{}'".format(query_result["quandl_error"])
        )
        return []
    if "errors" in query_result and query_result["errors"]:
        logging.error(
            "issue when retrieving info from quandl.com : '{}'".format(query_result["errors"])
        )
        return []

    rows = query_result["data"]

    qdl_result = namedtuple("QUANDL", ["date", "rate", "high", "low"])

    return [qdl_result(*v) for v in rows]
