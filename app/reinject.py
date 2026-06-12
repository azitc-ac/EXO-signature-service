import smtplib
import logging

import config

log = logging.getLogger(__name__)


def send(mail_from: str, rcpt_tos: list[str], content_bytes: bytes) -> None:
    try:
        with smtplib.SMTP(config.EXO_SMARTHOST, config.EXO_PORT, timeout=30) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.sendmail(mail_from, rcpt_tos, content_bytes)
        log.info("Re-injected mail from=%s to=%s", mail_from, rcpt_tos)
    except Exception as exc:
        log.error("Re-inject failed from=%s to=%s: %s", mail_from, rcpt_tos, exc)
        raise
