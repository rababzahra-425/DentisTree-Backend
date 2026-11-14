"""SMTP backend that Gmail accepts on Python 3.12+.

Gmail often closes the socket on AUTH PLAIN (especially when the client
sends credentials in the initial AUTH command). AUTH LOGIN waits for the
334 challenge instead and authenticates reliably.
"""
from django.core.mail.backends.smtp import EmailBackend as DjangoEmailBackend
from django.core.mail.utils import DNS_NAME


class EmailBackend(DjangoEmailBackend):
    def open(self):
        if self.connection:
            return False

        connection_params = {"local_hostname": DNS_NAME.get_fqdn()}
        if self.timeout is not None:
            connection_params["timeout"] = self.timeout
        if self.use_ssl:
            connection_params["context"] = self.ssl_context
        try:
            self.connection = self.connection_class(
                self.host, self.port, **connection_params
            )
            if not self.use_ssl and self.use_tls:
                self.connection.starttls(context=self.ssl_context)
            if self.username and self.password:
                conn = self.connection
                conn.ehlo_or_helo_if_needed()
                conn.user = self.username
                conn.password = self.password
                conn.auth("LOGIN", conn.auth_login, initial_response_ok=False)
            return True
        except OSError:
            if not self.fail_silently:
                raise
