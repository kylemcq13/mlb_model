# mlb_model

This project was influenced by this Fangraphs Community Research Post written by Cam Rogers- https://community.fangraphs.com/using-clustering-to-generate-bullpen-matchups/

Check out the app here --> https://bullpen-matchup-model.herokuapp.com/

This model uses a hitter's name and opposing team to return the best options for pitchers out of the opposing team's bullpen. The model can be broken down to 3 parts - data collection, cluster modeling, and a hitting quality model that predicts change in run expectancy based on launch angle and exit velocity.

## Data Collection 

A postgresql database was set up locally to store the data. Three python scripts were written to collect and tabularize the data for model use - adv_hitting.py, pitching.py, and statcast.py. These scripts are automated to run once per week to retrieve updated data throughout the MLB season. Each python script generates a pandas dataframe which is then sent stored in a local postgresql database. The data collected includes statcast, advanced hitting and advanced pitching statistics from fangraphs.com. pyBaseball was utilized to collect the data needed for this model. 

The main driver of the bullpen matchup model is the Statcast data which includes pitch by pitch statistics like velocity of the pitch, it's location, and even finer details such as spin axis and exit velocity off the bat. The statcast data collected includes all pitches from the 2016-2021 seasons. 

The advanced pitching and hitting statistics tables are collected weekly and include advanced stats such as wOBA and ISO at that particular point in the season. 

<img src="https://github.com/kylemcq13/mlb_model/blob/main/Sandbox/bp_matchup_arch.PNG" alt="High Level Data Arch." width="500" height="700">

## Cluster Modeling

The first piece of the model clusters pitches based on the following variables: release speed, spin axis, spin rate, pitch location, horizontal movement, and vertical movement. Pitches were bucketed based on pitcher handedness and pitch type and then clustered using Kmeans clusters. Using the elbow method, optimal k was chosen for clustering of each bucket. 

## Hitting Quality Model

A Random Forest Regressor that uses exit velocity and launch angle to predict change in run expectancy value. The output of this model rewards high quality contact as defined by exit velocity and launch angle. 

## Matchup Score

The matchup score combines the clustering data with the change in run expectancy data by multiplying the subset of pitches by the change in run expectancy score. For example, if a particular batter has a run expectancy score of 1 for Cluster 1, 2 for Cluster 2 and -3 for Cluster 3 and an opposing pitcher throws 20% of his pitches from Cluster 1, 50% from Cluster 2 and 30% from Cluster 3 then:

*0.2(1) + 0.5(2) + 0.3(-3)*

The matchup score then ultimately recommends the pitcher from the available options in the opposing teams' bullpen. 

## Recommender

Let's say the Detroit Tigers wanted bullpen matchup recommendations when facing Yoan Moncada. 

```
bp_reco('Moncada, Yoan', 'DET', bp_reco_df)
```
Below would be the recommendations.

<img src="https://github.com/kylemcq13/mlb_model/blob/main/Sandbox/yoyo_results.PNG" alt="Yoyo vs Tigers result" width="500" height="300">
