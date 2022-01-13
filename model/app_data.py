import pandas as pd
from configparser import ConfigParser
from sqlalchemy import create_engine
import utils

# establish sql engine connection
parser = ConfigParser()
parser.read('nb.ini')
conn_string = parser.get('my_db', 'conn_string')
engine = create_engine(conn_string)

# import tables
sql1 = '''
    SELECT 
        "game_date", "player_name", "pitcher", 
        "pitcher_team", "batter", "description", 
        "launch_speed", "launch_angle", "delta_run_exp", 
        "cluster_name"
    FROM clustering
    WHERE "description"!='hit_into_play'
'''
print('Importing non ball in play dataset')
non_bip = pd.read_sql_query(sql1, engine)

sql2 = '''
    SELECT *
    FROM run_exp_scoring_set
'''
print('Importing run_exp_scoring dataset')
scored_df = pd.read_sql_query(sql2, engine)

sql3 = '''
    SELECT *
    FROM player_lookup
'''
print("Importing player lookup")
player_lookup = pd.read_sql_query(sql3, engine)

sql4 = '''
    SELECT distinct("IDfg"), max("G") as G, max("GS") as GS
    FROM pitching
    GROUP BY "IDfg", "Team"
'''
print("Import pitching")
pitching = pd.read_sql_query(sql4, engine)

sql5 = '''
    SELECT distinct("IDfg")
    FROM hitting  
'''
print("Importing hitting")
hitting = pd.read_sql_query(sql5, engine)

frames = [scored_df, non_bip]
df_concat = pd.concat(frames)

# get average scores per batter per cluster faced
df_concat['clust_e_delta_re_mean'] = (
    df_concat.groupby(['batter', 'cluster_name'])
    ['e_delta_re'].transform('mean')
)

# obtain pitcher cluster distributions
df_concat_2 = (
    df_concat.groupby(['pitcher', 'cluster_name'])
    .size().unstack(fill_value=0).reset_index()
)
cluster_cols = df_concat_2.iloc[:, 1:]
cols = cluster_cols.columns

df_concat_2[cols] = (
    df_concat_2[cols].div(df_concat_2[cols]
                          .sum(axis=1), axis=0)
)

# retrieve distribution percentages for each pitcher
cluster_sum = (
    df_concat_2.melt(id_vars=["pitcher"],
                     var_name="cluster_name_pitcher",
                     value_name="value")
)
cluster_sum = cluster_sum[cluster_sum.value != 0]

# merge df's back together
df2 = (
    df_concat[['batter', 'pitcher', 'pitcher_team', 
               'game_date', 'cluster_name', 'clust_e_delta_re_mean']]
    .merge(cluster_sum, left_on=['pitcher', 'cluster_name'],
           right_on=['pitcher', 'cluster_name_pitcher'])
)

# calculate scores
df2['score'] = df2['value'] * df2['clust_e_delta_re_mean']
df2['matchup_score'] = (
    df2.groupby(['batter', 'pitcher'])['score']
       .transform('sum')
)

# apply player_id function
df3 = (
    utils.player_id(
        df=df2, player_lookup=player_lookup, 
        pitching=pitching, hitting=hitting)
)
df3['game_date'] = pd.to_datetime(df3['game_date'])

# create pitcher dataframe for 2021 pitchers only
pitcher_df = (
    df3[['pitcher_name', 'pitcher_team', 'game_date']]
    .sort_values('game_date')
    .groupby('pitcher_name')
    .tail(1)
)

# create final dataset
df3_2021_reco = (
    df3[['batter_name', 'pitcher_name', 'pitcher_team', 
         'matchup_score', 'isStarter']]
    .merge(pitcher_df, on='pitcher_name', how='inner')
    .drop(columns=['pitcher_team_x', 'game_date'])
    .rename(columns={'pitcher_team_y': 'pitcher_team'})
    .drop_duplicates()
)

# save to sql database
print('saving to sql')
df3_2021_reco.to_sql('bp_reco_df', engine, if_exists='replace',
                     chunksize=500, method='multi')