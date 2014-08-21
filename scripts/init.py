#!/usr/bin/env python
#fileencoding=utf-8

import time
import logging
import hashlib

from scaff import Scaffold

def hash_pwd(pwd, salt):
    return hashlib.sha1(pwd+'|'+salt).hexdigest()[:16]

class Runner(Scaffold):
    def main(self):
        logging.info('Start to build index...')
        self.db.page.ensure_index([('url', 'hashed')], unique=True)
        self.db.user.ensure_index([('mail', 'hashed')], unique=True)
        self.db.history.ensure_index([('redirect', 'hashed')])
        self.db.history.ensure_index([('url', 'hashed')])
        logging.info('Indexes built.')

        root_user = self.db.user.find_one({'mail': 'root@root'})
        if not root_user:
            root_user = {
                "name": "root",
                "created_at": time.time(),
                "created_by": "sys",
                "valid": True,
                "role": 0,
                "mail": "root@root",
                "salt": "dzwOrPqGdgOwBqyV",
            }
            root_user['pwd'] = hash_pwd(hash_pwd('802debaed8f55ffc', root_user['mail']), root_user['salt'])
            self.db.user.save(root_user)
            logging.info('Added root user.')

        site = self.db.site.find_one() or {}
        if 'name' not in site:
            site.update({
                'name': 'First Wiki',
            })
            self.db.site.save(site)
            logging.info('Added site.')


if __name__ == '__main__':
    Runner().run()
