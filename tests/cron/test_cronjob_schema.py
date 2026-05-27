def test_cronjob_schema_exposes_delivery_email_formatting_options():
    """Cron jobs can opt into rich email subject/body delivery metadata."""
    from tools.cronjob_tools import CRONJOB_SCHEMA

    properties = CRONJOB_SCHEMA["parameters"]["properties"]
    assert "delivery_subject" in properties
    assert "delivery_format" in properties
    assert properties["delivery_format"]["enum"] == ["plain", "markdown", "html"]
