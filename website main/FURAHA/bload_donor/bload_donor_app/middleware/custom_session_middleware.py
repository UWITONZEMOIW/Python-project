from importlib import import_module
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

class MultiSessionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        engine = import_module(settings.SESSION_ENGINE)
        path = request.path

        # Assign session key name based on URL
        if path.startswith('/admin/'):
            cookie_name = 'admin_sessionid'
        elif path.startswith('/collector/'):
            cookie_name = 'collector_sessionid'
        elif path.startswith('/donor/'):
            cookie_name = 'donor_sessionid'
        else:
            cookie_name = 'sessionid'  # default

        request.session_cookie_name = cookie_name
        session_key = request.COOKIES.get(cookie_name)
        request.session = engine.SessionStore(session_key)

    def process_response(self, request, response):
        try:
            accessed = request.session.accessed
            modified = request.session.modified
        except AttributeError:
            return response

        if accessed:
            cookie_name = getattr(request, 'session_cookie_name', settings.SESSION_COOKIE_NAME)
            if modified or settings.SESSION_SAVE_EVERY_REQUEST:
                if request.session.get_expire_at_browser_close():
                    max_age = None
                    expires = None
                else:
                    max_age = settings.SESSION_COOKIE_AGE
                    expires_time = request.session.get_expiry_date()
                    expires = expires_time.strftime("%a, %d-%b-%Y %H:%M:%S GMT")

                response.set_cookie(
                    cookie_name,
                    request.session.session_key,
                    max_age=max_age,
                    expires=expires,
                    domain=settings.SESSION_COOKIE_DOMAIN,
                    path=settings.SESSION_COOKIE_PATH,
                    secure=settings.SESSION_COOKIE_SECURE,
                    httponly=settings.SESSION_COOKIE_HTTPONLY,
                    samesite=settings.SESSION_COOKIE_SAMESITE,
                )
        return response
