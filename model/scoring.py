import pandas as pd
import numpy as np
import pickle
from datetime import date
from configparser import ConfigParser
from sqlalchemy import create_engine


# establish sql engine connection
parser = ConfigParser()
parser.read('nb.ini')
conn_string = parser.get('my_db', 'conn_string')
engine = create_engine(conn_string)

sql1 = '''
    SELECT "game_date", "player_name", "pitcher", "pitcher_team", "batter", "description", "launch_speed", "launch_angle", "delta_run_exp", "cluster_name"
    FROM clustering
    WHERE "description"='hit_into_play' AND "game_date" > '2020-12-31'
'''
print('Importing ball in play dataset')
scoring = pd.read_sql_query(sql1, engine)

# create object for today's date
today = str(date.today())

# Loading the saved decision tree model pickle
final_model_pkl_filename = 'run_exp_model_{}.pkl'.format(today)
final_model_pkl = open(final_model_pkl_filename, 'rb')
model = pickle.load(final_model_pkl)
print("Loaded saved model :: ", model)

# predict change in run expectancy with launch_speed and angle
scoring['e_delta_re'] = model.predict(scoring[['launch_speed','launch_angle']])

# save scoring dataframe to sql server
print('saving predictions to sql')
scoring.to_sql('run_exp_scoring_set', engine, if_exists='replace', 
               chunksize= 500, method='multi')

print('Done')
# End Script
