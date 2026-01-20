"""Mailtrap Airflow Provider - Send emails via Mailtrap.io transactional email service."""

__version__ = "1.0.0"


def get_provider_info():
    """Return provider metadata for Apache Airflow."""
    return {
        "package-name": "airflow-provider-mailtrap",
        "name": "Mailtrap",
        "description": "Send emails via Mailtrap.io transactional email service",
        "connection-types": [
            {
                "connection-type": "mailtrap",
                "hook-class-name": "mailtrap_provider.hooks.mailtrap.MailtrapHook",
            }
        ],
        "versions": [__version__],
    }
