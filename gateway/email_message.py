"""Shared helpers for building outgoing Hermes email messages."""

import html as html_lib
import logging
import re
import uuid
from email.message import EmailMessage
from email.utils import formataddr, formatdate
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

EMAIL_MARKDOWN_EXTENSIONS = ["extra", "sane_lists"]
EMAIL_HTML_STYLE = """
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #202124; line-height: 1.45; }
h1, h2, h3 { margin: 20px 0 8px; line-height: 1.2; }
p { margin: 0 0 12px; }
hr { border: 0; border-top: 1px solid #d0d7de; margin: 20px 0; }
table { border-collapse: collapse; width: 100%; margin: 10px 0 16px; }
th, td { border: 1px solid #d0d7de; padding: 6px 8px; text-align: left; vertical-align: top; }
th { background: #f6f8fa; font-weight: 600; }
pre, code { font-family: ui-monospace, SFMono-Regular, Consolas, monospace; }
pre { background: #f6f8fa; padding: 12px; overflow-x: auto; }
blockquote { margin: 0 0 12px; padding-left: 12px; border-left: 3px solid #d0d7de; color: #57606a; }
a { color: #1a73e8; }
""".strip()


def clean_email_subject(subject: str) -> str:
    """Collapse unsafe header whitespace while preserving normal subject text."""
    return re.sub(r"[\r\n\t ]+", " ", str(subject or "")).strip()


def reply_subject(subject: str) -> str:
    """Return a sanitized reply subject with one Re: prefix."""
    clean_subject = clean_email_subject(subject or "Hermes Agent")
    if re.match(r"^re:", clean_subject, flags=re.IGNORECASE):
        return clean_subject
    return f"Re: {clean_subject}"


def metadata_text(metadata: Optional[Dict[str, Any]], key: str) -> Optional[str]:
    if not metadata:
        return None
    value = metadata.get(key)
    if value is None:
        return None
    text = str(value)
    return text if text else None


def format_email_from_header(from_addr: str, from_name: Optional[str] = None) -> str:
    """Format an email From header with an optional display name."""
    clean_from_name = str(from_name or "").strip()
    return formataddr((clean_from_name, from_addr)) if clean_from_name else from_addr


def wrap_email_html(fragment: str) -> str:
    """Wrap an HTML fragment in a minimal email-friendly document."""
    text = str(fragment or "")
    if re.search(r"<\s*html[\s>]", text[:500], flags=re.IGNORECASE):
        return text
    return (
        "<!doctype html>\n"
        "<html><head><meta charset=\"utf-8\">"
        f"<style>{EMAIL_HTML_STYLE}</style>"
        "</head><body>"
        f"{text}"
        "</body></html>"
    )


def markdown_to_email_html(markdown_text: str) -> Optional[str]:
    """Render Markdown as email HTML after escaping raw HTML input."""
    try:
        import markdown as markdown_lib
    except ImportError:
        logger.warning("[Email] Markdown email requested but Python-Markdown is not installed")
        return None

    escaped_source = html_lib.escape(str(markdown_text or ""), quote=False)
    html_body = markdown_lib.markdown(
        escaped_source,
        extensions=EMAIL_MARKDOWN_EXTENSIONS,
        output_format="html5",
    )
    return wrap_email_html(html_body)


def html_body_from_metadata(body: str, metadata: Optional[Dict[str, Any]]) -> Optional[str]:
    html_body = metadata_text(metadata, "html_body") or metadata_text(metadata, "html")
    if html_body is not None:
        return wrap_email_html(html_body)

    format_value = (
        metadata_text(metadata, "format")
        or metadata_text(metadata, "content_type")
        or ""
    ).lower()
    if format_value in {"html", "text/html"}:
        return wrap_email_html(body)
    if format_value in {"markdown", "md", "text/markdown"}:
        return markdown_to_email_html(body)
    return None


def build_outgoing_email_message(
    *,
    from_addr: str,
    to_addr: str,
    subject: str,
    body: str,
    html_body: Optional[str] = None,
    in_reply_to: Optional[str] = None,
    from_name: Optional[str] = None,
) -> EmailMessage:
    """Build a text/plain email, optionally with a text/html alternative."""
    msg = EmailMessage()
    msg["From"] = format_email_from_header(from_addr, from_name)
    msg["To"] = to_addr
    msg["Subject"] = clean_email_subject(subject)
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
        msg["References"] = in_reply_to
    msg["Date"] = formatdate(localtime=True)
    msg_id = f"<hermes-{uuid.uuid4().hex[:12]}@{from_addr.split('@')[1]}>"
    msg["Message-ID"] = msg_id
    msg.set_content(body or "", subtype="plain", charset="utf-8")
    if html_body:
        msg.add_alternative(html_body, subtype="html", charset="utf-8")
    return msg
