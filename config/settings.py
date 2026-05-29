import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-replace-in-production")
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
ALLOWED_HOSTS = [host.strip() for host in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if host.strip()]
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if origin.strip()]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'storages',
    'django_otp',
    'django_otp.plugins.otp_totp',
    'django_otp.plugins.otp_static',
    'accounts.apps.AccountsConfig',
    'league.apps.LeagueConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'league.middleware.CurrentUserMiddleware',
    'accounts.middleware.AdminSecurityMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

SITE_ID = 1

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'league.context_processors.active_branding',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# Configure database - SQLite by default, PostgreSQL if DATABASE_URL is set to postgres://
db_config = dj_database_url.config(
    default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
    conn_max_age=600,
)
# Only add ssl_require for PostgreSQL connections, not SQLite
if db_config.get('ENGINE') == 'django.db.backends.postgresql':
    db_config['CONN_HEALTH_CHECKS'] = True
    db_config['OPTIONS'] = {'sslmode': 'require'} if not DEBUG else {}

DATABASES = {
    'default': db_config
}


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

TIME_ZONE = 'America/Chicago'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME', '')
AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', '')
AWS_S3_CUSTOM_DOMAIN = os.getenv('AWS_S3_CUSTOM_DOMAIN', '')
AWS_DEFAULT_ACL = None
AWS_QUERYSTRING_AUTH = False
AWS_LOCATION_STATIC = os.getenv('AWS_LOCATION_STATIC', 'static')
AWS_LOCATION_MEDIA = os.getenv('AWS_LOCATION_MEDIA', 'media')

if AWS_STORAGE_BUCKET_NAME:
    static_domain = AWS_S3_CUSTOM_DOMAIN or f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
    STATIC_URL = f"https://{static_domain}/{AWS_LOCATION_STATIC}/"
    MEDIA_URL = f"https://{static_domain}/{AWS_LOCATION_MEDIA}/"
    STORAGES = {
        'default': {
            'BACKEND': 'config.storage_backends.MediaStorage',
        },
        'staticfiles': {
            'BACKEND': 'config.storage_backends.StaticStorage',
        },
    }

ADMIN_ALLOWED_IPS = [ip.strip() for ip in os.getenv('ADMIN_ALLOWED_IPS', '').split(',') if ip.strip()]
TRUST_X_FORWARDED_FOR = os.getenv('TRUST_X_FORWARDED_FOR', 'False').lower() == 'true'
OTP_TOTP_ISSUER = os.getenv('OTP_TOTP_ISSUER', 'Cherokee Bowling League')
OTP_ADMIN_SETUP_URL = '/accounts/admin-mfa/setup/'
OTP_ADMIN_VERIFY_URL = '/accounts/admin-mfa/verify/'

AWS_TEXTRACT_ENABLED = os.getenv('AWS_TEXTRACT_ENABLED', 'False').lower() == 'true'
AWS_TEXTRACT_SNS_TOPIC_ARN = os.getenv('AWS_TEXTRACT_SNS_TOPIC_ARN', '')
AWS_TEXTRACT_ROLE_ARN = os.getenv('AWS_TEXTRACT_ROLE_ARN', '')

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'league:dashboard'
LOGOUT_REDIRECT_URL = 'accounts:login'

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
