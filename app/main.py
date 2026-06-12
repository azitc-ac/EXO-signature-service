import asyncio
import logging
import ssl
import threading
from pathlib import Path

import uvicorn
from aiosmtpd.controller import Controller

import config
from handler import SignatureHandler
from webui.app import app as fastapi_app

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger(__name__)


def _build_tls_context() -> ssl.SSLContext | None:
    cert = Path(config.SMTP_TLS_CERT)
    key = Path(config.SMTP_TLS_KEY)
    if not cert.exists() or not key.exists():
        log.warning("TLS cert/key not found (%s / %s), starting SMTP without TLS", cert, key)
        return None
    ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ctx.load_cert_chain(certfile=str(cert), keyfile=str(key))
    return ctx


def _run_webui():
    uvicorn.run(
        fastapi_app,
        host="0.0.0.0",
        port=config.WEBUI_PORT,
        log_level=config.LOG_LEVEL.lower(),
        access_log=False,
    )


async def _run_smtp():
    tls_ctx = _build_tls_context()
    handler = SignatureHandler()

    controller = Controller(
        handler,
        hostname="0.0.0.0",
        port=config.SMTP_PORT,
        tls_context=tls_ctx,
        require_starttls=tls_ctx is not None,
    )
    controller.start()
    log.info(
        "SMTP listener started on port %d (TLS: %s)",
        config.SMTP_PORT,
        "yes" if tls_ctx else "no",
    )
    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        controller.stop()


def main():
    log.info("Starting EXO Signature Service")

    webui_thread = threading.Thread(target=_run_webui, daemon=True)
    webui_thread.start()
    log.info("Web UI started on port %d", config.WEBUI_PORT)

    asyncio.run(_run_smtp())


if __name__ == "__main__":
    main()
