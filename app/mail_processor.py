import email
import email.message
import email.mime.multipart
import email.mime.text
import email.mime.base
import logging
from copy import deepcopy

import loop_detector

log = logging.getLogger(__name__)

_PRESERVE_HEADERS = {
    "from", "to", "cc", "bcc", "subject", "message-id",
    "date", "reply-to", "in-reply-to", "references",
}


def inject(msg: email.message.Message, sig_html: str, sig_txt: str) -> email.message.Message:
    content_type = msg.get_content_type()

    if msg.get_content_maintype() == "multipart":
        _inject_into_multipart(msg, sig_html, sig_txt)
    elif content_type == "text/html":
        payload = msg.get_payload(decode=True).decode(msg.get_content_charset() or "utf-8", errors="replace")
        msg.set_payload(_append_html_sig(payload, sig_html), charset="utf-8")
    elif content_type == "text/plain":
        payload = msg.get_payload(decode=True).decode(msg.get_content_charset() or "utf-8", errors="replace")
        new_payload = payload + "\n\n" + sig_txt if sig_txt else payload
        # Convert to multipart/alternative so we can add an HTML part
        new_msg = email.mime.multipart.MIMEMultipart("alternative")
        for key, val in msg.items():
            if key.lower() not in _PRESERVE_HEADERS:
                continue
            new_msg[key] = val
        new_msg.attach(email.mime.text.MIMEText(new_payload, "plain", "utf-8"))
        if sig_html:
            html_body = f"<html><body><pre>{_escape_html(payload)}</pre>{sig_html}</body></html>"
            new_msg.attach(email.mime.text.MIMEText(html_body, "html", "utf-8"))
        loop_detector.mark_as_signed(new_msg)
        return new_msg
    else:
        log.warning("Unhandled content type %s, forwarding as-is", content_type)

    loop_detector.mark_as_signed(msg)
    return msg


def _inject_into_multipart(msg: email.message.Message, sig_html: str, sig_txt: str) -> None:
    html_part = None
    txt_part = None

    for part in msg.walk():
        ct = part.get_content_type()
        if ct == "text/html" and not part.get_param("attachment", header="content-disposition"):
            html_part = part
        elif ct == "text/plain" and not part.get_param("attachment", header="content-disposition"):
            txt_part = part

    if html_part is not None and sig_html:
        charset = html_part.get_content_charset() or "utf-8"
        payload = html_part.get_payload(decode=True).decode(charset, errors="replace")
        html_part.set_payload(_append_html_sig(payload, sig_html), charset="utf-8")

    if txt_part is not None and sig_txt:
        charset = txt_part.get_content_charset() or "utf-8"
        payload = txt_part.get_payload(decode=True).decode(charset, errors="replace")
        txt_part.set_payload(payload + "\n\n" + sig_txt, charset="utf-8")


def _append_html_sig(html: str, sig_html: str) -> str:
    lower = html.lower()
    idx = lower.rfind("</body>")
    if idx != -1:
        return html[:idx] + sig_html + html[idx:]
    return html + sig_html


def _escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
    )
