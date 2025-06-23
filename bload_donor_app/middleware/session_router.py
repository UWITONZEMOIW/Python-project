from django.conf import settings

class SessionCookieRouterMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Default session cookie name
        request.session_cookie_name = settings.SESSION_COOKIE_NAME

        path = request.path

        if path.startswith('/admin/'):
            settings.SESSION_COOKIE_NAME = 'admin_sessionid'
        elif path.startswith('/donor') or path.startswith('/donor_login'):
            settings.SESSION_COOKIE_NAME = 'donor_sessionid'
        elif path.startswith('/collector') or path.startswith('/collector_login'):
            settings.SESSION_COOKIE_NAME = 'collector_sessionid'
        else:
            settings.SESSION_COOKIE_NAME = 'sessionid'

        response = self.get_response(request)

        # Ensure response uses the correct cookie name
        if hasattr(request, 'session_cookie_name'):
            response.set_cookie(
                key=settings.SESSION_COOKIE_NAME,
                value=request.session.session_key,
                max_age=settings.SESSION_COOKIE_AGE,
                path='/',
                secure=settings.SESSION_COOKIE_SECURE or None,
                httponly=True,
                samesite='Lax',
            )

        return response
