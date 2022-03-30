import os
import logging

from webob import Request, Response
from webob.exc import HTTPUnauthorized, HTTPFound
import requests

D4SCIENCE_SOCIAL_URL = ('https://socialnetworking1.d4science.org/'
                        'social-networking-library-ws/rest/2/users/get-email')

USER_TOKENS_DIRECTORY = '/etc/d4science/'

class AuthMiddleware(object):
    def __init__(self, app):
        self.app = app

    def get_user_token_file(self, user):
        return os.path.join(USER_TOKENS_DIRECTORY, user)

    def __call__(self, environ, start_response):
        req = Request(environ)

        print("31337")
        logging.error("Receiving request")
        path = os.environ.get('EGI_PROXY_PREFIX', '/')
        token = req.params.get('gcube-token', '')
        user = None
        if token:
            logging.debug("Token present, reauthenticating")
            r = requests.get(D4SCIENCE_SOCIAL_URL,
                             params={'gcube-token': token})
            if r.status_code != 200:
                return HTTPUnauthorized()(environ, start_response)
            user = r.json()['result']
            response = req.get_response(HTTPFound())
            # 432000 seconds is 5 days
            response.set_cookie('gcube-user-email', value=user, path=path,
                                max_age=432000)
            environ['GCUBE_TOKEN'] = token
            user_info_file = self.get_user_token_file(user)
            if not os.path.exists(user_info_file):
                with open(user_info_file, 'w') as f:
                    f.write(token)
            # make user we go to the right place
            return response(environ, start_response)
        else:
            user = req.cookies.get('gcube-user-email', '')
            if not user:
                return HTTPUnauthorized()(environ, start_response)
            if not os.path.exists(self.get_user_token_file(user)):
                logging.debug("Existing cookie, but no token file, failing")
                # User with cookie but without token !?
                return HTTPUnauthorized()(environ, start_response)
        environ['HTTP_REMOTE_USER'] = user
        environ['ILM'] = "all good"
        return self.app(environ, start_response)


def galaxy_app():
    import galaxy.webapps.galaxy.buildapp as buildapp
    app = AuthMiddleware(buildapp.uwsgi_app())
    return app
