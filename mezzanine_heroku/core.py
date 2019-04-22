import logging
import os

import dj_database_url
from django.test.runner import DiscoverRunner

MAX_CONN_AGE = 600

logger = logging.getLogger(__name__)


class HerokuDiscoverRunner(DiscoverRunner):
    """Test Runner for Heroku CI, which provides a database for you.
    This requires you to set the TEST database (done for you by settings().)"""

    def setup_databases(self, **kwargs):
        if not os.environ.get('CI'):
            raise ValueError(
                "The CI env variable must be set to enable this functionality.  WARNING:  "
                "This test runner will wipe all tables in the 'public' schema "
                "of the database it targets!"
            )
        self.keepdb = True
        return super(HerokuDiscoverRunner, self).setup_databases(**kwargs)

    def _wipe_tables(self, connection):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                    DROP TABLE (
                        SELECT
                            table_name
                        FROM
                            information_schema.tables
                        WHERE
                            table_schema = 'public'
                    ) CASCADE;
                """
            )

    def teardown_databases(self, old_config, **kwargs):
        self.keepdb = True
        for connection, old_name, destroy in old_config:
            if destroy:
                self._wipe_tables(connection)
        super(HerokuDiscoverRunner, self).teardown_databases(old_config, **kwargs)


def settings(config, *, db_colors=False, databases=True, test_runner=True, staticfiles=True, allowed_hosts=True, logging=True):

    # Database configuration.
    # TODO: support other database (e.g. TEAL, AMBER, etc, automatically.)
    if databases:
        # Integrity check.
        if 'DATABASES' not in config:
            config['DATABASES'] = {'default': None}

        conn_max_age = config.get('CONN_MAX_AGE', MAX_CONN_AGE)
            
        if db_colors:
            # Support all Heroku databases.
            # TODO: This appears to break TestRunner.
            for (env, url) in os.environ.items():
                if env.startswith('HEROKU_POSTGRESQL'):
                    db_color = env[len('HEROKU_POSTGRESQL_'):].split('_')[0]

                    logger.info('Adding ${} to DATABASES Django setting ({}).'.format(env, db_color))

                    config['DATABASES'][db_color] = dj_database_url.parse(url, conn_max_age=conn_max_age, ssl_require=True)

        if 'DATABASE_URL' in os.environ:
            logger.info('Adding $DATABASE_URL to default DATABASE Django setting.')

            # Configure Django for DATABASE_URL environment variable.
            config['DATABASES']['default'] = dj_database_url.config(conn_max_age=conn_max_age, ssl_require=True)

            logger.info('Adding $DATABASE_URL to TEST default DATABASE Django setting.')

            # Enable test database if found in CI environment.
            if 'CI' in os.environ:
                config['DATABASES']['default']['TEST'] = config['DATABASES']['default']

        else:
            logger.info('$DATABASE_URL not found, falling back to previous settings!')

    if test_runner:
        # Enable test runner if found in CI environment.
        if 'CI' in os.environ:
            config['TEST_RUNNER'] = 'mezzanine_heroku.HerokuDiscoverRunner'

    # Staticfiles configuration.
    if staticfiles:
        logger.info('Applying Heroku Staticfiles configuration to Django settings.')

        config['STATIC_ROOT'] = os.path.join(config['BASE_DIR'], 'static')
        config['STATIC_URL'] = '/static/'

        # Ensure STATIC_ROOT exists.
        os.makedirs(config['STATIC_ROOT'], exist_ok=True)

        # Insert Whitenoise Middleware.
        try:
            config['MIDDLEWARE_CLASSES'] = tuple(['whitenoise.middleware.WhiteNoiseMiddleware'] + list(config['MIDDLEWARE_CLASSES']))
        except KeyError:
            config['MIDDLEWARE'] = tuple(['whitenoise.middleware.WhiteNoiseMiddleware'] + list(config['MIDDLEWARE']))
        except Exception as e:
            raise e

        # WHitenoise storage config.
        try:
            config['STATICFILES_STORAGE'] = 'mezzanine_heroku.storage.StaticFilesStorage'
        except Exception as e:
            raise e

    if allowed_hosts:
        logger.info('Applying Heroku ALLOWED_HOSTS configuration to Django settings.')
        config['ALLOWED_HOSTS'] = ['*']

    if logging:
        logger.info('Applying Heroku logging configuration to Django settings.')

        config['LOGGING'] = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'verbose': {
                    'format': ('%(asctime)s [%(process)d] [%(levelname)s] ' +
                               'pathname=%(pathname)s lineno=%(lineno)s ' +
                               'funcname=%(funcName)s %(message)s'),
                    'datefmt': '%Y-%m-%d %H:%M:%S'
                },
                'simple': {
                    'format': '%(levelname)s %(message)s'
                }
            },
            'handlers': {
                'null': {
                    'level': 'DEBUG',
                    'class': 'logging.NullHandler',
                },
                'console': {
                    'level': 'DEBUG',
                    'class': 'logging.StreamHandler',
                    'formatter': 'verbose'
                }
            },
            'loggers': {
                'testlogger': {
                    'handlers': ['console'],
                    'level': 'INFO',
                }
            }
        }

    # Apply Heroku environment variables to Django/Mezzanine settings
    if 'SECRET_KEY' in os.environ:
        logger.info('Adding $SECRET_KEY to SECRET_KEY setting.')
        config['SECRET_KEY'] = os.environ['SECRET_KEY']

    if 'NEVERCACHE_KEY' in os.environ:
        logger.info('Adding $NEVERCACHE_KEY to NEVERCACHE_KEY setting.')
        config['NEVERCACHE_KEY'] = os.environ['NEVERCACHE_KEY']

    if 'SHOP_CURRENCY_LOCALE' in os.environ:
        logger.info('Adding $SHOP_CURRENCY_LOCALE to SHOP_CURRENCY_LOCALE setting.')
        config['SHOP_CURRENCY_LOCALE'] = os.environ['SHOP_CURRENCY_LOCALE']

    if 'STRIPE_API_KEY' in os.environ:
        logger.info('Adding $STRIPE_API_KEY to STRIPE_API_KEY setting.')
        config['STRIPE_API_KEY'] = os.environ['STRIPE_API_KEY']

    if 'AWS_ACCESS_KEY_ID' in os.environ:
        logger.info('Adding $AWS_ACCESS_KEY_ID to AWS_ACCESS_KEY_ID setting.')
        config['AWS_ACCESS_KEY_ID'] = os.environ['AWS_ACCESS_KEY_ID']

    if 'AWS_SECRET_ACCESS_KEY' in os.environ:
        logger.info('Adding $AWS_SECRET_ACCESS_KEY to AWS_SECRET_ACCESS_KEY setting.')
        config['AWS_SECRET_ACCESS_KEY'] = os.environ['AWS_SECRET_ACCESS_KEY']

    if 'AWS_STORAGE_BUCKET_NAME' in os.environ:
        logger.info('Adding $AWS_STORAGE_BUCKET_NAME to AWS_STORAGE_BUCKET_NAME setting.')
        config['AWS_STORAGE_BUCKET_NAME'] = os.environ['AWS_STORAGE_BUCKET_NAME']

        AWS_URL = 'https://s3.amazonaws.com/' + os.environ['AWS_STORAGE_BUCKET_NAME'] + '/';

        # logger.info('Adding $AWS_STORAGE_BUCKET_NAME to STATIC_URL setting.')
        # config['STATIC_URL'] = AWS_URL

        logger.info('Adding $AWS_STORAGE_BUCKET_NAME to MEDIA_URL setting.')
        config['MEDIA_URL'] = AWS_URL + 'static/'

        logger.info('Adding $AWS_STORAGE_BUCKET_NAME to ADMIN_MEDIA_PREFIX setting.')
        config['ADMIN_MEDIA_PREFIX'] = AWS_URL + 'admin/'

    if 'EMAIL_HOST' in os.environ:
        logger.info('Adding $EMAIL_HOST to EMAIL_HOST setting.')
        config['EMAIL_HOST'] = os.environ['EMAIL_HOST']

    if 'EMAIL_HOST_USER' in os.environ:
        logger.info('Adding $EMAIL_HOST_USER to EMAIL_HOST_USER setting.')
        config['EMAIL_HOST_USER'] = os.environ['EMAIL_HOST_USER']

    if 'EMAIL_HOST_PASSWORD' in os.environ:
        logger.info('Adding $EMAIL_HOST_PASSWORD to EMAIL_HOST_PASSWORD setting.')
        config['EMAIL_HOST_PASSWORD'] = os.environ['EMAIL_HOST_PASSWORD']

    if 'DEFAULT_FROM_EMAIL' in os.environ:
        logger.info('Adding $DEFAULT_FROM_EMAIL to DEFAULT_FROM_EMAIL setting.')
        config['DEFAULT_FROM_EMAIL'] = os.environ['DEFAULT_FROM_EMAIL']


    # Apply the theme, when using the Deploy to Heroku button[1] with the Free Mezzanine themes[2]
    # [1] https://github.com/jackvz/mezzanine-cms-on-heroku
    # [2] https://github.com/thecodinghouse/mezzanine-themes
    if 'THEME' in os.environ:
        if os.environ['THEME'].lower() == 'flat' or os.environ['THEME'].lower() == 'moderna' or os.environ['THEME'].lower() == 'nova' or os.environ['THEME'].lower() == 'solid':
            logger.info('Adding theme $THEME.')
            config['INSTALLED_APPS'] = ('free_theme_' + os.environ['THEME'].lower(),) + config['INSTALLED_APPS']
