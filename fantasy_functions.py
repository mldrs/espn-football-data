import requests
from datetime import datetime
import pandas as pd
import json
#import awswrangler as wr

fantasy_base_endpoint = "https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/"

def get_fantasy_teams(league_id, season):
    url = fantasy_base_endpoint + str(season) + "/segments/0/leagues/" + str(league_id) + "?view=mTeam"
    r = requests.get(url, params={'seasonId':season})
    d = r.json()

    #print(d)
    data = []
    for team in d['teams']:
        team_id = team['id']
        team_abbrev = team['abbrev']
        team_loc = "Legacy" #team['location']
        team_nick = "Legacy" #team['nickname']
        team_fullName = team['name'] #team_loc + " " + team_nick
        team_logo = team['logo']
        data.append([
            team_id, team_abbrev, team_loc, team_nick, team_fullName, team_logo
        ])


    data = pd.DataFrame(data, columns=['ID', 'Abbreviation', 'Location', 'Nickname', 'Team Name', 'Logo URL'])

    data.to_csv('output/Fantasy-Team-Metadata.csv', index=False)
    #data.to_excel(output_path + 'Fantasy-Team-Metadata.xlsx')
    #print(data)

def get_fantasy_stats(league_id, season):
    #test_player_id = pd.read_excel('output/nfl/'+ str(season) + '/manual_input/Eligibility checks ' + str(season) + '.xlsx', sheet_name='Sheet1')
    #test_player_id = wr.s3.read_excel('s3://web.mldrs.nl/NFL/2024/Eligibility checks 2024.xlsx')
    #el_df = pd.DataFrame(test_player_id)
    #eligible = el_df[el_df.Checked == "V"]['ID'].values.tolist()

    p = []
    for week in range(0,18):
        url = fantasy_base_endpoint + str(season) + "/segments/0/leagues/" + str(league_id) + '?view=kona_player_info&scoringPeriodId=' + str(week)

        filters = {
            "players":{
                "limit": 1500,
                "sortDraftRanks": {
                    "sortPriority": 1,
                    "sortAsc": True,
                    "value": "STANDARD"
                }
            }
        }


        r_headers = {'x-fantasy-filter': json.dumps(filters)}
        r = requests.get(url, headers=r_headers)
        d = r.json()

        #for local debugging
        #dbg = json.dumps(d)
        #with open("players.json", "w") as outfile:
        #    outfile.write(dbg)

        for player in d['players']:
            id = player.get('id')
            if 1==1:
            #if id in [4430191, 4569618]:
                #print(id)
                fteam = player.get('onTeamId')
                player_data = player.get('player')
                fullName = player_data.get('fullName')
                jersey = player_data.get('jersey')
                proTeam = player_data.get('proTeamId')
                for stattype in player_data.get('stats'):
                    statSeasonId = stattype.get('seasonId')
                    statSplitTypeId = stattype.get('statSplitTypeId')
                    statScoringPeriodId = stattype.get('scoringPeriodId')
                    if statSeasonId != season or statSplitTypeId > 1 or statScoringPeriodId != week:
                        continue
                    else:
                        statSourceId = stattype.get('statSourceId')
                        statAppliedTotal = stattype.get('appliedTotal')
                        #print('Season ' + str(statSeasonId) + ", period " + str(statScoringPeriodId)+ ", source "+ str(statSourceId) + ", split " + str(statSplitTypeId) + ", total " + str(statAppliedTotal))
                        p.append([id, fullName, fteam, statScoringPeriodId, statSourceId, statAppliedTotal])
            else:
                continue
            
    p = pd.DataFrame(p, columns=['ID', 'Name', 'Fantasy Team ID', 'Week', 'Stat Type', 'Stat Total'])
    p.loc[p['Week'] == 0, 'Week'] = str(season) + " Season"
    p.loc[p['Stat Type'] == 0, 'Stat Type'] = "Actual"
    p.loc[p['Stat Type'] == 1, 'Stat Type'] = "Projected"
    #print(p)
    #p.to_excel(output_path + 'Fantasy-stats-new.xlsx')
    p.to_csv('output/Fantasy-stats-new.csv', index=False)

def get_fantasy_team_stats(league_id, season):
    slotcodes = {
        0 : 'QB', 2 : 'RB', 4 : 'WR',
        6 : 'TE', 16: 'Def', 17: 'K',
        20: 'Bench', 21: 'IR', 23: 'Flex'
    }
    
    url = fantasy_base_endpoint + str(season) + "/segments/0/leagues/" + str(league_id) + "?view=mMatchup&view=mMatchupScore"
    
    
    
    data = []
    for week in range(1,18):
        r = requests.get(url, params={'scoringPeriodId':week, 'seasonId':season})
        d = r.json()
        for tm in d['teams']:
            tmid = tm['id']
            for p in tm['roster']['entries']:
                name = p['playerPoolEntry']['player']['fullName']
                player_id = p['playerPoolEntry']['player']['id']
                slot = p['lineupSlotId']
                pos = slotcodes[slot]
                inj = 'NA'
                try:
                    inj = p['playerPoolEntry']['player']['injuryStatus']
                except:
                    pass
                    
                data.append([
                    week, tmid, player_id, name, slot, pos, inj
                ])
    
    
    data = pd.DataFrame(data, columns=['Week', 'Team', 'Player ID', 'Player', 'Slot', 'Pos', 'Status'])
    
    data.loc[data['Week'] == 0, 'Week'] = str(season) + " Season"
    
    
    # Get teamnames
    team_url = fantasy_base_endpoint + str(season) + "/segments/0/leagues/" + str(league_id) + "?view=mTeam"
    
    r = requests.get(team_url)
    d = r.json()
    
    team_data = []
    for tm in d['teams']:
        tm_id = tm['id']
        #tm_full_name = tm['location'] + " " + tm['nickname']
        tm_full_name = tm['name']
        team_data.append([tm_id, tm_full_name])
    
    team_data = pd.DataFrame(team_data, columns=['Team ID', 'Team Full Name'])
    
    #print(team_data)
    
    merged = data.join(team_data.set_index('Team ID'), on='Team')
    merged = merged[['Week', 'Team', 'Team Full Name', 'Player ID', 'Player', 'Slot', 'Pos', 'Status']]
    
    merged.to_csv('output/Fantasy-stats-within-team.csv', index=False)
    #merged.to_excel(output_path + 'Fantasy-stats-within-teams.xlsx')
    #print(merged)