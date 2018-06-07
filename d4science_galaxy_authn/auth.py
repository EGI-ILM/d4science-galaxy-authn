from webob import Request, Response
from webob.exc import HTTPUnauthorized, HTTPFound
import requests

D4SCIENCE_SOCIAL_URL = ('https://socialnetworking1.d4science.org/'
                        'social-networking-library-ws/rest/2/users/get-email')

class AuthMiddleware(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        req = Request(environ)

        user = req.cookies.get('gcube-user-email', '')
        if not user:
            token = req.params.get('gcube-token', "")
            if not token:
                return HTTPUnauthorized()(environ, start_response)
            else:
                r = requests.get(D4SCIENCE_SOCIAL_URL,
                                 params={'gcube-token': token})
                if r.status_code != 200:
                    return HTTPUnauthorized()(environ, start_response)
                user = r.json()['result']
                response = req.get_response(HTTPFound())
                # 432000 seconds is 5 days
                response.set_cookie(name='gcube-user-email', value=user,
                                    max_age=432000)
                return response(environ, start_response)
        environ['HTTP_REMOTE_USER'] = user
        return self.app(environ, start_response)


def galaxy_app():
    import galaxy.webapps.galaxy.buildapp as buildapp
    app = AuthMiddleware(buildapp.uwsgi_app())
    return app
