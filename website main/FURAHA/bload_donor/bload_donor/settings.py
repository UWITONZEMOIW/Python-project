

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-ccdj(556!v#h*g#!q#ig+r4x7i5ail%$#(qa430s($l8@qi7c%'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []
# settings.py

SITE_URL = "http://127.0.0.1:8000"

# from django.urls import reverse_lazy
# LOGIN_URL = reverse_lazy('collector_login')



# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'bload_donor_app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',  # ← must be early
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'bload_donor_app.middleware.session_router.SessionCookieRouterMiddleware',
    'bload_donor_app.middleware.custom_session_middleware.MultiSessionMiddleware',  

]

ROOT_URLCONF = 'bload_donor.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Or your actual path
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'bload_donor_app.context_processors.urgency_banner',
                # 'bload_donor_app.context_processors.donor_counter',
                'bload_donor_app.context_processors.donor_counter_number', 
                
            ],
        },
    },
]

WSGI_APPLICATION = 'bload_donor.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': 'bload_donation',
#         'USER': 'boringo',
#         'PASSWORD': 'boringo@123',
#         'HOST': 'localhost',  # or your server IP
#         'PORT': '3306',        # default MySQL port
#         'OPTIONS': {
#             'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
#         }
#     }
# }

SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # or cache if configured
# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / "static"]


# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Sessions last for 2 weeks (default)
SESSION_COOKIE_AGE = 1209600  # in seconds (2 weeks)

# Close the browser to expire session if not using "Remember Me"
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Whether session data is saved to the database on every request
SESSION_SAVE_EVERY_REQUEST = False

# Use secure cookie in production (HTTPS only)
SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS

#=======================settings for the email sending========================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'dboringo3@gmail.com'
EMAIL_HOST_PASSWORD = 'abbv vodh cvmv ofxf'  # not your real password!
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER


# AUTH_USER_MODEL = 'yourapp.Collector'
# AUTH_USER_MODEL = 'bload_donor_app.Collector'  # Uncomment if using custom user model
# AUTH_USER_MODEL = 'bload_donor_app.Donor'  # Uncomment if using custom user model