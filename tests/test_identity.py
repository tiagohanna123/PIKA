import os
from pika.identity import identity, SystemIdentity


def test_identity_env_override(monkeypatch):
    monkeypatch.setenv("PIKA_SYSTEM_ID", "TestID")
    monkeypatch.setenv("PIKA_SYSTEM_DESCRIPTION", "desc")
    monkeypatch.setenv("PIKA_SYSTEM_VERSION", "1.2.3")
    monkeypatch.setenv("PIKA_SYSTEM_SYMBOL", "∆")
    new_identity = SystemIdentity.load()
    assert new_identity.id == "TestID"
    assert new_identity.description == "desc"
    assert new_identity.version == "1.2.3"
    assert new_identity.symbol == "∆"
