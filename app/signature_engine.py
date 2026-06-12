import os
import logging
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

import config
from graph_client import UserData

log = logging.getLogger(__name__)

_env: Environment | None = None


def _get_env() -> Environment:
    global _env
    if _env is None:
        _env = Environment(
            loader=FileSystemLoader(config.TEMPLATE_DIR),
            autoescape=False,
        )
    return _env


def _reload_env() -> Environment:
    global _env
    _env = None
    return _get_env()


def render(user: UserData) -> tuple[str, str]:
    env = _get_env()
    ctx = {
        "user": user,
    }

    try:
        html = env.get_template("signature.html").render(**ctx)
    except TemplateNotFound:
        log.warning("signature.html not found, using empty HTML signature")
        html = ""
    except Exception as exc:
        log.error("Error rendering HTML signature: %s", exc)
        html = ""

    try:
        txt = env.get_template("signature.txt").render(**ctx)
    except TemplateNotFound:
        log.warning("signature.txt not found, using empty plaintext signature")
        txt = ""
    except Exception as exc:
        log.error("Error rendering plaintext signature: %s", exc)
        txt = ""

    return html, txt
