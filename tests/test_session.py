import os
import importlib.util
import json


def _load_login_module():
    here = os.path.dirname(__file__)
    mod_path = os.path.normpath(os.path.join(here, '..', 'lib', 'login.py'))
    spec = importlib.util.spec_from_file_location('login', mod_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_plaintext_session(tmp_path):
    login = _load_login_module()
    VCenterSession = login.VCenterSession

    p = tmp_path / 'session.json'
    session = VCenterSession(session_file=str(p))
    meta = {'username': 'user', 'host': 'h.example', 'port': 443, 'timestamp': 123}
    session._save_session(meta)

    assert p.exists()
    loaded = session.load_saved_session()
    assert loaded == meta

    session.clear_saved_session()
    assert not p.exists()


def test_encrypted_session_if_available(tmp_path):
    login = _load_login_module()
    VCenterSession = login.VCenterSession

    if not getattr(login, 'HAVE_CRYPTO', False):
        import pytest

        pytest.skip('cryptography not available')

    # generate a key and set env var
    from cryptography.fernet import Fernet

    key = Fernet.generate_key().decode()
    os.environ['VMWARE_SESSION_KEY'] = key

    p = tmp_path / 'session.bin'
    session = VCenterSession(session_file=str(p))
    meta = {'username': 'u', 'host': 'h', 'port': 123, 'timestamp': 1}
    session._save_session(meta)

    assert p.exists()
    # if encrypted, file is binary token (not plain JSON)
    with open(p, 'rb') as fh:
        data = fh.read()
    assert data, 'session file empty'

    loaded = session.load_saved_session()
    assert loaded == meta

    session.clear_saved_session()
    assert not p.exists()
