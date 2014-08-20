#!/usr/bin/env python
#fileencoding=utf-8

import re
import time
import random
import string
import hashlib
import logging

from tornado.web import RequestHandler
from tornado.web import HTTPError
from tornado.escape import json_decode
from tornado.options import options

from bson.json_util import dumps, loads
from bson.objectid import ObjectId
from pymongo.errors import DuplicateKeyError

from lib.mail import send as send_mail

from lib import data_file

class BaseHandler(RequestHandler):
    allow_anony = False
    prefix = ''
    roles = [
        ('Admin', 100),
        ('Editor', 101),
        ('Subscriber', 102),
    ]

    def has_permission(self, path):
        if path  == '/users' or path.startswith('/user/'):
            return self.current_user and self.r % 100 == 0
        return self.current_user

    def prepare(self):
        uri = self.request.uri
        path = self.request.path
        user = self.current_user
        logging.info('user:%s is accessing %s', user, uri)

        if user is None and not self.allow_anony:
            self.redirect(self.get_login_url())
            return

        if not self.allow_anony and not self.has_permission(path):
            raise HTTPError(403)

    def get_login_url(self):
        return '/signin'

    def get_logout_url(self):
        return '/signout'

    def get_main_domain(self):
        return self.request.host.split(':')[0]

    def get_current_user(self):
        if options.debug:
            return dict(role=0, email='debug@local.host')

        user_json = self.get_secure_cookie("user")
        if user_json:
            user = json_decode(user_json)
            if user['login_sn'] == self.get_cookie("login_sn"):
                return user
            else:
                self.clear_cookie('user', domain=self.get_main_domain())
        else:
            self.clear_cookie('user', domain=self.get_main_domain())

        return None

    def has_argument(self, name):
        return name in self.request.arguments

    def write_error(self, status_code, **kwargs):
        if status_code == 403:
            self.write('You do not have previlege to view this page.')
            return

        return super(BaseHandler, self).write_error(status_code, **kwargs)

    def is_ajax_request(self):
        return self.request.headers.get("X-Requested-With") == "XMLHttpRequest"

    def dumps(self, obj):
        return dumps(obj, ensure_ascii=False, indent=4, sort_keys=True)

    def loads(self, s):
        return loads(s)

    def render(self, template, **kwargs):
        kwargs['navigation_bar'] = [i for i in [
            ('/users', 'users', 'Users'),
        ] if self.has_permission(i[0])]
        kwargs['site'] = self.db.site.find_one() or {'name': 'Shire'}

        return super(BaseHandler, self).render(template, **kwargs)


    @property
    def db(self):
        return self.application.db

    @property
    def img_prefix(self):
        return self.application.img_prefix

    @property
    def img_store_path(self):
        return self.application.img_store_path

    @property
    def m(self):
        return self.current_user['email']

    @property
    def r(self):
        return self.current_user['role']

#################################################################
## User Administration

def gen_salt():
    return ''.join(random.choice(string.letters) for i in xrange(16))

def hash_pwd(pwd, salt):
    return hashlib.sha1(pwd+'|'+salt).hexdigest()[:16]

class UserListHandler(BaseHandler):
    '''
    Define roles here
    '''
    def has_permission(self, url):
        ans = self.r % 100 == 0
        return ans and super(UserListHandler, self).has_permission(url)

    def get(self):
        users = list(self.db.user.find({'role':{'$in':[b for a,b in self.roles[1:]]}}, sort=[('_id', 1)]))

        role2sys = {b:a for a, b in self.roles}
        for i, user in enumerate(users):
            users[i]['role_str'] = role2sys[user['role']]

        self.render('user-list.html', users=users)

class UserHandler(BaseHandler):
    '''
    Define roles here
    '''
    def has_permission(self, url):
        ans = self.r % 100 == 0
        return ans and super(UserHandler, self).has_permission(url)

    def get(self, uid):
        user = self.db.user.find_one({'_id': ObjectId(uid)}) if uid else None
        roles = [r for r in self.roles[1:]]
        self.render('user-form.html', user=user, roles=roles)

    def post(self, uid):
        action = self.get_argument('action')
        logging.info('%s do %s to %s' % (self.m, action, uid))

        if action == 'save':
            self.save(uid)
        elif action == 'delete':
            self.delete(uid)

    def delete(self, uid):
        user = self.db.user.find_one({'_id': ObjectId(uid)}) if uid else {}
        user['valid'] = not user['valid'];
        self.db.user.save(user)
        self.write(dict(ok=1))

    def save(self, uid):
        mail = self.get_argument('mail')
        name = self.get_argument('name')
        pwd = self.get_argument('pwd', '')
        role = self.get_argument('role')
        salt = gen_salt()

        if re.match(r'^([0-9a-zA-Z]([-\.\w]*[0-9a-zA-Z])*@([0-9a-zA-Z][-\w]*[0-9a-zA-Z]\.)+[a-zA-Z]{2,9})$', mail) is None:
            self.write(dict(error_msg='invalid mail'))
            return

        #logging.info('uid:%s, mail:%s, pwd:%s, role:%s' % (uid, mail, '***', role))

        user = self.db.user.find_one({'_id': ObjectId(uid)}) if uid else {}
        insert = '_id' not in user

        user.update({
            'mail': mail,
            'name': name,
            'role': int(role),
        })

        if insert:
            plain_pwd = gen_salt()
            pwd = hash_pwd(plain_pwd, mail)

        if pwd:
            user.update({
                'salt':salt,
                'pwd': hash_pwd(pwd, salt),
            })

        if insert:
            user['created_at'] = time.time()
            user['created_by'] = self.m
            user['valid'] = True

        try:
            self.db.user.save(user)

            if insert:
                send_mail(mail,
                    'Your New Account At %s' % self.request.host,
                    'Hi, %s!<br>' % name +
                    'a new accont has been created for you. <br>' +
                    'Username: %s<br>' % mail +
                    'Password: %s<br>' % plain_pwd +
                    'Modify your password once you login. <br>' +
                    'Thanks.',
                    )

            self.write(dict(ok=1))
        except DuplicateKeyError:
            self.write(dict(error_msg='duplicate mail'))

class AccountHandler(BaseHandler):
    def get(self):
        user = self.db.user.find_one({'mail':self.m})
        assert user is not None

        role2sys = {b:a for a, b in self.roles}
        user['role_str'] = role2sys[user['role']] if user['role'] in role2sys else ''

        self.render('account.html', user=user)

    def post(self):
        user = self.db.user.find_one({'mail':self.m})
        assert user is not None

        name = self.get_argument('name')
        cpwd = self.get_argument('cpwd')
        npwd = self.get_argument('npwd')
        salt = gen_salt()

        if hash_pwd(cpwd, user['salt']) != user['pwd']:
            self.write(dict(error_msg='current password not correct.'))
            return

        user.update({
            'name': name,
            'pwd': hash_pwd(npwd, salt),
            'salt': salt,
        })
        self.db.user.save(user)
        self.write(dict(ok=1))

class SigninHandler(BaseHandler):
    allow_anony = True

    def get(self):
        if self.current_user is not None:
            self.redirect(self.get_next_url(self.current_user['role']))
            return

        self.render('signin.html')

    def post(self):
        mail = self.get_argument('mail')
        pwd = self.get_argument('pwd')

        user = self.db.user.find_one({'mail': mail})
        if user is None:
            self.write(dict(error_msg='user not exist.'))
            return
        if hash_pwd(pwd, user['salt']) != user['pwd']:
            self.write(dict(error_msg='password incorrect.'))
            return

        if not user['valid']:
            self.write(dict(error_msg='account banned.'))
            return

        user['last_login_time'] = time.time()
        self.db.user.save(user)

        cookie_user = {
            'email': mail,
            'role': user['role'],
            'login_sn': gen_salt(),
        }
        self.set_secure_cookie(
            "user",
            self.dumps(cookie_user),
            expires_days=7,
            domain=self.get_main_domain()
        )
        self.set_cookie(
            "login_sn",
            cookie_user['login_sn'],
            domain=self.get_main_domain()
        )

        self.write(dict(url=self.get_next_url(user['role'])))

    def get_next_url(self, role):
        referer = self.request.headers.get('Referer')
        if referer and referer != self.request.full_url():
            return referer

        return '/'

class SignoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie('user', domain=self.get_main_domain())
        self.clear_cookie('login_sn', domain=self.get_main_domain())
        self.redirect(self.request.headers.get('Referer', '/'))

class UploadHandler(BaseHandler):
    def check_xsrf_cookie(self):
        pass

    def post(self):
        f = self.request.files['file'][0]
        f_data = f['body']
        f_type = f['filename'].split('.')[-1]
        f_url = self.img_prefix + data_file.save(
            self.img_store_path, f_data, f_type)

        self.write(f_url)
        logging.info("%s uploaded img %s",
                     self.current_user['email'], f_url)
