import logging
from cgi import parse_qs
from urllib import urlencode

from google.appengine.ext import db
from google.appengine.api import urlfetch
from django.utils import simplejson as json

from lib.webapp import RequestHandler

from models import Account
import settings


class LoginHandler(RequestHandler):

    def get(self):
        """Handles both legs of OAuth authorization. On the first request, the
        user is redirected to Facebook to authorize our application, with this
        same URL as the return point.  On the second request, a verification
        code is given which will allow us to get an access code which we can
        use to get the user's profile info from Facebook."""

        logging.info('Logging in via Facebook...')

        # See if we got a verification code from Facebook (which will happen
        # when the callback is hit after the user authorizes the app on
        # Facebook)
        code = self.request.get('code')

        # Figure out if we've got a "next" destination
        next = self.request.get('next')

        # Get a Facebook object to work with
        fb = Facebook(self.request.path_url)

        # If not, we need to redirect them to Facebook to authorize us
        if not code:
            logging.info('Auth URL: %s' % fb.auth_url)
            if next:
                self.set_secure_cookie('next', next)
            return self.redirect(fb.auth_url)

        # If so, we need to use the verification code to get an access code,
        # and use that to create/update a user account.
        else:
            access_token = fb.get_access_token(code)
            assert access_token, 'No access token for code %s' % code

            profile = fb.get_profile(access_token)
            assert profile, 'No profile for token %s' % access_token

            key_name = 'facebook:%s' % profile['id']
            acc = Account.get_or_insert(
                key_name,
                email=profile['email'],
                first_name=profile['first_name'],
                last_name=profile['last_name'],
                oauth_token=access_token)

            self.set_secure_cookie('account', str(acc.key()))
            next = self.get_secure_cookie('next')
            if next:
                self.delete_cookie('next')
                return self.redirect(next)
            else:
                return self.redirect_to('index')


class AccountHandler(RequestHandler):
    pass


class Facebook(object):

    AUTH_URL = 'https://graph.facebook.com/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://graph.facebook.com/oauth/access_token'
    PROFILE_URL = 'https://graph.facebook.com/me'
    PROFILE_ICON_URL = 'http://graph.facebook.com/%s/picture?type=square'
    PERMISSIONS = 'email'

    def __init__(self, redirect_uri):
        self.redirect_uri = redirect_uri

    @property
    def auth_url(self):
        args = dict(scope=self.PERMISSIONS, **self.base_args)
        return '%s?%s' % (self.AUTH_URL, urlencode(args))

    def get_access_token(self, verifier):
        """Exchanges the given verification code for an access token, which
        gives us actual access to the account's information."""
        logging.info('Getting access token for verifier %s' % verifier)
        resp = self.make_request(self.ACCESS_TOKEN_URL,
                                 client_secret=settings.FB_APP_SECRET,
                                 code=verifier)

        # Did we get a good response?
        if resp.status_code == 200:
            data = parse_qs(resp.content)
            return data['access_token'][-1]
        else:
            logging.error('Access Token Error')
            logging.error('Status %s: %s' % (resp.status_code, resp.content))
            return None

    def get_profile(self, access_token):
        logging.info('Getting FB account for access token %s' % access_token)
        resp = self.make_request(self.PROFILE_URL,
                                 access_token=access_token)
        if resp.status_code == 200:
            return json.loads(resp.content)
        else:
            logging.error('Account Error')
            logging.error('Status %s: %s' % (resp.status_code, resp.content))
            return None

    def make_request(self, url, **kwargs):
        kwargs.update(self.base_args)
        url = '%s?%s' % (url, urlencode(kwargs))
        logging.info('FB Request: %s' % url)
        return urlfetch.fetch(url)

    @property
    def base_args(self):
        return dict(client_id=settings.FB_APP_ID,
                    redirect_uri=self.redirect_uri)


class ProfileHandler(RequestHandler):
    pass
