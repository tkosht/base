from template_python_app.core import healthcheck


def test_healthcheck_default() -> None:
    assert healthcheck() == "template:ok"


def test_healthcheck_custom_name() -> None:
    assert healthcheck("python") == "python:ok"
