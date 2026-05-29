"""Example source and recipient adapters."""

from enlace_examples.file_source import FileSourceAdapter
from enlace_examples.http_source import HttpSourceAdapter
from enlace_examples.logging_recipient import LoggingRecipientAdapter
from enlace_examples.webhook_recipient import WebhookRecipientAdapter

__all__ = [
    "FileSourceAdapter",
    "HttpSourceAdapter",
    "LoggingRecipientAdapter",
    "WebhookRecipientAdapter",
]
