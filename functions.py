import json
import logging
import requests
import pandas as pd
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import re
import os

output_path = 'output/'
os.makedirs(os.path.dirname(output_path), exist_ok=True)

def get_schedule(sports, league, season, seasontype):
    league_schedule = []
    team_info = []

    # Get teams
    # Sample url: https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/teams 
    teams_url = "https://site.api.espn.com/apis/site/v2/sports/" + sports + "/" + league + "/teams"
    request_teams = requests.get(teams_url)
    data = request_teams.json()['sports'][0]['leagues'][0]
    league_id = data['id']
    league_name = data['name']
    for teams in data['teams']:
        team_id = teams['team']['id']
        team_alt_color = "#" + teams['team']['alternateColor']
        
        # Get schedule for team, seasontype=2 = regular season
        # Sample url: https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/teams/22/schedule?season=2023&seasontype=2
        team_schedule_url = 'https://site.api.espn.com/apis/site/v2/sports/' + sports + '/' + league + '/teams/' + team_id + '/schedule?season='+str(season)+'&seasontype=' + str(seasontype)
        request_schedule = requests.get(team_schedule_url).json()
        team = request_schedule['team']
        
        # Team Information
        team_id = team['id']
        team_abbrev = team['abbreviation']
        team_location = team['location']
        team_name = team['name']
        team_displayname = team['displayName']
        team_color = "#" + team['color']
        team_logo = team['logo']
        #team_bye = request_schedule['byeWeek']

        # Log team to console
        #print(team_name)
        
        team_info.append([sports, league, team_id, team_abbrev, team_location, team_name, team_displayname, team_color, team_alt_color, team_logo])
        
        # Game information
        for event in request_schedule['events']:
            event_id = event['id']
            event_name = event['name']
            # event_date = datetime.strptime(event['date'], "%Y-%m-%dT%H:%MZ").strftime("%Y%m%d")
            event_date = datetime.strptime(event['date'], "%Y-%m-%dT%H:%MZ").replace(tzinfo=timezone.utc).astimezone(tz=ZoneInfo('Europe/Amsterdam')).strftime("%Y%m%d")
            event_time = datetime.strptime(event['date'], "%Y-%m-%dT%H:%MZ").replace(tzinfo=timezone.utc).astimezone(tz=ZoneInfo('Europe/Amsterdam')).strftime("%H:%M")
            event_date_NY = datetime.strptime(event['date'], "%Y-%m-%dT%H:%MZ").replace(tzinfo=timezone.utc).astimezone(tz=ZoneInfo('America/New_York')).strftime("%Y%m%d")
            event_time_NY = datetime.strptime(event['date'], "%Y-%m-%dT%H:%MZ").replace(tzinfo=timezone.utc).astimezone(tz=ZoneInfo('America/New_York')).strftime("%H:%M")
            event_status = event['competitions'][0]['status']['type']['description']
            event_shortname = event['shortName']
            event_week = event.get('week', {}).get('text')
            for competitors in event['competitions'][0]['competitors']:
                if competitors['homeAway'] == 'home':
                    homeTeam = competitors['team']['displayName']
                    try:
                        homeScore = int(competitors['score']['value'])
                    except:
                        homeScore = ""
                elif competitors['homeAway'] == 'away':
                    awayTeam = competitors['team']['displayName']
                    try:
                        awayScore = int(competitors['score']['value'])
                    except:
                        awayScore = ""
                else:
                    print('homeAway type not home/away!')
            if event_status == "Scheduled":
                score = " "
            elif event_status == "Postponed":
                score = "P"
            else:
                score = str(homeScore) + "-" + str(awayScore)
    
            league_schedule.append([team_id, league_name, event_date, event_time, event_id, event_name, event_shortname,  event_status, homeTeam, awayTeam, homeScore, awayScore, score, event_week, event_date_NY, event_time_NY])
    
    #Teams sheet
    team_info_table = pd.DataFrame(team_info, columns=['Sport', 'League', 'ID', 'Abbreviation', 'Location', 'Name', 'Display Name', 'Color', 'Alternative Color', 'Logo URL'])
    
    #Schedule sheet
    league_schedule_table = pd.DataFrame(league_schedule, columns=['Team ID', 'League', 'Date', 'Time', 'Match ID', 'Match Name', 'Match abbreviation', 'Match Status', 'Home Team', 'Away Team', 'Home Score', 'Away Score', 'Score', 'Week', 'Date (ET)', 'Time (ET)'])
    
    team_info_table.to_csv('output/Teams '+ league + ' ' + str(season) + '-' + str(seasontype) +'.csv', index=False)
    league_schedule_table.to_csv('output/Schedule '+ league + ' ' + str(season) + '.csv', index=False)

    print('Team info & league schedule updated.')
    

def get_standings(sports, leagues, season):
    division_standings = []

    # Get division standings
    # Sample url: https://site.web.api.espn.com/apis/v2/sports/baseball/mlb/standings?region=us&lang=en&contentorigin=espn&type=0&level=3&sort=gamesbehind%3Aasc%2Cwinpercent%3Adesc%2Cplayoffseed%3Aasc&startingseason=2002
    division_standings_url = 'https://site.web.api.espn.com/apis/v2/sports/' + sports + '/' + leagues + '/standings?region=us&lang=en&contentorigin=espn&type=0&level=3&sort=gamesbehind%3Aasc%2Cwinpercent%3Adesc%2Cplayoffseed%3Aasc&season=' + str(season)
    
    request_standings = requests.get(division_standings_url)
    data = request_standings.json()['children']
    for league in data:
        league_id = league['id']
        league_name = league['name']
        league_abbrev = league['abbreviation']
        print(f'League is {league_name} ({league_abbrev}) with ID {league_id}')
        for division in league['children']:
            division_id = division['id']
            division_name = division['name']
            division_abbrev = division['abbreviation']
            print(f'Division is {division_name} ({division_abbrev}) with ID {division_id}')
            for index, team in enumerate(division['standings']['entries']):
                team_ranking = index +1
                team_id = team['team']['id']
                team_name = team['team']['displayName']
                team_logo = team['team']['logos'][0]['href']
                print(f'{division_abbrev} #{team_ranking}: {team_name}')
                for stat in team['stats']:
                    try:
                        stat_id = stat['name']
                        stat_name = stat['displayName']
                    except:
                        stat_name = stat['name']
                    try:
                        stat_value = stat['value']
                    except:
                        stat_value = stat['displayValue']
                    division_standings.append([league_id, league_name, league_abbrev, division_id, division_name, division_abbrev, team_id, team_name, team_logo, team_ranking, stat_id, stat_name, stat_value])
    standings = pd.DataFrame(division_standings, columns= ['League ID', 'League Name', 'League Abbreviation','Division ID', 'Division Name', 'Division Abbreviation', 'Team ID', 'Team Name', 'Team Logo', 'Team Ranking', 'Stat ID', 'Stat name', 'Stat value'])
    
    # temp fix for NFL
    standings = standings[(standings['Stat ID'] != 'pointDifferential')]

    standings_pvt = standings.pivot(columns = 'Stat name', values='Stat value', index=['League ID', 'League Name', 'League Abbreviation','Division ID', 'Division Name', 'Division Abbreviation', 'Team ID', 'Team Name', 'Team Logo', 'Team Ranking']).reset_index()
    standings_pvt.to_csv('output/Standings '+ leagues + ' ' + str(season) +'.csv', index=False)
    print('Division standings updated.')
    
def get_rosters(sports, leagues, season):
    
    teams_url = "https://site.api.espn.com/apis/site/v2/sports/" + sports + "/" + leagues + "/teams"
    request_teams = requests.get(teams_url)
    teams = request_teams.json()['sports'][0]['leagues'][0]['teams']

    athletes = []
    for team in teams:
        teamid = team['team']['id']
        roster_url = 'https://site.api.espn.com/apis/site/v2/sports/' + sports + '/' + leagues + '/teams/' + str(teamid) + '?enable=roster,projection,stats'
        request_rosters = requests.get(roster_url)
        data = request_rosters.json()['team']
        team_id = data.get('id')
        team_name = data.get('displayName')

        for athlete in data['athletes']:
            id = athlete.get('id')
            firstName = athlete.get('firstName')
            lastName = athlete.get('lastName')
            displayName = athlete.get('displayName')
            weight = athlete.get('displayWeight')
            height = athlete.get('displayHeight')
            age = athlete.get('age')
            headshot = athlete.get('headshot', {}).get('href')
            jersey = athlete.get('jersey')
            pos_displayName = athlete.get('position', {}).get('displayName')
            pos_abbreviation = athlete.get('position', {}).get('abbreviation')
            status_displayName = athlete.get('status', {}).get('name')
            experience = athlete.get('experience', {}).get('years')

            athletes.append([team_id, team_name, id, firstName, lastName, displayName, weight, height, age, headshot, jersey, pos_displayName, pos_abbreviation, status_displayName, experience])

    athlete_table = pd.DataFrame(athletes, columns=['Team ID', 'Team Name', 'ID', 'First Name', 'Last Name', 'Display Name', 'Weight','Height','Age','Headshot','Jersey','Position','Position abbreviation','Status','Experience'])
    
    athlete_table.to_csv('output/Rosters '+ leagues + ' ' + str(season) +'.csv', index=False)
    
def get_stats_leaders(sports, leagues, season):
    url = 'https://sports.core.api.espn.com/v2/sports/' + sports + '/leagues/' + leagues + '/seasons/' + str(season) + '/types/2/leaders?limit=1000'
    try:
        data = requests.get(url).json()['categories']
    except:
        return "No stats for sports/season combo"

    leaders = []

    for stat in data:
        stat_name = stat.get('displayName')
        #print(stat_name)
        rank = 1
        for player in stat['leaders']:
            ba = player.get('athlete', {}).get('$ref')
            pattern = "http://sports.core.api.espn.com/v2/sports/" + sports + '/leagues/' + leagues +'/seasons/' + str(season) + "/athletes/(.*?)\?lang=en&region=us"
            athlete = re.search(pattern, ba).group(1)
            displayValue = player.get('displayValue')
            value = player.get('value')
            leaders.append([stat_name, rank, athlete, value, displayValue])
            rank = rank+1

    ba_table = pd.DataFrame(leaders, columns=['Stat Name', 'Rank', 'Athlete', 'Value', 'Display Value'])
    
    ba.to_csv('output/Stats Leaders '+ leagues + ' ' + str(season) +'.csv', index=False)

    #wr.s3.to_csv(df=ba_table, path='s3://espn-files/' + leagues + '/Stats Leaders ' + leagues + ' ' + str(season) + '.csv', index=False, s3_additional_kwargs={'ACL': 'public-read'})