#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import logging
from google.appengine.ext.webapp import template
import os
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api import users
from buzzexceptions import BuzzAuthorizationException, BuzzOperationException
from data import YahooOauthData
from yahoo_gateway import YahooUser

def need_to_oauth_yahoo_user(yahoo_user):
    if not yahoo_user.admin_user.access_token or not yahoo_user.admin_user.access_secret or not yahoo_user.admin_user.session_handle:
        return True

    return False

class BaseHandler(webapp.RequestHandler):

    def get_account(self):
        self.template_values = {}
        if users.get_current_user():
            self.template_values['login_out_url'] = users.create_logout_url("/")
            self.template_values['login_out_linktext'] = "Logout"
        else:
            self.template_values['login_out_url'] = users.create_login_url("/")
            self.template_values['login_out_linktext'] = "Login"
            raise BuzzAuthorizationException("You must login")
        user = users.get_current_user()
        self.template_values['username'] = user.nickname()
        users_query = YahooOauthData.all()
        users_query.filter('google_user = ', user)
        found_user_a = users_query.fetch(1)
        if not found_user_a:
            # make new one
            yahoo_data = YahooOauthData(google_user=user)
            yahoo_data.put()
            logging.log(logging.INFO, "A new user has joined: %s" % (str(user)))
        else:
            yahoo_data = found_user_a[0]
        self.yahoo_user = YahooUser(yahoo_data, callback_url="%s/oauthdone" % (get_app_base_url()))
        logging.log(logging.INFO, "User %s has accessed the system." % (str(user)))
        return self.yahoo_user

    def link_yahoo_oauth(self, yahoo_user, request):
        url = yahoo_user.start_oauth(reset=True)
        self.template_values['redirecturl'] = url
        self.write_page("templates/startoauth.html")

    def write_page(self, template_filename):
        path = os.path.join(os.path.dirname(__file__), template_filename)
        self.response.out.write(template.render(path, self.template_values))


class ResultsHandler(BaseHandler):

    def post(self):
        self.do_page()

    def get(self):
        self.do_page()

    def do_page(self):
        terms = self.request.get("terms")

        yahoo_user = self.get_account()

        logging.log(logging.INFO, "User %s has is searching for %s." % (str(yahoo_user), terms))


        terms_a = terms.split()
        links = yahoo_user.search(terms_a)
        self.template_values['search_terms'] = terms
        self.template_values['links'] = links
        self.write_page("templates/results.html")

def get_app_base_url():
    server = os.environ['SERVER_SOFTWARE']
    ndx = server.find("Development")
    scheme = "http"
    if ndx >= 0:
        scheme = "http"
    return "%s://%s:%s" % (scheme, os.environ['SERVER_NAME'], os.environ['SERVER_PORT'])

class LandingHandler(BaseHandler):

    def post(self):
        self.do_page()

    def get(self):
        self.do_page()

    def do_page(self):
        yahoo_user = self.get_account()
        if not yahoo_user.admin_user.yahoo_consumer_key or not yahoo_user.admin_user.yahoo_consumer_secret:
            self.write_page("templates/yahoooauth.html")
        elif need_to_oauth_yahoo_user(yahoo_user):
            self.link_yahoo_oauth(yahoo_user, self)
        else:
            yahoo_user.check_refresh()
            self.write_page("templates/search.html")

class StartOauth(BaseHandler):

    def post(self):
        self.do_page()

    def get(self):
        self.do_page()

    def do_page(self):
        yahoo_user = self.get_account()

        consumer_key = self.request.get("yahoo_key")
        consumer_secret = self.request.get("yahoo_secret")

        if not consumer_key or not consumer_secret:
            raise BuzzOperationException("You must specify a consumer key and secret")

        yahoo_user.set_consumer_keys(consumer_key, consumer_secret)

        self.link_yahoo_oauth(yahoo_user, self)


class YahooOauthReturnUserHandler(BaseHandler):
    def post(self):
        self.do_page()

    def get(self):
        self.do_page()

    def do_page(self):
        yahoo_user = self.get_account()
        yahoo_user.set_auth_response(self.request)
        self.redirect("/")


def main():
    debug = True
    application = webapp.WSGIApplication([('/', LandingHandler),
                                          ('/startoauth', StartOauth),
                                          ('/results', ResultsHandler),
                                          ('/oauthdone', YahooOauthReturnUserHandler),
                                        ],
                                         debug=debug)

    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
