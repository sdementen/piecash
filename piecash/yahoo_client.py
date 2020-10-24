"""Wrapper around Yahoo Finance API
https://query1.finance.yahoo.com/v7/finance/download/aapl?period1=1487685205&period2=1495457605&interval=1d&events=history&crumb=dU2hYSfAy9E
https://query1.finance.yahoo.com/v7/finance/quote?symbols=TLS.AX,MUS.AX
https://help.yahoo.com/kb/SLN2310.html
"""
import csv
import datetime
import logging
import re
from collections import namedtuple
from decimal import Decimal
from time import sleep

import pytz


MAX_ATTEMPT = 5

YAHOO_BASE_URL = "https://query1.finance.yahoo.com/v7/finance"

YahooSymbol = namedtuple("YahooSymbol", "name,symbol,exchange,timezone,currency,date,price")
YahooQuote = namedtuple("YahooQuote", "date,open,high,low,close,adj_close,volume")


def get_latest_quote(symbol):
    import requests

    resp = requests.get("{}/quote".format(YAHOO_BASE_URL), params={"symbols": symbol})
    resp.raise_for_status()

    try:
        data = resp.json()["quoteResponse"]["result"][0]
    except IndexError:
        from .core.commodity import GncCommodityError

        raise GncCommodityError("Can't find information on symbol '{}' on yahoo".format(symbol))

    tz = data["exchangeTimezoneName"]

    return YahooSymbol(
        data["longName"],
        data["symbol"],
        data["exchange"],
        tz,
        data["currency"],
        datetime.datetime.fromtimestamp(data["regularMarketTime"]).astimezone(pytz.timezone(tz)),
        data["regularMarketPrice"],
    )


crumble_link = "https://finance.yahoo.com/quote/{0}/history?p={0}"
crumble_regex = r'CrumbStore":{"crumb":"(.*?)"}'
quote_link = "https://query1.finance.yahoo.com/v7/finance/download/{}?period1={}&period2={}&interval=1d&events=history&crumb={}"


def get_crumble_and_cookie(symbol):
    import requests

    link = crumble_link.format(symbol)
    response = requests.get(link)
    cookie_str = response.headers["set-cookie"]

    match = re.search(crumble_regex, response.text)
    crumble_str = match.group(1)
    return crumble_str, cookie_str


def download_quote(symbol, date_from, date_to, tz=None):
    import requests

    def normalize(d):
        if isinstance(d, datetime.datetime):
            pass
        elif isinstance(d, datetime.date):
            d = datetime.datetime.combine(d, datetime.time(0))
        else:
            d = datetime.datetime.strptime(d, "%Y-%m-%d")
        if not d.tzinfo:
            assert tz
            # todo: understand yahoo behavior as even in the browser, I get
            # weird results ...
            # d = d.replace(tzinfo=tz)
        return d

    date_from = normalize(date_from)
    date_to = normalize(date_to)
    time_stamp_from = int(date_from.timestamp())
    time_stamp_to = int(date_to.timestamp())

    for i in range(MAX_ATTEMPT):
        logging.info("{} attempt to download quotes for symbol {} from yahoo".format(i, symbol))

        crumble_str, cookie_str = get_crumble_and_cookie(symbol)

        link = quote_link.format(symbol, time_stamp_from, time_stamp_to, crumble_str)

        resp = requests.get(link, headers={"Cookie": cookie_str})
        try:
            resp.raise_for_status()
        except Exception as e:
            sleep(2)
        else:
            break
    else:
        raise e

    csv_data = list(csv.reader(resp.text.strip().split("\n")))

    return [
        yq
        for data in csv_data[1:]
        for yq in [
            YahooQuote(
                datetime.datetime.strptime(data[0], "%Y-%m-%d").date(),
                *[Decimal(f) for f in data[1:]]
            )
        ]
        if date_from.date() <= yq.date <= date_to.date()
    ]


if __name__ == "__main__":
    print(get_latest_quote("KO"))

    print(download_quote("ENGI.PA", "2018-02-26", "2018-03-01", tz=pytz.timezone("CET")))

if __name__ == "__main__":
    print(get_latest_quote("ENGI.PA"))
    print(get_latest_quote("AAPL"))
