from time import sleep
from tqdm import tqdm
from urllib.request import urlopen
import json
from collections import defaultdict
from io import BytesIO
from zipfile import ZipFile
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from dateutil import tz
from copy import deepcopy
from bs4 import BeautifulSoup


# Start date for calculating seconds
UNIX_START = datetime(1970, 1, 1)


def date2daily(str_time):
    x = datetime.strptime(str_time, '%Y-%m-%d %H:%M:%S')
    daily = "%04d-%02d-%02d" % (x.year, x.month, x.day)
    return daily


def daily2date(daily):
    x = datetime.strptime(daily, "%Y-%m-%d")
    date = "%04d-%02d-%02d 00:00:00" % (x.year, x.month, x.day)
    return date


def date2datetime(str_time):
    str_time = str(str_time)
    datetime_obj = datetime.strptime(str_time, '%Y-%m-%d %H:%M:%S')
    return datetime_obj


def date2seconds(str_time):
    datetime_obj = date2datetime(str_time)
    seconds = (datetime_obj - UNIX_START).total_seconds()
    return seconds


def seconds2datetime(seconds):
    datetime_obj = datetime.fromtimestamp(seconds, timezone.utc)
    datetime_obj = datetime(datetime_obj.year,
                            datetime_obj.month,
                            datetime_obj.day,
                            datetime_obj.hour,
                            datetime_obj.minute,
                            datetime_obj.second)
    return datetime_obj


def seconds2date(seconds):
    date_obj = seconds2datetime(seconds)
    return datetime2date(date_obj)


def datetime2date(datetime_obj):
    str_time = '%04d-%02d-%02d %02d:%02d:%02d'
    return str_time % (datetime_obj.year, datetime_obj.month,
                       datetime_obj.day, datetime_obj.hour,
                       datetime_obj.minute, datetime_obj.second)


def date2str(date):
    str_date = '%04d-%02d-%02d %02d:%02d:%02d' %\
        (date.year, date.month, date.day, date.hour, date.minute, date.second)
    return str_date


def get_time_now(is_local=False):
    date = datetime.utcnow()
    if is_local:
        to_zone = tz.tzlocal()
        # Convert time zone
        date = date.astimezone(to_zone)
        date = date.now()
    return date2str(date)


def get_data(ticker, start, end=None, period=30, exchange="polo"):
    """Get OHLCV data from the source

    Parameters
    ----------
    ticker: str
        The symbol of stocks or coin
    start: '%Y-%m-%d %H:%M:%S'
        The start point for fetching data
    end: '%Y-%m-%d %H:%M:%S', optional
        The end point for fetching data
    period: int
        The frequency of bar (sec)
    exchange: str, (default 'polo')
        THe name of exchange to use

    Returns
    -------
    pd.DataFrame: OHLCV data
    """
    # We do not want to include start time
    start_sc = date2seconds(start) + 1
    if end is None:
        end = get_time_now()
    end_sc = date2seconds(end)
    print(start_sc, end_sc)
    print(start_sc, end_sc)
    print(start, end)
    if exchange == "polo":
        base_url = "https://poloniex.com/public?command=returnChartData&currencyPair=%s&start=%d&end=%d&period=%d"
        url = base_url % (ticker, start_sc, end_sc, period)
        df = pd.read_json(url)
    elif exchange == "bitfx":
        base_url = "https://api.bitfinex.com/v2/candles/trade:%s:%s/hist?start=%d&end=%d"
        limit = 120
        period_sc = Time2Seconds[period]
        step = period_sc * limit
        ends_sc = np.arange(end_sc, start_sc, -step)
        dfs = []
        for _end_sc in tqdm(ends_sc):
            _start_sc = max(start_sc, _end_sc - step)
            url = base_url % (period, ticker, int(_start_sc * 1000), int(_end_sc * 1000))
            while True:
                try:
                    df = pd.read_json(url)
                    break
                except Exception as e:
                    print(e)
                    if int(e.status) == 429:
                        print('hit rate limit, sleeping for a minute...')
                        sleep(60)
            if len(df) == 0:
                break
            else:
                df = _preprocess_bitfx(df)
                dfs.append(df)
                # You can hit ~ 20 time each minute
                sleep(3)
        if dfs:
            df = pd.concat(dfs)
        else:
            df = pd.DataFrame(dfs)
    elif exchange == "kraken":
        base_url = "https://api.kraken.com/0/public/OHLC?pair=%s&interval=%d&since=%s"
        url = base_url % (ticker, period, start_sc)
        while True:
            try:
                res = urlopen(url)
                res = json.loads(res.read())
                data = res["result"][ticker]
                break
            except Exception as e:
                print(e)
                print(res)
                if res["error"][0] == 'EService:Unavailable':
                    print('Failed! Try again')
                    sleep(6)
        df = _preprocess_kraken(data)
        _start_sc = data[0][0]
        period_sc = period * 60
        if start_sc <= _start_sc - period_sc and ticker in symbol_kraken2polo:
            _start_sc -= 1
            base_url = "https://poloniex.com/public?command=returnChartData&currencyPair=%s&start=%d&end=%d&period=%d"
            _ticker = symbol_kraken2polo[ticker]
            url = base_url % (_ticker, start_sc, _start_sc, period_sc)
            polo_df = pd.read_json(url)
            # Price
            ohlc_df = df[["open", "high", "low", "close"]]
            polo_ohlc_df = polo_df[["open", "high", "low", "close"]]
            price_ratio = ohlc_df["open"].values[0] / polo_ohlc_df["close"].values[-1]
            polo_ohlc_df *= price_ratio
            ohlc_df = pd.concat([polo_ohlc_df, ohlc_df])
            # Volume
            volume_df = df[["volume"]]
            polo_volume_df = polo_df[["volume"]]
            volume_ratio = volume_df.values[0][0] / polo_volume_df.values[-1][0]
            polo_volume_df *= volume_ratio
            volume_df = pd.concat([polo_volume_df, volume_df])
            # Date
            date_df = pd.concat([polo_df[["date"]], df[["date"]]])
            df = pd.concat([date_df, ohlc_df, volume_df], axis=1)
            df = df.reset_index()
    elif exchange == "stock":
        url = "https://www.quandl.com/api/v3/datasets/%s/data.json?api_key=%s" % (ticker, QUANDL_APIKEY)
        if start is None:
            start = date2daily(start)
            url += "start_date=%s" % start
        if end is None:
            end = date2daily(end)
            url += "start_date=%s" % end
        res = urlopen(url)
        res = json.loads(res.read())
        cols = res['dataset_data']['column_names']
        data = res['dataset_data']['data']
        data_dict = defaultdict(list)
        for x in data:
            for i, col in enumerate(cols):
                if col in stock_columns_map:
                    col = stock_columns_map[col]
                data_dict[col].append(x[i])
        df = pd.DataFrame(data_dict)
    else:
        raise NotImplementedError()
    return df


def _preprocess_bitfx(df):
    date = [seconds2datetime(x / 1000) for x in df[0].values]
    df_dict = dict(date=date,
                   open=df[1].values,
                   close=df[2].values,
                   high=df[3].values,
                   low=df[4].values,
                   volume=df[5].values)
    df = pd.DataFrame(df_dict)
    return df


def _preprocess_kraken(data):
    columns = ["date", "open", "high", "low", "close",
               "vwap", "volume", "count"]
    new_data = defaultdict(list)
    data = deepcopy(data)
    for x in data:
        for i, col in enumerate(columns):
            if i == 0:
                x[i] = seconds2datetime(x[i])
            else:
                x[i] = float(x[i])
            new_data[col].append(x[i])
    df = pd.DataFrame(new_data)
    return df


def get_symbols(exchange="polo", APIKEY=None):
    """Get symbols traded on each exchange

    Parameters
    ----------
    exchange: str, (default 'polo')
        The name of exchange
    APIKEY: str, optional
        Need to use quandl API

    Returns
    -------
    List(str): The list of symbols
    """

    if exchange == "polo":
        url = "https://poloniex.com/public?command=returnTicker"
        df = pd.read_json(url)
        return list(df.columns)
    elif exchange == "stock":
        url = "https://www.quandl.com/api/v3/databases/WIKI/codes.json?api_key=%s" % APIKEY
        res = urlopen(url)
        zipfile = ZipFile(BytesIO(res.read()))
        zipfile.extract(zipfile.namelist()[0])
        df = pd.read_csv(zipfile.namelist()[0], header=None)
        return df[0].values
    else:
        raise NotImplementedError()


def get_info_SP500():
    wiki_url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    html = urlopen(wiki_url)
    bsobj = BeautifulSoup(html, 'lxml')
    table = bsobj.findAll('tbody')[0].findAll('tr')
    info = defaultdict(list)
    columns = [x.get_text() for x in table[0].findAll('th')]
    for row in table[1:]:
        row = [x.get_text() for x in row.findAll('td')]
        for i, col in enumerate(columns):
            info[col].append(row[i])
    return pd.DataFrame(info)