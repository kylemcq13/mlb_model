import pandas


def player_id(df, player_lookup, pitching, hitting):

    # create player lookup table
    player_lookup_df = (
        player_lookup[['name_last', 'name_first', 
                       'key_mlbam', 'key_fangraphs']]
    )

    # set up pitcher names
    df3 = df.merge(player_lookup_df, how='left', 
                   left_on='pitcher', right_on='key_mlbam')
    df3['pitcher_name'] = df3['name_last'] + ', ' + df3['name_first']

    # set up hitter names
    df3 = df3.merge(player_lookup, how='left', 
                    left_on='batter', right_on='key_mlbam')
    df3['batter_name'] = df3['name_last_y'] + ', ' + df3['name_first_y']

    # drop unneeded columns
    df3 = (
        df3.drop(columns=['name_last_x', 'name_first_x', 
                          'name_last_y', 'name_first_y'])
    )

    # merge on fangraphs keys
    df3 = df3.merge(pitching, how='left', 
                    left_on='key_fangraphs_x', right_on='IDfg')
    df3 = df3.merge(hitting, how='left', 
                    left_on='key_fangraphs_y', right_on='IDfg')

    # identify starting vs relief pitchers
    df3['isStarter'] = ((df3['gs'] / df3['g']) > 0.8)

    # drop columns from starter vs reliever calc
    df3 = df3.dropna(subset=['g', 'gs'])

    return df3
    