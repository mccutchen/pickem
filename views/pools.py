import logging
from lib.webapp import RequestHandler


class Index(RequestHandler):

    def get(self):
        return self.render('templates/index.html')
        return self.render('index.html')


class Pools(RequestHandler):
    pass


class Pool(RequestHandler):
    pass


class Entries(RequestHandler):
    pass


class Entry(RequestHandler):
    pass


class Picks(RequestHandler):
    pass


class Pick(RequestHandler):
    pass


class ManagePool(RequestHandler):
    pass


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

        # If not, we need to redirect them to Facebook to authorize us
        if not code:
            url = oauth.facebook.get_auth_url()
            return self.redirect(url)

        # If so, we need to use the verification code to get an access code,
        # and use that to update/create a user account.
        else:
            access_token = oauth.facebook.get_access_token(code)

            # See if we've got an existing OAuth connection for this OAuth
            # account.
            ext_id = oauth.facebook.get_ext_id(access_token)
            oauth_info = OauthInfo.get_by_external_id(ext_id, 'facebook')

            # If so, just look up the corresponding account and log it in.
            if oauth_info:
                acc = Account.get_by_id(oauth_info.account_id)
                if acc:
                    acc.set_oauth(oauth_info)
                    oauth_info.update_access(token_secret=access_token)
                    auth.login(self, acc, True) # Implicit acc.put()
                    return self.do_redirect()
                else:
                    self.add_message('Account not found.')
                    return self.redirect('/signin/')

            # If not, we need to do the one-time-only OAuth connection
            # confirmation dance.
            else:
                self.session['token_key'] = ''
                self.session['token_secret'] = access_token
                url = reverse('ConfirmOauthHandler', 'facebook')
                return self.redirect(url)


class Account(RequestHandler):
    pass
