# mlb_model

This project was influenced by this Fangraphs Community Research Post - 

Check out the app here --> https://bullpen-matchup-model.herokuapp.com/

This model uses a hitter's name and opposing team to return the best options for pitchers out of the bullpen. The model can be broken down to 3 parts - data collection, cluster modeling, and a hitting quality model.

## Data Collection 

A postgresql database was set up locally store the data. Three python scripts were written to collect and tabularize the data for model use - adv_hitting.py, pitching.py, and statcast.py. These were run once per week to collect fresh data throughout the MLB season. Each python script generates a pandas dataframe which is then sent to a local postgresql database. The data collected includes statcast, advanced hitting and advanced pitching statistics from fangraphs.com. pyBaseball was utilized to collect the data needed for this model. 

The main driver of the bullpen matchup model is the Statcast data which includes pitch by pitch statistics like velocity of the pitch, it's location, and even finer details such as spin axis and exit velocity. The statcast data collected includes all pitches from the 2016-2021 seasons. 

The advanced pitching and hitting statistics tables are collected weekly and include advanced stats such as wOBA and ISO at that particular point in the season. 

<img src="https://github.com/kylemcq13/mlb_model/blob/main/Sandbox/bp_matchup_arch.PNG" alt="High Level Data Arch." width="500" height="700">

## Cluster Modeling

The first piece of the model clusters pitches based on the following variables: release speed, spin axis, spin rate, pitch location, horizontal movement, vertical movement. Pitches were bucketed based on pitcher handedness and pitch type and then clustered using Kmeans clusters. Using the elbow method, optimal k was chosen for clustering each bucket. 

## Change in Run Expectancy Model

A Random Forest Regressor that uses exit velocity and launch angle to predict change in run expectancy value. This model rewards high quality contact as defined by exit velocity and launch angle. 

## Matchup Score

The matchup score combines the clustering data with the change in run expectancy data by multiplying the subset of pitches by the change in run expectancy score. 

