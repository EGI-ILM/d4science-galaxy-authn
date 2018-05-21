from webob import Request, Response
from webob.exc import HTTPUnauthorized, HTTPFound
import requests

D4SCIENCE_SOCIAL_URL = ('https://socialnetworking1.d4science.org/'
                        'social-networking-library-ws/rest/2/people/profile')

class AuthMiddleware(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        req = Request(environ)

        user = req.cookies.get('gcube-user', '')
        if not user:
            user = 'pepe@gmail.com'
            token = req.params.get('gcube-token', "")
            if not token:
                return HTTPUnauthorized()(environ, start_response)
            else:
                r = requests.get(D4SCIENCE_SOCIAL_URL,
                                 params={'gcube-token': token})
                if r.status_code != 200:
                    return HTTPUnauthorized()(environ, start_response)
                user = r.json()['result']['username']
                response = req.get_response(HTTPFound())
                response.set_cookie('gcube-user', user)
                return response(environ, start_response)
        environ['HTTP_REMOTE_USER'] = user
        return self.app(environ, start_response)


def galaxy_app():
    import galaxy.webapps.galaxy.buildapp as buildapp
    app = AuthMiddleware(buildapp.uwsgi_app())
    return app
