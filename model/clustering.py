import pandas as pd
import numpy as np
from datetime import date
from datetime import datetime
from configparser import ConfigParser
from sqlalchemy import create_engine
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import struct
import sys

version = struct.calcsize("P")*8 

print(version)
print(sys.version)

# establish sql engine connection
parser = ConfigParser()
parser.read('nb.ini')
conn_string = parser.get('my_db', 'conn_string')
engine = create_engine(conn_string)

# fetch statcast data from postgresql database

sql1 = '''
        SELECT "player_name", "home_team", "away_team", "inning_topbot", "p_throws", "pitch_type", "game_date", "events", "pitcher", 
         "batter", "description", "launch_speed", "launch_angle", "release_speed", "release_spin_rate", "pfx_x", "pfx_z", 
         "plate_x", "plate_z", "effective_speed", "pitch_name", "spin_axis", "delta_run_exp"
        FROM statcast_2016
    '''
print('Importing 2016 data')
sc_16 = pd.read_sql_query(sql1, engine)

sql2 = '''
        SELECT "player_name", "home_team", "away_team", "inning_topbot", "p_throws", "pitch_type", "game_date", "events", "pitcher", 
         "batter", "description", "launch_speed", "launch_angle", "release_speed", "release_spin_rate", "pfx_x", "pfx_z", 
         "plate_x", "plate_z", "effective_speed", "pitch_name", "spin_axis", "delta_run_exp"
        FROM statcast_2017
    '''
print('Importing 2017 data')
sc_17 = pd.read_sql_query(sql2, engine)

sql3 = '''
        SELECT "player_name", "home_team", "away_team", "inning_topbot", "p_throws", "pitch_type", "game_date", "events", "pitcher", 
         "batter", "description", "launch_speed", "launch_angle", "release_speed", "release_spin_rate", "pfx_x", "pfx_z", 
         "plate_x", "plate_z", "effective_speed", "pitch_name", "spin_axis", "delta_run_exp"
        FROM statcast_2018
    '''
print('Importing 2018 data')
sc_18 = pd.read_sql_query(sql3, engine)

sql4 = '''
        SELECT "player_name", "home_team", "away_team", "inning_topbot", "p_throws", "pitch_type", "game_date", "events", "pitcher", 
         "batter", "description", "launch_speed", "launch_angle", "release_speed", "release_spin_rate", "pfx_x", "pfx_z", 
         "plate_x", "plate_z", "effective_speed", "pitch_name", "spin_axis", "delta_run_exp"
        FROM statcast_2019
    '''
print('Importing 2019 data')
sc_19 = pd.read_sql_query(sql4, engine)

sql5 = '''
        SELECT "player_name", "home_team", "away_team", "inning_topbot", "p_throws", "pitch_type", "game_date", "events", "pitcher", 
         "batter", "description", "launch_speed", "launch_angle", "release_speed", "release_spin_rate", "pfx_x", "pfx_z", 
         "plate_x", "plate_z", "effective_speed", "pitch_name", "spin_axis", "delta_run_exp"
        FROM statcast_2020
    '''
print('Importing 2020 data')
sc_20 = pd.read_sql_query(sql5, engine)

sql6 = '''
        SELECT "player_name", "home_team", "away_team", "inning_topbot", "p_throws", "pitch_type", "game_date", "events", "pitcher", 
         "batter", "description", "launch_speed", "launch_angle", "release_speed", "release_spin_rate", "pfx_x", "pfx_z", 
         "plate_x", "plate_z", "effective_speed", "pitch_name", "spin_axis", "delta_run_exp"
        FROM statcast_2021
    '''
print('Importing 2021 data')
sc_21 = pd.read_sql_query(sql6, engine)

statcast = pd.concat([sc_16, sc_17, sc_18, sc_19, sc_20, sc_21])

# fill nulls
statcast['events']=statcast['events'].fillna('none')
statcast['launch_speed']=statcast['launch_speed'].fillna(0)
statcast['launch_angle']=statcast['launch_angle'].fillna(0)

# relevant columns
# cols = ['player_name', 'home_team', 'away_team', 'inning_topbot', 'p_throws', 'pitch_type', 'game_date', 'events', 'pitcher', 
#          'batter', 'description', 'launch_speed', 'launch_angle', 'release_speed', 'release_spin_rate', 'release_extension', 'pfx_x', 'pfx_z', 
#          'plate_x', 'plate_z', 'pitch_name', 'spin_axis', 'delta_run_exp']

sc_cluster = statcast

# assign pitcher teams
def pitcher_team(row):

	if row['inning_topbot'] == 'Top':
		return row['home_team']
	
	if row['inning_topbot'] == 'Bot':
		return row['away_team']

sc_cluster['pitcher_team'] = sc_cluster.apply(pitcher_team, axis=1)

# Fastballs and Four Seam Fastballs are the same thing
# Group pitches into similar moving pitches: Fastballs, Moving Fastballs, Slider/Cutter, Curve and Off Speed

sc_cluster['pitch_type'] = sc_cluster['pitch_type'].replace(['FA'],'FF')

# categorize the pitches according to pitcher handedness and pitch type

conditions = [
    ((sc_cluster['p_throws'] == 'R') & (sc_cluster['pitch_type'] == 'FF')),
    ((sc_cluster['p_throws'] == 'R') & (sc_cluster['pitch_type'] == 'FT') | (sc_cluster['p_throws']=='R') & (sc_cluster['pitch_type']=='SI')),
    ((sc_cluster['p_throws'] == 'R') & (sc_cluster['pitch_type'] == 'SL') | (sc_cluster['p_throws']=='R') & (sc_cluster['pitch_type']=='FC')),
    ((sc_cluster['p_throws'] == 'R') & (sc_cluster['pitch_type'] == 'CU') | (sc_cluster['p_throws']=='R') & (sc_cluster['pitch_type']=='KC')),
    ((sc_cluster['p_throws'] == 'R') & (sc_cluster['pitch_type'] == 'CH') | (sc_cluster['p_throws']=='R') & (sc_cluster['pitch_type']=='FS')),
    ((sc_cluster['p_throws'] == 'L') & (sc_cluster['pitch_type'] == 'FF')),
    ((sc_cluster['p_throws'] == 'L') & (sc_cluster['pitch_type'] == 'FT') | (sc_cluster['p_throws']=='L') & (sc_cluster['pitch_type']=='SI')),
    ((sc_cluster['p_throws'] == 'L') & (sc_cluster['pitch_type'] == 'SL') | (sc_cluster['p_throws']=='L') & (sc_cluster['pitch_type']=='FC')),
    ((sc_cluster['p_throws'] == 'L') & (sc_cluster['pitch_type'] == 'CU') | (sc_cluster['p_throws']=='L') & (sc_cluster['pitch_type']=='KC')),
    ((sc_cluster['p_throws'] == 'L') & (sc_cluster['pitch_type'] == 'CH') | (sc_cluster['p_throws']=='L') & (sc_cluster['pitch_type']=='FS'))
    ]

values = ['rhp_ff', 'rhp_mf', 'rhp_slct', 'rhp_cukc', 'rhp_off', 'lhp_ff', 'lhp_mf', 'lhp_slct', 'lhp_cukc', 'lhp_off']

sc_cluster['cat'] = np.select(conditions, values)

# define scaler object
scaler = StandardScaler()

# creating a copy to keep original df as is for later
df_clust = sc_cluster.copy()

cols_scale = [
    'release_speed', 'release_spin_rate', 'pfx_x', 'pfx_z', 'spin_axis', 'plate_x', 'plate_z']

# scale the data
scaler = StandardScaler().fit(df_clust[cols_scale])
df_clust[cols_scale] = scaler.transform(df_clust[cols_scale])

rhp_ff = df_clust.loc[df_clust['cat']=='rhp_ff'].dropna()
rhp_slct = df_clust.loc[df_clust['cat']=='rhp_slct'].dropna()
rhp_off = df_clust.loc[df_clust['cat']=='rhp_off'].dropna()
lhp_ff = df_clust.loc[df_clust['cat']=='lhp_ff'].dropna()
lhp_mf = df_clust.loc[df_clust['cat']=='lhp_mf'].dropna()
lhp_slct = df_clust.loc[df_clust['cat']=='lhp_slct'].dropna()
lhp_cukc = df_clust.loc[df_clust['cat']=='lhp_cukc'].dropna()
lhp_off = df_clust.loc[df_clust['cat']=='lhp_off'].dropna()


df_list = [rhp_ff, rhp_slct, rhp_off, lhp_ff, lhp_mf, lhp_slct, lhp_cukc, lhp_off]

print('clustering data')
for df in df_list:
    kmeanModel = KMeans(n_clusters=4)
    kmeanModel.fit(df[cols_scale])
    df['cluster_id'] = kmeanModel.labels_
    df['cluster_id'] = df['cluster_id'].astype('str')
    df['cluster_name'] = df['cat'] + '_' + df['cluster_id']

rhp_mf = df_clust.loc[df_clust['cat']=='rhp_mf'].dropna()
rhp_cukc = df_clust.loc[df_clust['cat']=='rhp_cukc'].dropna()

df_list2 = [rhp_mf, rhp_cukc]

for df in df_list2:
    kmeanModel = KMeans(n_clusters=5)
    kmeanModel.fit(df[cols_scale])
    df['cluster_id'] = kmeanModel.labels_
    df['cluster_id'] = df['cluster_id'].astype('str')
    df['cluster_name'] = df['cat'] + '_' + df['cluster_id']

frames = [rhp_mf, rhp_cukc, rhp_ff, rhp_slct, rhp_off, lhp_ff, lhp_mf, lhp_slct, lhp_cukc, lhp_off]

df_concat = pd.concat(frames)

df_concat['create_date'] = date.today()

print('saving to sql')
df_concat.to_sql('clustering', engine, if_exists='replace', chunksize=1000,
                 method='multi')