#!/usr/bin/env python
#fileencoding=utf-8

from jinja2 import Environment
from jinja2 import FileSystemLoader
from jinja2 import BytecodeCache

def guess_autoescape(template_name):
    if template_name is None or '.' not in template_name:
        return False
    ext = template_name.rsplit('.', 1)[1]
    return ext in ('html', 'htm', 'xml')

class MemoryBytecodeCache(BytecodeCache):
    # TODO: consider to make a Redis based cache

    def __init__(self):
        self.cache = {}

    def load_bytecode(self, bucket):
        code = self.cache.get(bucket.key)
        if code:
            bucket.bytecode_from_string(code)

    def dump_bytecode(self, bucket):
        self.cache[bucket.key] = bucket.bytecode_to_string()

    def clear(self):
        self.cache = {}


class JinjaLoader(object):
    def __init__(self, **kwargs):
        super(JinjaLoader, self).__init__()
        auto_reload = kwargs.get('debug', True)
        loader = kwargs.get('loader')
        if not loader:
            root_path = kwargs.get('root_path')
            if not root_path:
                assert 'no loader could be selected!'
            loader = FileSystemLoader(root_path)
        auto_escape = kwargs.get('auto_escape', guess_autoescape)
        self.env = Environment(loader=loader,
                               autoescape=auto_escape,
                               extensions=['jinja2.ext.autoescape'],
                               trim_blocks=True,
                               lstrip_blocks=True,
                               cache_size=-1,  # no clean-up
                               bytecode_cache=MemoryBytecodeCache(),
                               auto_reload=auto_reload)

        additional_globals = {
            'ord': ord,
            'chr': chr,
            'unichr': unichr,
        }
        self.env.globals.update(additional_globals)

    def load(self, name, parent_path=None):
        return JinjaTemplate(self.env.get_template(name))

    def reset(self):
        '''Reset the cache of compiled templates, required
           in debug mode.
        '''
        self.env.cache.clear()


class JinjaTemplate(object):
    def __init__(self, template):
        self.template = template

    def generate(self, **kwargs):
        # jinja uses unicode internally but tornado uses utf string
        return self.template.render(**kwargs).encode('utf-8')
