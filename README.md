Sentry smart mailer
=============

A sentry plugin that adds some more logic on error notification rules.
By default Sentry sends an email when an error is first received and
when the error gets received after it was marked as resolved.

By enabling the plugin you will get an email notification if the same error gets
received frequently (1 email after 10, another after 100 and so on with log 10).

Also it will resend an email when the same error 'reappears' after 1 months.


Also, it integrates with the [sentry_defcon](https://github.com/tbarbugli/sentry_defcon) plugin so that when sentry is receiving lots
of errors, it will stop sending email until the error/rate decrease to a safer level
(aka it stops spamming your inbox).