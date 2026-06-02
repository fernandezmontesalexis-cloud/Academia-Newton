import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

load_dotenv()  # lee .env en desarrollo local

BASE_DIR = Path(__file__).resolve().parent.parent

# ── SEGURIDAD ──────────────────────────────────────────────────────────────
# En producción: variable de entorno SECRET_KEY obligatoria en Render
# En desarrollo local: fallback al valor de desarrollo (nunca usar en producción)
SECRET_KEY = os.environ.get('SECRET_KEY')

# En producción: DEBUG=False (variable de entorno en Render)
# En desarrollo local: True por defecto, sin necesidad de configurar nada
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

# En producción: dominio asignado por Render (ej. academia-newton.onrender.com)
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Dominios de confianza para formularios POST en producción (CSRF)
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',')
    if origin.strip()
]

# ── APPS ───────────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'web',
]

# ── MIDDLEWARE ─────────────────────────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',   # sirve CSS/JS en producción
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'web.middleware.PerfilActivoMiddleware',
    'web.middleware.NoCacheMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'web/templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ── BASE DE DATOS ──────────────────────────────────────────────────────────
# En producción: Render inyecta DATABASE_URL automáticamente al conectar PostgreSQL
# En desarrollo local: usa SQLite si DATABASE_URL no está definida (sin cambio)
DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# ── VALIDACIÓN DE CONTRASEÑAS ──────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ── INTERNACIONALIZACIÓN ───────────────────────────────────────────────────
LANGUAGE_CODE = 'es-pe'
TIME_ZONE     = 'America/Lima'
USE_I18N      = True
USE_TZ        = True

# ── ARCHIVOS ESTÁTICOS ─────────────────────────────────────────────────────
STATIC_URL       = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'web/static']
STATIC_ROOT      = BASE_DIR / 'staticfiles'

# WhiteNoise: comprime y cachea estáticos automáticamente en producción
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ── CONFIGURACIÓN GENERAL ──────────────────────────────────────────────────
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── AUTENTICACIÓN Y SESIÓN ─────────────────────────────────────────────────
LOGIN_URL           = '/'
LOGIN_REDIRECT_URL  = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

SESSION_COOKIE_AGE        = 1800   # 30 minutos de inactividad
SESSION_SAVE_EVERY_REQUEST = True  # reinicia el contador con cada acción
