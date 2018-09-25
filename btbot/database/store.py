from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tqdm import tqdm
from time import sleep

from config import URL, QUANDL_URL
from sql_declarative import Price30M, Base, StockPriceDay
from utils import get_data, get_symbols


def store(session, ticker, date, open, high, low,
          close, volume, table, *args, **kwargs):
    """Store data into database

    Parameters
    ----------
    session: sql session object
    ticker: str
        Symbol
    date: '%Y-%m-%d %H:%M:%S'
    open, high, low, close, volume: float
    table: str
        The name of table
    """
    if table == "price30m":
        obj = Price30M(ticker=ticker, date=date, open=open, high=high,
                       low=low, close=close, volume=volume)
    else:
        obj = StockPriceDay(ticker=ticker, date=date, open=open, high=high,
                            low=low, close=close, volume=volume)
    session.add(obj)
    session.commit()


def store_df(ticker, df, table="price30m"):
    """Store DataFrame into database

    Parameters
    ----------
    ticker: str
        Symbol
    df: pd.DataFrame which contains open, high, low, close, volume
    table: str
        The name of table
    """
    # Establish connection
    if table == "stock_price_daily":
        engine = create_engine(QUANDL_URL)
    else:
        engine = create_engine(URL)
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    df_val = df.values
    for val in tqdm(df_val):
        data = dict(session=session, ticker=ticker)
        for i, col in enumerate(df.columns):
            data[col] = val[i]
        store(**data, table=table)
    session.close()


def update(ticker, end=None, period="30", exchange="polo"):
    """Update database

    Parameters
    ----------
    ticker: str
        Symbol
    end: '%Y-%m-%d %H:%M:%S'
        The most recent data in databases
    period: float or str
        The unit is second
    exchange: str
        The name of exchange
    """
    if end is None:
        end = "1970-01-01 00:00:00"
    df = get_data(ticker, start=end, end=None,
                  period=period, exchange=exchange)
    if exchange == "stock":
        table = "stock_price_daily"
    else:
        table = "price30m"
    store_df(ticker, df, table=table)


if __name__ == '__main__':
    pairs = get_symbols()
    for pair in tqdm(pairs):
        update(pair, period=1800, exchange="polo")
        sleep(3)
