#!/usr/bin/env python
#fileencoding=utf-8

import random
import string
import hashlib
import time
import signal
from uuid import uuid4

def rand_string(desired_len):
    sr = random.SystemRandom()
    printable = string.letters + string.digits
    printable_len = len(printable)
    chars = [printable[sr.randint(0, printable_len - 1)] for _ in
             range(desired_len)]
    return ''.join(chars)


def uuid_rand():
    '''
    prefer to rand_string
    '''
    return uuid4().hex


def sha1_hash(value):
    sha1 = hashlib.sha1()
    sha1.update(value)
    digest = sha1.hexdigest()
    return digest


def install_tornado_shutdown_handler(ioloop, server, logger=None):
    # see https://gist.github.com/mywaiting/4643396 for more detail
    if logger is None:
        import logging
        logger = logging

    def _sig_handler(sig, frame):
        logger.info("Signal %s received. Preparing to stop server.", sig)
        ioloop.add_callback(shutdown)

    def shutdown():
        logger.info("Stopping http server...")
        server.stop()

        MAX_WAIT_SECONDS_BEFORE_SHUTDOWN = 3
        logger.info("Will shutdown in %s seconds",
                    MAX_WAIT_SECONDS_BEFORE_SHUTDOWN)
        deadline = time.time() + MAX_WAIT_SECONDS_BEFORE_SHUTDOWN

        def stop_loop():
            now = time.time()
            if now < deadline and (ioloop._callbacks or ioloop._timeouts):
                ioloop.add_timeout(now + 1, stop_loop)
                logger.debug("Waiting for callbacks and timeouts in IOLoop...")
            else:
                ioloop.stop()
                logger.info("Server is shutdown")

        stop_loop()

    signal.signal(signal.SIGTERM, _sig_handler)
    signal.signal(signal.SIGINT, _sig_handler)
