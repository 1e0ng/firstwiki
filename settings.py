#!/usr/bin/env python
#fileencoding=utf-8

import logging
from tornado.options import define

def define_app_options():
    define('debug', default=True)
    define('log_level', default=logging.INFO)
    define('cookie_secret', default='Overide this.')

    define('mongodb_host', default="127.0.0.1")
    define('mongodb_port', default=27017)
    define('mongodb_name', default="shire")

    define('port', default=8004)

    define('img_prefix', '/data/img/')
    define('img_store_path', 'data/img/')

    define('smtp_host', 'smtp.xx.com')
    define('smtp_username', 'user@domain')
    define('smtp_password', 'idontknow')


    try:
        import local_settings
    except ImportError:
        pass
