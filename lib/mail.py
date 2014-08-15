#!/usr/bin/env python
#fileencoding=utf-8

import logging
import smtplib
from email.mime.text import MIMEText

from tornado.options import options


class MailError(Exception):
    pass


def send(to, subject, content):
    msg = MIMEText(content, _subtype="html", _charset="utf-8")

    msg['Subject'] = subject
    msg['From'] = options.smtp_username
    msg['To'] = to

    s = None
    try:
        s = smtplib.SMTP_SSL(options.smtp_host)
        s.login(options.smtp_username, options.smtp_password)
        s.sendmail(msg['From'], [to], msg.as_string())
    except Exception as ex:
        logging.warning("send mail failed. detail: %s", str(ex))
        raise MailError(str(ex))
    finally:
        if s:
            s.quit()
