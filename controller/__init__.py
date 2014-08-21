import time
import logging
import traceback
from datetime import datetime

from tornado.web import HTTPError
from bson.objectid import ObjectId

from handlers import BaseHandler

class HomeHandler(BaseHandler):
    def get(self):
        pages = list(self.db.page.find(fields={'url':1, 'title':1, 'viewed': 1}, sort=[('viewed', -1), ('_id', 1)]))
        self.render('page_list.html', pages=pages)

class AdminHandler(BaseHandler):
    def get(self):
        pages = list(self.db.page.find(fields={'url':1, 'title':1, 'viewed': 1}, sort=[('viewed', -1), ('_id', 1)]))
        self.render('_page_list.html', pages=pages)

class PageEditHandler(BaseHandler):
    def get(self, url):
        page = self.db.page.find_one({'url': url}) or {'url': url}
        self.render('_page_form.html', page=page)

    def create(self, url, title, content, viewed=0):
        page = {
            'url': url,
            'title': title,
            'content': content,
            'author': self.m,
            'modified': time.time(),
            'viewed': viewed,
        }
        return self.db.page.insert(page)

    def update(self, page, title, content):
        self.db.page.remove({'_id': page['_id']})
        pid = self.create(page['url'], title, content, page['viewed'])

        self.db.history.update({'redirect': page['_id']}, {'$set':{'redirect': pid}}, multi=True)
        page['redirect'] = pid
        self.db.history.insert(page)

    def post(self, url):
        title = self.get_argument('title')
        content = self.get_argument('content')

        page = self.db.page.find_one({'url': url})

        try:
            if not page:
                self.create(url, title, content)
            else:
                self.update(page, title, content)
        except Exception, e:
            error_msg = unicode(e) or traceback.format_exc()
            logging.warn(traceback.format_exc())
            self.write(dict(error_msg=error_msg))
            return
        self.write({'ok':1})

class PageHandler(BaseHandler):
    def get(self, url):
        page = self.db.page.find_one({'url': url})
        if not page:
            raise HTTPError(404)
        self.db.page.update({'_id': page['_id']}, {'$inc': {'viewed': 1}})
        self.render('page.html', page=page)

class HistoryListHandler(BaseHandler):
    def get(self, url):
        history = list(self.db.history.find({'url': url}, fields={'modified': 1, 'title': 1, 'author': 1}, sort=[('modified', -1)]))
        self.render('_history_list.html', history=history)

class HistoryPageHandler(BaseHandler):
    def get(self, _id):
        page = self.db.history.find_one({'_id': ObjectId(_id)})
        if not page:
            raise HTTPError(404)
        self.render('page.html', page=page)
