from datetime import datetime, timedelta
import logging
import urllib2
from buzzexceptions import BuzzYahooOauthException
from oauth import get_oauth_client
import simplejson as json

class YahooUser(object):

    def __init__(self, user, callback_url=""):

        self.admin_user = user

        self._request_token_url = "https://api.login.yahoo.com/oauth/v2/get_request_token"
        self._access_token_url = "https://api.login.yahoo.com/oauth/v2/request_auth"
        self._get_token_url = "https://api.login.yahoo.com/oauth/v2/get_token"

        self._callback_url = callback_url
        self._oauthclient = get_oauth_client("yahoo", self.admin_user._yahoo_consumer_key, self.admin_user._yahoo_consumer_secret, self._callback_url)

    def set_consumer_keys(self, key, secret):
        self.admin_user.yahoo_consumer_key = key
        self.admin_user.yahoo_consumer_secret = secret
        self.admin_user.put()

    def set_auth_response(self, request):
        auth_token = request.get("oauth_token")
        auth_verifier = request.get("oauth_verifier")
        oauth_problem = request.get("oauth_problem")

        if oauth_problem:
            raise BuzzYahooOauthException(oauth_problem)
        if not auth_token or not auth_verifier:
            raise BuzzYahooOauthException("Token and/or Verifier were not provided")
        result = self._oauthclient.get_user_info(auth_token, auth_verifier=auth_verifier)

        self.admin_user.access_token = result["token"]
        self.admin_user.access_secret = result["secret"]
        self.admin_user.session_handle = result["session_handle"]
        self.admin_user.yahoo_oauth_refresh_date = datetime.now()
        self.admin_user.put()

    def test_user_account(self, info=False):
        if not self.admin_user.access_token or not self.admin_user.access_secret:
            self.reset_oauth()
            return False
        return True

    def start_oauth(self, reset=False):
        if reset:
            self.reset_oauth()
        if self.admin_user.access_token and self.admin_user.access_secret:
            raise BuzzYahooOauthException("The users account is already associated with yahoo.  You must reset the values to continue")
        url = self._oauthclient.get_authorization_url()
        return url

    def reset_oauth(self):
        self.admin_user.access_token = ""
        self.admin_user.access_secret = ""
        self.admin_user.session_handle = ""
        self.admin_user.put()

    def check_refresh(self):
        tm = datetime.now() - timedelta(minutes=50)
        if not self.admin_user.yahoo_oauth_refresh_date or self.admin_user.yahoo_oauth_refresh_date < tm:
            self.refresh()

    def refresh(self):
        self._oauthclient.refresh(self.admin_user.access_token, self.admin_user.access_secret, self.admin_user.session_handle)
        self.admin_user.yahoo_oauth_refresh_date = datetime.now()
        self.admin_user.put()

    def search(self, terms_list):

        service = "web"
        key_line = ' '.join(terms_list)
        key_line_a = key_line.split()
        key_line = urllib2.quote(' '.join(key_line_a))

        base_url = "http://yboss.yahooapis.com/ysearch/%s" % (service)

        params = {"q" : key_line,
                  "count": "10"}
        url = base_url

        response  = self._oauthclient.make_request(url,
                                    token=self.admin_user.access_token,
                                    secret=self.admin_user.access_secret,
                                    additional_params=params)
        if response.status_code != 200:
            raise Exception("failed to search, status code %d, %s" % (response.status_code, response.content))
        data = json.loads(response.content)
        results = data['bossresponse'][service]
        results = results['results']

        return results


    def get_google_user(self):
        return self.admin_user.google_user

    def __str__(self):
        return str(self.get_google_user())
        