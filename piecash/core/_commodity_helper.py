import logging
from collections import namedtuple
import json

__author__ = 'sdementen'


def run_yql(yql, scalar=False):
    # run a yql query and return results as list or scalar
    import requests

    DATATABLES_URL = 'store://datatables.org/alltableswithkeys'
    PUBLIC_API_URL = 'http://query.yahooapis.com/v1/public/yql'
    text_result = requests.get(PUBLIC_API_URL, params={'q': "env 'store://datatables.org/alltableswithkeys';" + yql, 'format': 'json'}).text
    try:
        query_result = json.loads(text_result)["query"]
    except ValueError:
        logging.error(u"issue when retrieving info from yahooapis.com : '{}'".format(text_result))
        return []

    if query_result["count"] == 0:
        # no results
        return None if scalar else []

    quotes = query_result["results"]["quote"]
    fields = (quotes if scalar else quotes[0]).keys()
    yql_result = namedtuple("YQL", fields)

    if scalar:
        return yql_result(**quotes)
    else:
        return [yql_result(**v) for v in quotes]


def quandl_fx(fx_mnemonic, base_mnemonic, start_date):
    """Retrieve exchange rate of commodity fx in function of base
    """
    import requests

    PUBLIC_API_URL = 'http://www.quandl.com/api/v1/datasets/CURRFX/{}{}.json'.format(fx_mnemonic, base_mnemonic)
    text_result = requests.get(PUBLIC_API_URL, params={'request_source': 'python', 'request_version': 2,
                                                       'trim_start': "{:%Y-%m-%d}".format(start_date)}).text
    try:
        query_result = json.loads(text_result)
    except ValueError:
        logging.error("issue when retrieving info from quandl.com : '{}'".format(text_result))
        return []
    if "error" in query_result:
        logging.error("issue when retrieving info from quandl.com : '{}'".format(query_result["error"]))
        return []
    if "errors" in query_result:
        logging.error("issue when retrieving info from quandl.com : '{}'".format(query_result["errors"]))
        return []

    rows = query_result["data"]

    qdl_result = namedtuple("QUANDL", ["date", "rate", "high", "low"])

    return [qdl_result(*v) for v in rows]
