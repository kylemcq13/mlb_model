import pandas as pd
import numpy as np
import pickle
from datetime import date
from configparser import ConfigParser
from sqlalchemy import create_engine
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.model_selection import GridSearchCV

# consider training model on years' previous data, scoring on current season

# establish sql engine connection
parser = ConfigParser()
parser.read('nb.ini')
conn_string = parser.get('my_db', 'conn_string')
engine = create_engine(conn_string)

sql1 = '''
    SELECT 
        "game_date", "player_name", "pitcher", 
        "pitcher_team", "batter", "description", 
        "launch_speed", "launch_angle", "delta_run_exp", 
        "cluster_name"
    FROM clustering
    WHERE
        "description" = 'hit_into_play' AND 
        "game_date" < '2020-12-31' AND random()<0.1
'''
df = pd.read_sql_query(sql1, engine)

# create object for today's date
today = str(date.today())

# save training set to sql database
print('Saving training data')
df['create_date'] = date.today()
df.to_sql('training_df', engine, if_exists='replace', 
          chunksize=500, method='multi')

# split the data
X, y = df[['launch_speed', 'launch_angle']], df['delta_run_exp']

# create train and test sets
X_train, X_test, y_train, y_test = train_test_split(
    X, y, random_state=13, test_size=0.3
)

# bring pipelines together for modeling
rf_reg = Pipeline(steps=[('scaler', StandardScaler()),
                         ('regressor', RandomForestRegressor())])

param_dist = { 
          'regressor__n_estimators': [100, 200, 500],
          'regressor__max_depth': [None, 5, 8]
}

# Hyperparameter tuning
search = GridSearchCV(rf_reg, param_dist, 
                      n_jobs=-1, scoring='neg_root_mean_squared_error')
print('Training model...')
search.fit(X_train, y_train)
search.best_params_

# predict on the test set
y_pred = search.best_estimator_.predict(X_test)

# error scores
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
print('rmse: ', rmse)

r2 = r2_score(y_test, y_pred)
print('r2: ', r2)

mae = mean_absolute_error(y_test, y_pred)
print('mae: ', mae)

# Dump the trained model with pkl
final_model_pkl_filename = 'run_exp_model_{}.pkl'.format(today)

# Open the file to save as pkl file
final_model_pkl = open(final_model_pkl_filename, 'wb')
pickle.dump(search.best_estimator_, final_model_pkl)

# Close the pickle instances
final_model_pkl.close()

print('Done')
