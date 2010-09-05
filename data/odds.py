import datetime
import logging
import re
from xml.etree import ElementTree

from google.appengine.ext import db
from google.appengine.api import urlfetch

from models import Team, Game


feed_url = 'http://content.linesmaker.com/xml/lines/203.xml'
teams = Team.all_teams()
team_map = dict((team.name.lower(), team) for team in teams)


def update_odds():
    logging.info('Fetching %s...' % feed_url)
    resp = urlfetch.fetch(feed_url)
    if not resp.status_code == 200:
        return logging.error(
            'Could not update odds. Bad response: %s' % resp.status_code)
    logging.info('Parsing XML...')
    try:
        doc = ElementTree.fromstring(resp.content)
    except Exception, e:
        logging.error('Parse error: %s' % e)
        logging.error('Contents:\n%s' % resp.content)
    else:
        events = doc.findall('event')
        games = [handle_event(event) for event in events]
        logging.info('Found odds for %s games' % len(games))
        db.put(games)

def handle_event(event):
    home_team, away_team, date = find_event_info(event)
    game = Game.all()\
        .filter('home_team =', home_team)\
        .filter('away_team =', away_team)\
        .filter('start >=', date)\
        .get()

    if not game:
        return logging.error(
            'No game for %s @ %s @ %s' % (away_team, home_team, date))

    markets = event.find('markets').findall('market')
    points = None
    for market in markets:
        linetype = market.find('lineType')
        if linetype is not None and linetype.text.strip() == 'PSH':
            try:
                points = float(market.find('points').text)
            except ValueError:
                logging.error(
                    'Unknown points: %r' % market.find('points').text)
                points = None
            break
    game.spread = points
    logging.info('%s: %s' % (game, points))
    return game

def find_event_info(event):
    meta = event.find('eventDescriptor')
    home_team = get_team(meta.find('homeTeamName').text)
    away_team = get_team(meta.find('awayTeamName').text)
    date_string = meta.find('postTimeDateString').text
    date = datetime.datetime.strptime(date_string, '%m-%d-%y').date()
    return home_team, away_team, date

def get_team(s):
    """Expects a team name in the form Name(Place)."""
    p = r'(\w+)\(([^)]+)\)'
    match = re.match(p, s)
    assert match
    return team_map[match.group(1).lower()]
