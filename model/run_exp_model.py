import pandas as pd
import numpy as np
from configparser import ConfigParser
from sqlalchemy import create_engine
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.model_selection import GridSearchCV


# establish sql engine connection
parser = ConfigParser()
parser.read('nb.ini')
conn_string = parser.get('my_db', 'conn_string')
engine = create_engine(conn_string)

sql1 = '''
    SELECT *
    FROM clustering
'''
df = pd.read_sql_query(sql1, engine)

# non ball in play outcomes
non_bip = df.loc[df['description']!='hit_into_play']

# calculate average delta run expectancy by outcome
non_bip['e_delta_re'] = non_bip.groupby('description')['delta_run_exp'].transform('mean')

# ball in play outcomes
bip = df.loc[df['description']=='hit_into_play']

# sample 10k records for training set
bip_10k = bip.sample(n=10000, random_state=1)

# split the data
X, y = bip_10k[['launch_speed', 'launch_angle']], bip_10k['delta_run_exp']

# create train and test sets
X_train, X_test, y_train, y_test = train_test_split(
    X, y, random_state=13, test_size=0.3
)

# bring pipelines together for modeling
rf_reg = Pipeline(steps=[('scaler', StandardScaler()),
                        ('regressor', RandomForestRegressor())])

param_dist = { 
          'regressor__n_estimators': [100, 200, 500],
          'regressor__max_depth':[None, 5, 8]
}

# Hyperparameter tuning
search = GridSearchCV(rf_reg, 
param_dist, n_jobs=-1, scoring='neg_root_mean_squared_error')
search.fit(X_train, y_train)
search.best_params_

y_pred = search.best_estimator_.predict(X_test)

# error scores
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
print('rmse: ', rmse)

r2 = r2_score(y_test, y_pred)
print('r2: ', r2)

mae = mean_absolute_error(y_test, y_pred)
print('mae: ', mae)

# predict change in run expectancy with launch_speed and angle
bip['e_delta_re'] = search.best_estimator_.predict(bip[['launch_speed','launch_angle']])

# fill in dataframe with ball in play and non ball in play
frames = [bip, non_bip]
df_concat = pd.concat(frames)

# find average e delta re score per batter per cluster
df_concat['clust_e_delta_re_mean'] = df_concat.groupby(['batter', 'cluster_name'])['e_delta_re'].transform('mean')

# breakdown pitches thrown per cluster per pitcher
df_concat_2 = df_concat.groupby(['pitcher', 'cluster_name']).size().unstack(fill_value=0).reset_index()

cols = ['lhp_cukc_0', 'lhp_cukc_1', 'lhp_cukc_2', 'lhp_cukc_3',
        'lhp_ff_0', 'lhp_ff_1', 'lhp_ff_2', 'lhp_ff_3',
        'lhp_mf_0', 'lhp_mf_1', 'lhp_mf_2', 'lhp_mf_3',
        'lhp_off_0', 'lhp_off_1', 'lhp_off_2', 'lhp_off_3',
        'lhp_slct_0', 'lhp_slct_1', 'lhp_slct_2', 'lhp_slct_3',
        'rhp_cukc_0', 'rhp_cukc_1', 'rhp_cukc_2', 'rhp_cukc_3', 'rhp_cukc_4',
        'rhp_ff_0', 'rhp_ff_1', 'rhp_ff_2', 'rhp_ff_3',
        'rhp_mf_0', 'rhp_mf_1', 'rhp_mf_2', 'rhp_mf_3', 'rhp_mf_4',
        'rhp_off_0', 'rhp_off_1', 'rhp_off_2', 'rhp_off_3',
        'rhp_slct_0', 'rhp_slct_1', 'rhp_slct_2', 'rhp_slct_3']

df_concat_2[cols] = df_concat_2[cols].div(df_concat_2[cols].sum(axis=1), axis=0)

cluster_sum = df_concat_2.melt(id_vars=["pitcher"], var_name="cluster_name_pitcher", value_name="value")

cluster_sum = cluster_sum[cluster_sum.value != 0]

df2 = df_concat[['batter', 'pitcher', 'pitcher_team', 'game_date', 'cluster_name', 'clust_e_delta_re_mean']].merge(cluster_sum, left_on=['pitcher', 'cluster_name'], right_on=['pitcher', 'cluster_name_pitcher'])
df2['score'] = df2['value'] * df2['clust_e_delta_re_mean']
df2['matchup_score'] = df2.groupby(['batter', 'pitcher'])['score'].transform('sum')

sql1 = '''
    SELECT *
    FROM player_lookup
'''
player_lookup = pd.read_sql_query(sql1, engine)

sql_pitching = '''
    SELECT distinct("IDfg"), max("G") as G, max("GS") as GS
    FROM pitching
    GROUP BY "IDfg", "Team"
'''

pitching = pd.read_sql_query(sql_pitching, engine)

sql_hitting = '''
    SELECT distinct("IDfg")
    FROM hitting  
'''

hitting = pd.read_sql_query(sql_hitting, engine)

player_lookup = player_lookup[['name_last', 'name_first', 'key_mlbam', 'key_fangraphs']]

df3 = df2.merge(player_lookup, how='left', left_on = 'pitcher', right_on = 'key_mlbam')

df3['pitcher_name'] = df3['name_last'] + ', ' + df3['name_first']

df3 = df3.merge(player_lookup, how='left', left_on='batter', right_on='key_mlbam')

df3['batter_name'] = df3['name_last_y'] + ', ' + df3['name_first_y']

df3 = df3.drop(columns=['name_last_x', 'name_first_x', 'name_last_y', 'name_first_y'])

df3 = df3.merge(pitching, how='left', left_on='key_fangraphs_x', right_on='IDfg')

df3 = df3.merge(hitting, how='left', left_on='key_fangraphs_y', right_on='IDfg')

df3['isStarter'] = ((df3['gs'] / df3['g']) > 0.8)

df3 = df3.dropna(subset=['g', 'gs'])

pitcher_df = df3[['pitcher_name', 'pitcher_team', 'game_date']].sort_values('game_date').groupby('pitcher_name').tail(1)
pitcher_df_2021 = pitcher_df.loc[pitcher_df['game_date']>'2021-01-01']

df3_2021 = df3.loc[df3['game_date']>'2021-03-01']
df3_2021_reco = df3_2021[['batter_name', 'pitcher_name', 'pitcher_team', 'matchup_score', 'isStarter']].merge(pitcher_df_2021, on='pitcher_name', how='inner').drop(columns=['pitcher_team_x', 'game_date']).rename(columns = {'pitcher_team_y':'pitcher_team'}).drop_duplicates()

df3_2021_reco.to_sql('bp_reco_df', engine, if_exists='replace', 
               chunksize= 100, method='multi')