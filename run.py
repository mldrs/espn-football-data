import json
import logging
import requests
import pandas as pd
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import re
import functions as fn

def get_espn_data(event):

    sport = event['sport']
    league = event['league']
    season = event['season']
    seasontype = event['seasontype']
    league_id = event['league_id']
    print(f"Getting data for {league} {sport} in season {season} with Fantasy League ID {league_id}")
    
    print(str(datetime.now()) + ': Updating schedules and team info...')
    fn.get_schedule(sport, league, season, seasontype)
    
    print(str(datetime.now()) + ': Updating standings...')
    fn.get_standings(sport, league, season)
    
    print(str(datetime.now()) + ': Updating rosters...')
    fn.get_rosters(sport, league, season)
    
    #if sport == 'baseball':
    #    print(str(datetime.now()) + ': Updating stats leaders...')
    #    fn.get_stats_leaders(sport, league, season)
    #elif sport == 'football':
    #    league_id = event['league_id']
    #    ffn.get_fantasy_teams(league_id, season)
    #    ffn.get_fantasy_stats(league_id, season)
    #    ffn.get_fantasy_team_stats(league_id, season)

get_espn_data(
    {
        "sport":"football",
        "league":"nfl",
        "season": 2025,
        "league_id": 80921619,
        "seasontype": 2
    }
)