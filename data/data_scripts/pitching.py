from datetime import date
from datetime import datetime
from configparser import ConfigParser
import pandas as pd
from pybaseball import pitching_stats
from sqlalchemy import create_engine
from datetime import date

# establish sql engine connection
parser = ConfigParser()
parser.read('nb.ini')
conn_string = parser.get('my_db', 'conn_string')
engine = create_engine(conn_string)

# set opening day date and current year
current_year = datetime.now().year

# scrape advanced hitting stats
pitching = pitching_stats(current_year, qual=1)
pitching['date_pull'] = date.today() 

# remove special characters from column names for postgresql requirements
pitching.columns = pitching.columns.str.replace('%', 'pct')
pitching.columns = pitching.columns.str.replace(r'[()]', '', regex=True)

# export to sql database
pitching.to_sql('pitching', engine, if_exists='append', 
               chunksize= 100, method='multi')