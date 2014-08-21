import time

from tornado.web import HTTPError
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

    def post(self, url):
        page = self.db.page.find_one({'url': url}) or {'url': url}
        title = self.get_argument('title')
        content = self.get_argument('content')

        page['title'] = title
        page['content'] = content
        page['author'] = self.m
        page['modified'] = time.time()
        self.db.page.save(page)

        self.write({'ok':1})

class PageHandler(BaseHandler):
    def get(self, url):
        page = self.db.page.find_one({'url': url})
        if not page:
            raise HTTPError(404)
        self.db.page.update({'_id': page['_id']}, {'$inc': {'viewed': 1}})
        self.render('page.html', page=page)
