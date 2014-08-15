import time
import logging
from functools import partial

from tornado.ioloop import IOLoop
from tornado.ioloop import PeriodicCallback

from scaffold import Scaffold


class Service(Scaffold):
    def __init__(self, interval=1):
        '''
        inteval is in seconds
        '''
        super(Service, self).__init__()
        self.interval = interval * 1000
        self.periodicalCb = None

    def stop(self):
        if self.periodicalCb:
            self.periodicalCb.stop()

    def run(self, *args, **kwargs):
        super(Service, self).run(*args, **kwargs)
        self.periodicalCb = PeriodicCallback(
            partial(super(Service, self).run, *args, **kwargs),
            self.interval, IOLoop.instance())
        self.periodicalCb.start()
        IOLoop.instance().start()

    def main(self):
        '''
        Subclass this method
        '''
        logging.error('Subclass main method... %s' % time.clock())


if __name__ == '__main__':
    service = Service()
    try:
        service.run()
    except KeyboardInterrupt:
        service.stop()
