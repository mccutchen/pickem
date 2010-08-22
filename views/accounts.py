import logging
from cgi import parse_qs
from urllib import urlencode

from django.utils import simplejson as json
from lib.webapp import RequestHandler


class Login(RequestHandler):

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

        # Get a Facebook object to work with
        fb = Facebook(self.request.url)

        # If not, we need to redirect them to Facebook to authorize us
        if not code:
            return self.redirect(fb.auth_url)

        # If so, we need to use the verification code to get an access code,
        # and use that to create/update a user account.
        else:
            access_token = fb.get_access_token(code)

            # See if we've got an existing OAuth connection for this OAuth
            # account.
            profile = fb.get_profile(access_token)
            assert profile is not None

            # Get or create a new account in a transaction
            def txn():
                ext_id = profile['id']
                acc = Account.all().filter(ext_id=ext_id).get()
                if acc is None:
                    logging.info('Creating new account for FB id %s' % ext_id)
                    acc = Account(
                        email=profile['email'],
                        first_name=profile['first_name'],
                        last_name=profile['last_name'],
                        oauth_token=access_token)
                    acc.put()
                return acc
            account = db.run_in_transaction(txn)
            self.set_secure_cookie('account_id', acc.key().id())
            return self.redirect_to('Index')


class Account(RequestHandler):
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
        resp = self.make_request(self.ACCESS_TOKEN_URL,
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
        return urlfetch.fetch(url)

    @property
    def base_args(self):
        return dict(client_id=settings.FB_APP_ID,
                    redirect_uri=self.redirect_uri)
