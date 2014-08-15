#!/usr/bin/env python
#encoding=utf-8

import os
import logging

from pymongo import MongoClient

from tornado.httpserver import HTTPServer
from tornado.web import Application
from tornado.ioloop import IOLoop
from tornado.options import options, parse_command_line
from jinja2 import ChoiceLoader, FileSystemLoader

import settings
from lib.template import JinjaLoader
from lib.misc import install_tornado_shutdown_handler
from lib.request_handlers import SmartStaticFileHandler, MultiFileFinder
from lib.request_handlers import ResourceHandler

from handlers import BaseHandler, UploadHandler


class ShireWeb(object):
    def get_settings(self, proj_template_path, proj_static_paths):
        settings.define_app_options()
        parse_command_line(final=True)

        self_dir_path = os.path.abspath(os.path.dirname(__file__))
        loader = ChoiceLoader([
            FileSystemLoader(proj_template_path),
            FileSystemLoader(os.path.join(self_dir_path, 'templates')),
            ])

        SmartStaticFileHandler.file_finder = MultiFileFinder(
            proj_static_paths,
            os.path.join(self_dir_path, 'static'))

        return {
            'template_loader': JinjaLoader(loader=loader, auto_escape=False),
            'debug': options.debug,
            'cookie_secret': options.cookie_secret,
            'xsrf_cookies': True,

            'static_path': u'/static/',
            'static_handler_class': SmartStaticFileHandler,
        }

    def __init__(self, routes, template_path, proj_static_paths=[],
                 **more_settings):
        the_settings = self.get_settings(template_path, proj_static_paths)
        the_settings.update(more_settings)

        routes.extend([
            (r'/upload', UploadHandler),
            (r"/data/img/(.*)", ResourceHandler,
             {
                 "valid_file_types": ["jpg", "png", "wmf"],
                 "path": options.img_store_path
             }),
        ])

        self.app = Application(routes, **the_settings)
        self.app.db = self.setup_db()

        self.app.img_prefix = options.img_prefix
        self.app.img_store_path = options.img_store_path

    def setup_db(self):
        host = options.mongodb_host
        port = options.mongodb_port
        name = options.mongodb_name
        logging.info("connecting to database %s:%s, %s ...", host, port, name)
        client = MongoClient(host, port)
        return client[name]

    def run(self):
        logging.info('Runing at port %s in %s mode',
                     options.port, 'debug' if options.debug else 'production')
        server = HTTPServer(self.app, xheaders=True)
        server.listen(options.port)

        install_tornado_shutdown_handler(IOLoop.instance(), server)
        logging.info('Good to go!')

        IOLoop.instance().start()
        logging.info('Exiting...waiting for background jobs done...')
        logging.info('Done. Bye.')


if __name__ == "__main__":
    class _HelloworldHandler(BaseHandler):
        def get(self):
            self.render('hello.html', word='hello')

    routes = [
        (r'/', _HelloworldHandler),
        ]
    server = ShireWeb(routes, 'templates')
    server.run()
