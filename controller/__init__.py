from tornado.web import HTTPError
from handlers import BaseHandler

class HomeHandler(BaseHandler):
    def get(self):
        pages = list(self.db.page.find(fields={'url':1, 'title':1}, sort=[('_id', 1)]))
        self.render('page_list.html', pages=pages)

class AdminHandler(BaseHandler):
    def get(self):
        self.db.page.ensure_index([('url',1)], unique=True)
        pages = list(self.db.page.find(fields={'url':1, 'title':1}, sort=[('_id', 1)]))
        self.render('_page_list.html', pages=pages)

class PageEditHandler(BaseHandler):
    def get(self, url):
        page = self.db.page.find_one({'url': url}) or {'url': url}
        site = self.db.site.find_one()
        home = site and site.get('home', '_') or '_'
        if home == url:
            page['home'] = True

        self.render('_page_form.html', page=page)

    def post(self, url):
        page = self.db.page.find_one({'url': url}) or {'url': url}
        title = self.get_argument('title')
        content = self.get_argument('content')
        home = self.get_argument('home', 'false') == 'true'

        page['title'] = title
        page['content'] = content
        self.db.page.save(page)

        site = self.db.site.find_one() or {}
        if home:
            site['home'] = url
        else:
            site.pop('home', None)
        self.db.site.save(site)

        self.write({'ok':1})

class PageHandler(BaseHandler):
    def get(self, url):
        page = self.db.page.find_one({'url': url})
        if not page:
            raise HTTPError(404)
        self.render('page.html', page=page)

