import flask
import pandas as pd
from flask import request
from configparser import ConfigParser
from sqlalchemy import create_engine
import sys

print(sys.version)



app = flask.Flask(__name__, template_folder='html_templates')

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

def bp_reco(batter, pitcher_tm, df):
    df_reco = df.loc[df['batter_name']==batter]
    df_reco_team = df_reco.loc[df_reco['pitcher_team']==pitcher_tm]

    return df_reco_team.sort_values(by=['matchup_score'])

# Set up the main route
@app.route('/', methods=['GET', 'POST'])

def main():
    if flask.request.method == 'GET':
        
        batter_nms = bp_reco_df['batter_name'].unique()
        pitcher_tms = bp_reco_df['pitcher_team'].unique()

        return (flask.render_template('index.html', batter_names=batter_nms, pitcher_teams=pitcher_tms))
    
    if flask.request.method == 'POST':
        # form = InputForm(request.form)

        batter_input = request.form.get("bn")
        team_input = request.form.get("pt")
        
        result_final = bp_reco(batter_input, team_input,
                                    bp_reco_df)
        pitcher_name = []
        matchup_score = []
        
        for i in range(len(result_final)):
            pitcher_name.append(result_final.iloc[i][2])
            matchup_score.append(result_final.iloc[i][3])

        return (flask.render_template(
                                 'positive.html', 
                                 pitcher=pitcher_name,
                                 score=matchup_score,
                                 search_name=batter_input))  

if __name__ == '__main__':
    app.run()