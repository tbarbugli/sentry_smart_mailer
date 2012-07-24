from datetime import timedelta, datetime
import math
from sentry.plugins import plugins

_switches = {}

class RegisteringMetaClass(type):
    '''
    Registers switches classes
    '''
    def __new__(cls, classname, bases, classDict):
        class_definition = type.__new__(cls, classname, bases, classDict)
        if not classDict.get("__metaclass__"):
            _switches[classname] = class_definition
        return class_definition

    @classmethod
    def should_send(cls, *args, **kwargs):
        raise NotImplementedError

class Switch():
    __metaclass__ = RegisteringMetaClass

class SwitchManager():

    @classmethod
    def send_email(cls, *args, **kws):
        return all([s.should_send(*args, **kws) for s in _switches.values()])

class IgnoreLoggerSwitch(Switch):
    """
    Does not send email for loggers in SKIP_LOGGERS
    """
    SKIP_LOGGERS = ('http404',)

    @classmethod
    def should_send(cls, *args, **kwargs):
        logger_name = kwargs['logger_name']
        return not logger_name in cls.SKIP_LOGGERS

class WakeUpSwitch(Switch):
    """
    resends an email for not new messages if WAKEUP_PERIOD is passed
    or if the message was received many times (log base 10 times)
    """
    WAKEUP_PERIOD = 30 * 24 * 3600

    @classmethod
    def check_increase_threshold(cls, prev, current):
        """
        uses log 10 to determine if we have seen enough messages to issue
        another notification (1,10,100,1000,10000 ...)
        """
        return int(math.log(current,10) - math.log(prev,10)) >= 1

    @classmethod
    def should_send(cls, *args, **kwargs):
        group = kwargs['group']
        ret = cls._should_send(*args, **kwargs)
        if ret and group.times_seen > 1:
            #hack to change the mail subject when error is recurrent
            group.project.name = "RECURRENT %s" % group.project.name
        return ret

    @classmethod
    def _should_send(cls, *args, **kwargs):
        group = kwargs['group']
        last_email_sent = group.last_email_sent
        if not last_email_sent or not isinstance(last_email_sent, list):
            return True
        last_email_sent_at, last_email_sent_count = last_email_sent[-1]
        now = datetime.now()
        if not last_email_sent_at:
            return True
        if last_email_sent_at + timedelta(seconds= cls.WAKEUP_PERIOD) < now:
            return True
        if cls.check_increase_threshold(last_email_sent_count, group.times_seen):
            return True
        return False

class ThrottleSwitch(Switch):
    """
    Stop sending emails when Defcon is @ 1
    """

    @classmethod
    def should_send(cls, *args, **kwargs):
        try:
            defcon = plugins.get('sentry_defcon')
        except KeyError:
            return True
        return not defcon.is_cocked()
