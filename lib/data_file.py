#!/usr/bin/env python
#fileencoding=utf-8

import os
import md5
import shutil


_builtin_open = open


def path_prefix(filename):
    return os.path.join(filename[:2], filename[2:4])


def fullpath(root, filename):
    return os.path.join(root, path_prefix(filename), filename)


def open(root, filename):
    path = os.path.join(root, path_prefix(filename), filename)

    return _builtin_open(path, "rb")


def ensure_dir_exist(path):
    if not os.path.exists(path):
        os.makedirs(path)


def save(root, content, ext=""):
    digest = md5.new(content).hexdigest()
    pathname = fullpath(root, digest)
    if ext:
        pathname += "." + ext

    abspath = os.path.abspath(pathname)
    if os.path.exists(abspath):
        return os.path.basename(abspath)

    dirname = os.path.dirname(abspath)
    ensure_dir_exist(dirname)

    tmp_abspath = '{}.tmp.{}'.format(abspath, os.getpid())
    with _builtin_open(tmp_abspath, "wb") as fobj:
        fobj.write(content)
    shutil.move(tmp_abspath, abspath)

    return os.path.basename(abspath)
