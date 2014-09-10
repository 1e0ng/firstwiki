import time
import json
import logging
import traceback

from tornado.web import HTTPError
from bson.objectid import ObjectId
import markdown

from handlers import BaseHandler

class HomeHandler(BaseHandler):
    def get(self):
        pages = list(self.db.page.find({'deleted': False}, fields={'url':1, 'title':1, 'viewed': 1}))
        orders = {x['pid']: x['order'] for x in self.db.order.find()}
        pages.sort(key=lambda x: (orders.get(x['_id'], 0), -long(str(x['_id']), 16)))
        self.render('page_list.html', pages=pages)

class AdminHandler(BaseHandler):
    def get(self):
        pages = list(self.db.page.find(fields={'url':1, 'title':1, 'viewed': 1, 'deleted':1}))
        orders = {x['pid']: x['order'] for x in self.db.order.find()}
        pages.sort(key=lambda x: (orders.get(x['_id'], 0), -long(str(x['_id']), 16)))
        self.render('_page_list.html', pages=pages)

    def post(self):
        m =  self.get_argument('m')
        m = json.loads(m)
        self.db.order.drop()
        orders = [{'pid': ObjectId(k), 'order': v} for k, v in m.items()]
        self.db.order.insert(orders)
        self.write({'ok':1})

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
            'deleted': False,
        }
        return self.db.page.insert(page)

    def update(self, page, title, content, new_url):
        self.db.page.remove({'_id': page['_id']})
        pid = self.create(new_url, title, content, page['viewed'])

        self.db.history.update({'redirect': page['_id']}, {'$set':{'redirect': pid}}, multi=True)
        page['redirect'] = pid
        self.db.history.insert(page)

    def delete(self, url):
        page = self.db.page.find_one({'url': url})
        deleted = not page['deleted']
        self.db.page.update({'_id':page['_id']}, {'$set':{'deleted': deleted}})

    def post(self, url):
        action = self.get_argument('action')
        try:
            if action == 'delete':
                self.delete(url)
            else:
                title = self.get_argument('title')
                content = self.get_argument('content')
                new_url = self.get_argument('new_url')

                if new_url != url:
                    if self.db.page.find_one({'url': new_url}):
                        raise Exception('URL duplicated')

                page = self.db.page.find_one({'url': url})

                if not page:
                    self.create(url, title, content)
                else:
                    self.update(page, title, content, new_url)
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
        page['content'] = markdown.markdown(page['content'])
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
        page['content'] = markdown.markdown(page['content'])
        self.render('page.html', page=page)
