from datetime import date
from datetime import datetime
from configparser import ConfigParser
from pybaseball import batting_stats
from sqlalchemy import create_engine


# establish sql engine connection
parser = ConfigParser()
parser.read('nb.ini')
conn_string = parser.get('my_db', 'conn_string')
engine = create_engine(conn_string)

# set opening day date and current year
current_year = datetime.now().year

# scrape advanced hitting stats
hitting = batting_stats(current_year, current_year, qual=1)
hitting['date_pull'] = date.today() 

# remove special characters from column names for postgresql requirements
hitting.columns = hitting.columns.str.replace('%', 'pct')
hitting.columns = hitting.columns.str.replace(r'[()]', '', regex=True)

# export to sql database
hitting.to_sql('hitting', engine, if_exists='append', 
               chunksize=100, method='multi')
