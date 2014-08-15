#!/usr/bin/env python
#fileencoding=utf-8
'''
various request handlers
'''

import os
import re
from tornado.web import StaticFileHandler
from tornado.web import HTTPError

import data_file


class FileFinder(object):
    def get_absolute_path(self, path):
        raise NotImplementedError()

    def validate_absolute_path(self, path):
        '''
        take care of the fs side problem
        '''
        raise NotImplementedError()


class MultiFileFinder(FileFinder):
    def __init__(self, roots, default_root):
        self.roots = tuple(roots)
        self.default_root = default_root

    def get_absolute_path(self, path):
        for root in self.roots:
            absolute_path = os.path.abspath(os.path.join(root, path))
            if os.path.exists(absolute_path):
                return absolute_path
        return os.path.abspath(os.path.join(self.default_root, path))

    def validate_absolute_path(self, absolute_path):
        for root in (self.default_root,) + self.roots:
            if not (absolute_path + os.path.sep).startswith(root):
                continue
            return
        raise HTTPError(403, "%s is not in root static directory",
                        self.path)


class SmartStaticFileHandler(StaticFileHandler):
    '''
    '''
    file_finder = None

    def initialize(self, path):
        self.root = u'<bad root>'

    @classmethod
    def get_absolute_path(cls, root, path):
        return cls.file_finder.get_absolute_path(path)

    def validate_absolute_path(self, root, absolute_path):
        self.file_finder.validate_absolute_path(absolute_path)

        if not os.path.exists(absolute_path):
            raise HTTPError(404)
        if not os.path.isfile(absolute_path):
            raise HTTPError(403, "%s is not a file", self.path)
        return absolute_path


class ResourceHandler(StaticFileHandler):
    """
    """
    def initialize(self, path, valid_file_types):
        super(ResourceHandler, self).initialize(path, None)
        self.valid_file_types = valid_file_types
        pattern_str = "^[a-f0-9]{32}\.(?:%s)$" % '|'.join(valid_file_types)
        self.path_reg_pattern = re.compile(pattern_str, re.I)

    def get_current_user(self):
        return None

    def get(self, filename, include_body=True):
        if not self.path_reg_pattern.match(filename):
            raise HTTPError(404)
        return super(ResourceHandler, self).get(filename, include_body)

    @classmethod
    def get_absolute_path(cls, root, path):
        '''
        override
        '''
        abspath = os.path.abspath(data_file.fullpath(root, path))
        return abspath

    def get_cache_time(self, path, modified, mime_type):
        '''
        never expires
        '''
        return 86400 * 365 * 99

    @classmethod
    def make_static_url(cls, settings, path):
        raise NotImplementedError()

    @classmethod
    def get_version(cls, settings, path):
        raise NotImplementedError()
