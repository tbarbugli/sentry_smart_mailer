from datetime import datetime
import sentry_smart_mailer
from sentry_smart_mailer.switches import SwitchManager
from sentry.plugins import register
from sentry.plugins import unregister
from sentry.plugins.sentry_mail.models import MailProcessor

class SmartMailer(MailProcessor):
    title = 'Smart mailer'
    slug = 'sentry_smart_mailer'
    conf_key = 'sentry_smart_mailer'
    version = sentry_smart_mailer.VERSION
    author = "Tommaso Barbugli"
    author_url = "https://github.com/tbarbugli/sentry_smart_mailer"

    def should_notify(self, group, event):
        notify = SwitchManager.send_email(group=group, logger_name=group.logger)
        # base_notification = False and super(SmartMailer, self).should_notify(group, event)
        import logging
        # logging.warning('%r %r' % (notify, base_notification))
        return notify

    def post_process(self, group, event, is_new, is_sample, **kwargs):
        if not self.should_notify(group, event):
            return
        try:
            email_sent_at = list(group.last_email_sent)
        except:
            email_sent_at = []
        self.notify_users(group, event)
        email_sent_at.append((datetime.now(), group.times_seen or 1))
        group.last_email_sent = email_sent_at[-5:]
        group.save()

register(SmartMailer)
unregister(MailProcessor)