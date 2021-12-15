import pandas as pd
from configparser import ConfigParser
from sqlalchemy import create_engine


# establish sql engine connection
parser = ConfigParser()
parser.read('nb.ini')
conn_string = parser.get('my_db', 'conn_string')
engine = create_engine(conn_string)

# fetch statcast data from postgresql database

sql1 = '''
        SELECT *
        FROM bp_reco_df
    '''
bp_reco_df = pd.read_sql_query(sql1, engine)

bp_reco_df.to_csv(r'D:/mlb_model/data/bp_reco_df.csv')