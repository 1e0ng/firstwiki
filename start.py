#!/usr/bin/env python
#encoding=utf-8
import os

from shireweb import ShireWeb

if __name__ == "__main__":
    routes = [
        (r'/', 'controller.HomeHandler'),

        (r'/_', 'controller.AdminHandler'),
        (r'/_/users/?', 'handlers.UserListHandler'),
        (r'/_/user/?(\w*)', 'handlers.UserHandler'),
        (r'/_/account', 'handlers.AccountHandler'),
        (r'/_(/.*)', 'controller.PageEditHandler'),

        (r'/signin', 'handlers.SigninHandler'),
        (r'/signout', 'handlers.SignoutHandler'),

        (r'(.*)', 'controller.PageHandler'),
        ]
    template_path = os.path.abspath(__file__ + '/../templates')
    server = ShireWeb(routes, template_path)
    server.run()
