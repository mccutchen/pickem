import base64
import calendar
import datetime
import email
import hashlib
import hmac
import logging
import re
import time

from ext import webapp2
from lib.jinja import render_to_string

from models import Account
from settings import COOKIE_SECRET


DEFAULT_STATUS = 200
DEFAULT_MIMETYPE = 'text/html; charset=utf-8'


class RequestHandler(webapp2.RequestHandler):
    """A custom Tornado RequestHandler that knows how to tell if a user has
    logged in via Twitter and renders Jinja2 templates."""

    @property
    def account(self):
        """A account is considered to be logged in via Twitter if they have
        their account_id stored in a secure cookie."""
        if not hasattr(self, '_account'):
            try:
                account_id = int(self.get_secure_cookie('account_id'))
            except:
                self._account = None
            else:
                self._account = Account.get_by_id(account_id)
        return self._account

    def render(self, template, context=None, status=None, mimetype=None):
        """Renders the given template (or list of templates to choose) with
        the given context using Jinja2."""
        context = context or {}
        self.response.set_status(status or DEFAULT_STATUS)
        self.response.headers['Content-type'] = mimetype or DEFAULT_MIMETYPE
        resp = render_to_string(template, context)
        self.response.out.write(resp.encode('utf-8', 'xmlcharrefreplace'))

    ##########################################################################
    # Cookie API and implementation ported from Tornado:
    # http://github.com/facebook/tornado/blob/master/tornado/web.py
    ##########################################################################
    def get_cookie(self, name, default=None):
        return self.request.cookies.get(name, default)

    def set_cookie(self, *args, **kwargs):
        return self.response.set_cookie(*args, **kwargs)

    def set_secure_cookie(self, name, value, **kwargs):
        """Signs and timestamps a cookie so it cannot be forged.

        You must specify the 'cookie_secret' setting in your Application
        to use this method. It should be a long, random sequence of bytes
        to be used as the HMAC secret for the signature.

        To read a cookie set with this method, use get_secure_cookie().
        """
        timestamp = str(int(time.time()))
        value = base64.b64encode(value)
        signature = cookie_signature(name, value, timestamp)
        value = "|".join([value, timestamp, signature])
        return self.set_cookie(name, value, **kwargs)

    def get_secure_cookie(self, name, value=None):
        """Returns the given signed cookie if it validates, or None.

        In older versions of Tornado (0.1 and 0.2), we did not include the
        name of the cookie in the cookie signature. To read these old-style
        cookies, pass include_name=False to this method. Otherwise, all
        attempts to read old-style cookies will fail (and you may log all
        your users out whose cookies were written with a previous Tornado
        version).
        """
        if value is None: value = self.get_cookie(name)
        if not value: return None
        parts = value.split("|")
        if len(parts) != 3: return None
        signature = cookie_signature(name, parts[0], parts[1])
        if not time_independent_equals(parts[2], signature):
            logging.warning("Invalid cookie signature %r", value)
            return None
        timestamp = int(parts[1])
        if timestamp < time.time() - 31 * 86400:
            logging.warning("Expired cookie %r", value)
            return None
        try:
            return base64.b64decode(parts[0])
        except:
            return None

    def delete_cookie(self, *args, **kwargs):
        return self.response.delete_cookie(*args, **kwargs)


##############################################################################
# Cookie utils, ported from Tornado:
# http://github.com/facebook/tornado/blob/master/tornado/web.py
##############################################################################

def cookie_signature(*parts):
    h = hmac.new(COOKIE_SECRET, digestmod=hashlib.sha1)
    for part in parts:
        h.update(part)
    return h.hexdigest()

def time_independent_equals(a, b):
    if len(a) != len(b):
        return False
    result = 0
    for x, y in zip(a, b):
        result |= ord(x) ^ ord(y)
    return result == 0

def utf8(s):
    if isinstance(s, unicode):
        return s.encode("utf-8")
    return str(s)
