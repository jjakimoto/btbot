import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .config import URL
from .sql_declarative import Price30M, Base
from .utils import date2datetime


def fetch_data(start, end, tickers):
    engine = create_engine(URL)
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    start = date2datetime(start)
    base_query = session.query(Price30M).filter(Price30M.date > start)
    if end is not None:
        end = date2datetime(end)
        base_query = base_query.filter(Price30M.date <= end)
    data = {}
    for ticker in tickers:
        x = base_query.filter(Price30M.ticker == ticker).all()
        timeidx = [x_i.date for x_i in x]
        dict_val = dict(
            open=[x_i.open for x_i in x],
            high=[x_i.high for x_i in x],
            low=[x_i.low for x_i in x],
            close=[x_i.close for x_i in x],
            volume=[x_i.volume for x_i in x])
        df = pd.DataFrame(dict_val, index=timeidx)
        df = df.loc[~df.index.duplicated(keep='first')]
        df.sort_index(inplace=True)
        data[ticker] = df
    return data
