import email
import logging

import config
import graph_client
import loop_detector
import mail_processor
import reinject
import signature_engine

log = logging.getLogger(__name__)


class SignatureHandler:
    async def handle_DATA(self, server, session, envelope):
        sender = envelope.mail_from
        recipients = envelope.rcpt_tos
        raw = envelope.content

        try:
            msg = email.message_from_bytes(raw)

            if loop_detector.is_signed(msg):
                log.debug("Loop detected for mail from=%s, forwarding as-is", sender)
                reinject.send(sender, recipients, raw)
                return "250 OK"

            user_data = await graph_client.get_user(sender)
            sig_html, sig_txt = signature_engine.render(user_data)
            modified = mail_processor.inject(msg, sig_html, sig_txt)
            reinject.send(sender, recipients, modified.as_bytes())
            return "250 OK"

        except Exception as exc:
            log.error("Processing failed for mail from=%s: %s", sender, exc)
            if config.FALLBACK_ON_ERROR:
                log.info("Fallback: forwarding original mail from=%s", sender)
                try:
                    reinject.send(sender, recipients, raw)
                except Exception as fallback_exc:
                    log.error("Fallback re-inject also failed: %s", fallback_exc)
                    return "451 Temporary processing error"
                return "250 OK"
            return "451 Temporary processing error"
