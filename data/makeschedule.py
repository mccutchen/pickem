import datetime
import simplejson as json
import env

from google.appengine.ext import db
import models

scheduleData = json.load(open('data/schedule.json'))

fmt = '%Y-%m-%d %H:%M:%S'

def parsedate(s):
    d = datetime.datetime.strptime(s, fmt)
    return d + datetime.timedelta(hours=5) # convert to UTC

season_start = parsedate(scheduleData[0]['start']).date()
season_end = parsedate(scheduleData[-1]['end']).date()

season = models.Season.all()\
    .filter('start_date =', season_start)\
    .filter('end_date =', season_end)\
    .get()
if not season:
    print 'making season'
    season = models.Season(start_date=season_start, end_date=season_end)
    season.put()

print season

slates = []
games = []
for slateData in scheduleData:
    slate = db.Query(models.Slate).ancestor(season)\
        .filter('name =', slateData['name']).get()
    if not slate:
        slate = models.Slate(
            parent=season,
            start=parsedate(slateData['start']),
            end=parsedate(slateData['end']),
            name=slateData['name'])
        slate.put()
    print slate
    
    for gamedata in slateData['games']:
        home_key = gamedata['home'].keys()[0]
        away_key = gamedata['away'].keys()[0]
        home_team = models.Team.get_by_key_name(home_key)
        away_team = models.Team.get_by_key_name(away_key)
        assert home_team
        assert away_team
        game = db.Query(models.Game).ancestor(slate)\
            .filter('home_team =', home_team)\
            .filter('away_team =', away_team)\
            .get()
        if not game:
            game = models.Game(
                parent=slate,
                home_team=home_team,
                away_team=away_team,
                start=parsedate(gamedata['datetime']))
        games.append(game)
        print ' -', game

gamekeys = db.put(games)
