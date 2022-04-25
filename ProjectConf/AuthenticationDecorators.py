from time import strftime
from functools import wraps
import flask
import logging
from flask import Blueprint, current_app
from firebase_admin import auth, exceptions
import traceback

auth_decorators_app = Blueprint('Auth_Decorators', __name__)

@auth_decorators_app.after_request
def after_request(response):
    """ Logging after every request. """
    # This avoids the duplication of registry in the log,
    # since that 500 is already logged via @app.errorhandler.
    if response.status_code != 500:
        ts = strftime('[%Y-%b-%d %H:%M]')
        current_app.logger.error('%s %s %s %s %s %s',
                      ts,
                      flask.request.remote_addr,
                      flask.request.method,
                      flask.request.scheme,
                      flask.request.full_path,
                      response.status)
    return response


@auth_decorators_app.errorhandler(Exception)
def exceptions(e):
    """ Logging after every Exception. """
    ts = strftime('[%Y-%b-%d %H:%M]')
    tb = traceback.format_exc()
    current_app.logger.error('%s %s %s %s %s 5xx INTERNAL SERVER ERROR\n%s',
                  ts,
                  flask.request.remote_addr,
                  flask.request.method,
                  flask.request.scheme,
                  flask.request.full_path,
                  tb)
    return "Internal Server Error", 500


def validateCookie(f):
    @wraps(f)
    def decorated_function(*args, **kws):
        try:
            session_cookie = flask.request.cookies.get('session')
            if not session_cookie:
                current_app.logger.exception("No Cookie Present, failed to validate cookie")
                current_app.logger.exception(traceback.format_exc())
                flask.abort(401, 'No session cookie available')
            try:
                decoded_claims = auth.verify_session_cookie(session_cookie, check_revoked=True)
                return f(decoded_claims, *args, **kws)
            except auth.InvalidSessionCookieError:
                current_app.logger.exception("InvalidSessionCookieError: Can't verify cookie, cookie must have expired")
                current_app.logger.exception(traceback.format_exc())
                flask.abort(401, 'InvalidSessionCookieError')
        except:
            current_app.logger.exception("Cookie verification failed: Unsure about error")
            current_app.logger.exception(traceback.format_exc())
            flask.abort(401, 'Failed to validate cookie')
    return decorated_function