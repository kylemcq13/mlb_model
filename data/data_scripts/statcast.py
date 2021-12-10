from datetime import date
from datetime import datetime
from configparser import ConfigParser
import pandas as pd
import pybaseball
from pybaseball import statcast
from sqlalchemy import create_engine
from datetime import date

# establish sql engine connection
parser = ConfigParser()
parser.read('nb.ini')
conn_string = parser.get('my_db', 'conn_string')
engine = create_engine(conn_string)

# set opening day date and current year
current_year = datetime.now().year
today = str(date.today())
opening_day = '{}-03-31'.format(current_year)

# scrape statcast data
if __name__ == '__main__':

    pybaseball.cache.enable()
    statcast_data = statcast(opening_day, today)

    # export to sql database
    statcast_data.to_sql('statcast_{}'.format(current_year), engine, if_exists='replace', 
                        chunksize= 100, method='multi')
