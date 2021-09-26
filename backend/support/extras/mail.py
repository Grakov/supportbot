import subprocess
from subprocess import Popen, PIPE, CalledProcessError

from django.core.mail import EmailMessage
from django.template.loader import get_template
from django.core.mail.backends import smtp, base

from support.models import Settings


class SendmailEmailBackend(base.BaseEmailBackend):
    """
    Sendmail backend
    Based on https://github.com/perenecabuto/django-sendmail-backend/
    Backend uses -f parameter of sendmail, so check webserver user to be in /etc/mail/trusted-users
    """
    def send_messages(self, email_messages) -> int:
        if not email_messages:
            return 0

        num_sent = 0
        for message in email_messages:
            if self._send(message):
                num_sent += 1
        return num_sent

    def _send(self, email_message: EmailMessage) -> int:
        recipients = email_message.recipients()
        if not recipients:
            return False

        from_email = email_message.from_email
        if from_email is None or from_email == '':
            raise ValueError('Missing sender email: from_email should be set')

        sendmail_binary = Settings.get_value_by_key('system.mail.sendmail_binary', None)
        # trying to find sendmail binary
        if sendmail_binary is None:
            try:
                output = subprocess.check_output(['whereis', '-b', 'sendmail'], universal_newlines=True)
                sendmail_binary = output.split("\n")[0].split()[1]
            except (CalledProcessError, IndexError):
                sendmail_binary = '/usr/sbin/sendmail'

        # sending message
        try:
            # -t: Read message for recipients
            ps = Popen([sendmail_binary] + ['-f', f'\"{from_email}\"'] + recipients, stdin=PIPE, stderr=PIPE)
            ps.stdin.write(email_message.message().as_bytes())
            (stdout, stderr) = ps.communicate()
        except Exception:
            if not self.fail_silently:
                raise
            return False
        if ps.returncode:
            if not self.fail_silently:
                error = stderr if stderr else stdout
                raise Exception('send_messages failed: %s' % error)
            return False
        return True


def send_mail(subject: str, to: list, template: str, context: dict, from_email=None):
    # TODO add system.from_email param

    method = Settings.get_value_by_key('system.mail.transport', 'sendmail')
    if method == 'smtp':
        smtp_host = Settings.get_value_by_key('system.mail.smtp_host', 'localhost')
        smtp_port = Settings.get_value_by_key('system.mail.smtp_port', 25)
        smtp_username = Settings.get_value_by_key('system.mail.smtp_username', '')
        smtp_password = Settings.get_value_by_key('system.mail.smtp_password', '')
        smtp_tls = Settings.get_value_by_key('system.mail.smtp_tls', False)
        smtp_ssl = Settings.get_value_by_key('system.mail.smtp_ssl', False)
        if smtp_tls and smtp_ssl:
            smtp_ssl = False

        connection = smtp.EmailBackend(host=smtp_host, port=smtp_port, username=smtp_username, password=smtp_password,
                                       use_tls=smtp_tls, use_ssl=smtp_ssl, fail_silently=False)
    elif method == 'sendmail':
        connection = SendmailEmailBackend(fail_silently=False)
    else:
        raise ValueError(f"Invalid value for system.mail.transport setting: {method}")

    if from_email is None:
        from_email = Settings.get_value_by_key('system.mail.default_from', '')

    message = EmailMessage(
        subject=subject,
        body=get_template(template).render(context=context),
        from_email=from_email,
        to=to,
        connection=connection,
    )
    message.content_subtype = 'html'

    message.send(fail_silently=False)
