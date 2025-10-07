import os
import importlib.util
import json
import tempfile
import unittest


def _load_login_module():
    here = os.path.dirname(__file__)
    mod_path = os.path.normpath(os.path.join(here, '..', 'lib', 'login.py'))
    spec = importlib.util.spec_from_file_location('login', mod_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestSessionPersistence(unittest.TestCase):
    def test_plaintext_session(self):
        login = _load_login_module()
        VCenterSession = login.VCenterSession

        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, 'session.json')
            session = VCenterSession(session_file=str(p))
            meta = {'username': 'user', 'host': 'h.example', 'port': 443, 'timestamp': 123}
            session._save_session(meta)

            self.assertTrue(os.path.exists(p))
            loaded = session.load_saved_session()
            self.assertEqual(loaded, meta)

            session.clear_saved_session()
            self.assertFalse(os.path.exists(p))

    @unittest.skipUnless(os.environ.get('VMWARE_SESSION_KEY') or True, 'cryptography not available skip check at runtime')
    def test_encrypted_session_if_available(self):
        login = _load_login_module()
        VCenterSession = login.VCenterSession

        # skip-enforced only if cryptography missing at runtime
        if not getattr(login, 'HAVE_CRYPTO', False):
            self.skipTest('cryptography not available')

        # generate a key and set env var
        from cryptography.fernet import Fernet

        key = Fernet.generate_key().decode()
        os.environ['VMWARE_SESSION_KEY'] = key

        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, 'session.bin')
            session = VCenterSession(session_file=str(p))
            meta = {'username': 'u', 'host': 'h', 'port': 123, 'timestamp': 1}
            session._save_session(meta)

            self.assertTrue(os.path.exists(p))
            with open(p, 'rb') as fh:
                data = fh.read()
            self.assertTrue(data, 'session file empty')

            loaded = session.load_saved_session()
            self.assertEqual(loaded, meta)

            session.clear_saved_session()
            self.assertFalse(os.path.exists(p))


if __name__ == '__main__':
    unittest.main()
