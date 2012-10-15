from datetime import datetime
import pickle
import sentry_smart_mailer
from sentry.models import GroupMeta
from sentry.plugins import register
from sentry.plugins import unregister
from sentry.plugins.sentry_mail.models import MailProcessor
from sentry.utils.cache import Lock, UnableToGetLock
from sentry_smart_mailer.switches import SwitchManager


LAST_MAIL_SENT_AT_KEY = '_LAST_MAIL_SENT_AT'
DEFAULT_VALUE = pickle.dumps([])

def get_last_email_sent_at_obj(group):
    meta, c = GroupMeta.objects.get_or_create(
        group=group,
        key=LAST_MAIL_SENT_AT_KEY,
        defaults=dict(value=DEFAULT_VALUE)
    )
    return meta

def get_last_email_sent_at(group):
    meta = get_last_email_sent_at_obj(group)
    return pickle.loads(meta.value)

def set_last_email_sent_at(group, value):
    meta = get_last_email_sent_at_obj(group)
    meta.value = pickle.dumps(value)
    meta.save()

class SmartMailer(MailProcessor):
    title = 'Smart mailer'
    slug = 'sentry_smart_mailer'
    conf_key = 'sentry_smart_mailer'
    version = sentry_smart_mailer.VERSION
    author = "Tommaso Barbugli"
    author_url = "https://github.com/tbarbugli/sentry_smart_mailer"

    def should_notify(self, group):
        return SwitchManager.send_email(group=group, logger_name=group.logger)

    def post_process(self, group, event, is_new, is_sample, **kwargs):
        lock_key = 'lock_mail:%s' % group.id
        try:
            with Lock(lock_key, timeout=0.5):
                self._post_process(group, event, is_new, is_sample, **kwargs)
        except UnableToGetLock:
            pass

    def _post_process(self, group, event, is_new, is_sample, **kwargs):
        if not self.should_notify(group):
            return
        try:
            email_sent_at = list(get_last_email_sent_at(group))
        except:
            email_sent_at = []
        self.notify_users(group, event)
        email_sent_at.append((datetime.now(), group.times_seen or 1))
        set_last_email_sent_at(group, email_sent_at[-5:])

register(SmartMailer)
unregister(MailProcessor)
