import logging
from lib.webapp import RequestHandler


class OddsHandler(RequestHandler):

    def get(self):
        from data import odds
        logging.info('Updating odds...')
        odds.update_odds()
