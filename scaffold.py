#!/usr/bin/env python
#fileencoding=utf-8

import time
import logging

from tornado.options import options, parse_command_line
from pymongo import MongoClient

import settings

class Scaffold(object):
    def __init__(self):
        self.setup()

    def setup(self):
        settings.define_app_options()
        parse_command_line(final=True)

        self.db = self.setup_db()

    def setup_db(self):
        logging.info('Runing in %s mode' % ('debug' if options.debug else 'production'))
        logging.debug('DEBUG')

        db = MongoClient(options.mongodb_host, options.mongodb_port)[options.mongodb_name]
        logging.info('Connected to db %s ' % options.mongodb_host)

        return db

    def timeit(self, fn, *args, **kwargs):
        t1 = time.clock()
        ret = fn(*args, **kwargs)
        t2 = time.clock()
        return t2 - t1, ret

    def run(self, *args, **kwargs):
        t, r = self.timeit(self.main, *args, **kwargs)
        logging.info('Cost %s seconds.' % t)
        return r

    def main(self, *args, **kwargs):
        assert True == False
