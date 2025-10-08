"""
login.py
VMware vCenter 登入/登出管理模組
依據 login.md 規範實作
"""
import os
import json
import time
import getpass
from pathlib import Path
import base64

# optional pyvmomi (pyVim) support
try:
    from pyVim.connect import SmartConnect, Disconnect
    import ssl
    HAVE_PYVMOMI = True
except Exception:
    SmartConnect = None
    Disconnect = None
    ssl = None
    HAVE_PYVMOMI = False

# optional encryption support
try:
    from cryptography.fernet import Fernet, InvalidToken
    HAVE_CRYPTO = True
except Exception:
    Fernet = None
    InvalidToken = Exception
    HAVE_CRYPTO = False
# PBKDF2 imports (needed for passphrase-derived keys) - try regardless
try:
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.backends import default_backend
except Exception:
    PBKDF2HMAC = None
    hashes = None
    default_backend = None

import logging

class VCenterSession:
    """Manage a vCenter connection and persist last-session metadata.

    Session metadata (host, username, port and optional cookie) are stored in
    a JSON file by default at ~/.vmware_session.json. Passwords are not
    stored. Use `resume()` to re-login using stored host/username (it will
    prompt for the password interactively).
    """

    DEFAULT_SESSION_FILE = os.path.expanduser('~/.vmware_session.json')

    def __init__(self, session_file: str | None = None):
        self.si = None
        self.status = '未連線'
        self.logger = logging.getLogger(__name__)
        # allow overriding the session file via environment variable
        env_path = os.environ.get('VMWARE_SESSION_FILE')
        self.session_file = (
            session_file or env_path or self.DEFAULT_SESSION_FILE
        )

    def login(self, username, password, vcenter_host, port=443):
        """Login to vCenter. On success, persist session metadata (no password).

        Returns True on success, False on failure.
        """
        if not HAVE_PYVMOMI or SmartConnect is None or ssl is None:
            self.status = "登入失敗: pyvmomi (pyVim) 未安裝或匯入失敗，請安裝 pyvmomi 套件。"
            self.logger.error(self.status)
            return False
        try:
            context = ssl._create_unverified_context()
            self.si = SmartConnect(
                host=vcenter_host,
                user=username,
                pwd=password,
                port=port,
                sslContext=context
            )
            self.status = '已連線'

            # try to capture a session cookie if available (may be None)
            cookie = None
            try:
                cookie = getattr(self.si._stub, 'cookie', None)
            except Exception:
                cookie = None

            meta = {
                'username': username,
                'host': vcenter_host,
                'port': port,
                'timestamp': int(time.time()),
            }
            if cookie:
                meta['cookie'] = cookie

            try:
                self._save_session(meta)
            except Exception as e:
                self.logger.warning(f"Could not save session metadata: {e}")

            self.logger.info(f"成功登入 vCenter: {vcenter_host}")
            return True
        except Exception as e:
            self.status = f"登入失敗: {e}"
            self.logger.error(self.status)
            return False

    def logout(self):
        """登出 vCenter，釋放連線資源"""
        try:
            if self.si:
                Disconnect(self.si)
                self.status = '已登出'
                self.logger.info("已成功登出 vCenter")
            # always attempt to clear persisted session (session file + salt)
            try:
                self.clear_saved_session()
            except Exception:
                pass
        except Exception as e:
            self.logger.error(f"登出失敗: {e}")

    def get_status(self):
        """取得目前 vCenter 連線狀態"""
        return self.status

    # --- session persistence helpers ---
    def _save_session(self, metadata: dict):
        # ensure parent directory exists
        parent = Path(self.session_file).expanduser().parent
        parent.mkdir(parents=True, exist_ok=True)

        key_env = os.environ.get('VMWARE_SESSION_KEY')
        passphrase = os.environ.get('VMWARE_SESSION_PASSPHRASE')
        data = json.dumps(metadata, ensure_ascii=False).encode('utf-8')

        # prefer explicit key, else derive from passphrase
        if HAVE_CRYPTO and (key_env or passphrase):
            try:
                if key_env:
                    key_bytes = key_env.encode()
                else:
                    # derive key from passphrase using PBKDF2 with per-file salt
                    if PBKDF2HMAC is None:
                        raise RuntimeError('cryptography PBKDF2 unavailable')
                    salt_path = f"{self.session_file}.salt"
                    if os.path.exists(salt_path):
                        salt = open(salt_path, 'rb').read()
                    else:
                        salt = os.urandom(16)
                        with open(salt_path, 'wb') as sf:
                            sf.write(salt)

                    kdf = PBKDF2HMAC(
                        algorithm=hashes.SHA256(),
                        length=32,
                        salt=salt,
                        iterations=390000,
                        backend=default_backend(),
                    )
                    key_bytes = base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))

                f = Fernet(key_bytes)
                token = f.encrypt(data)
                with open(self.session_file, 'wb') as fh:
                    fh.write(token)
                return
            except Exception as e:
                self.logger.warning(f"Failed to encrypt session file, falling back to plaintext: {e}")

        # fallback: plaintext JSON
        with open(self.session_file, 'w', encoding='utf-8') as fh:
            json.dump(metadata, fh, ensure_ascii=False)

    def load_saved_session(self) -> dict | None:
        """Return saved session metadata or None if missing."""
        try:
            if not os.path.exists(self.session_file):
                return None
            key_env = os.environ.get('VMWARE_SESSION_KEY')
            passphrase = os.environ.get('VMWARE_SESSION_PASSPHRASE')
            # if key or passphrase and cryptography available, try to decrypt (file is bytes)
            if HAVE_CRYPTO and (key_env or passphrase):
                try:
                    with open(self.session_file, 'rb') as fh:
                        token = fh.read()

                    if key_env:
                        key_bytes = key_env.encode()
                    else:
                        if PBKDF2HMAC is None:
                            raise RuntimeError('cryptography PBKDF2 unavailable')
                        salt_path = f"{self.session_file}.salt"
                        if not os.path.exists(salt_path):
                            raise RuntimeError('Salt file missing for passphrase-derived key')
                        salt = open(salt_path, 'rb').read()
                        kdf = PBKDF2HMAC(
                            algorithm=hashes.SHA256(),
                            length=32,
                            salt=salt,
                            iterations=390000,
                            backend=default_backend(),
                        )
                        key_bytes = base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))

                    f = Fernet(key_bytes)
                    data = f.decrypt(token)
                    return json.loads(data.decode('utf-8'))
                except InvalidToken:
                    # decryption failed -> try plaintext fallback
                    self.logger.warning('Failed to decrypt session file with provided key; trying plaintext parse')
                except Exception as e:
                    self.logger.warning(f'Error decrypting session file: {e}')

            # fallback: try plaintext JSON
            with open(self.session_file, 'r', encoding='utf-8') as fh:
                return json.load(fh)
        except Exception as e:
            self.logger.warning(f"Failed to load saved session: {e}")
            return None

    def clear_saved_session(self):
        try:
            if os.path.exists(self.session_file):
                os.remove(self.session_file)
            # also remove salt file if present
            salt_path = f"{self.session_file}.salt"
            if os.path.exists(salt_path):
                try:
                    os.remove(salt_path)
                except Exception as e:
                    self.logger.warning(f"Failed to remove salt file: {e}")
        except Exception as e:
            self.logger.warning(f"Failed to clear saved session: {e}")

    def resume(self) -> bool:
        """Attempt to resume a saved session by asking the user for the password.

        This does not attempt to reuse stored passwords. It will prompt for the
        password interactively and perform a fresh login using the stored
        host/username/port.
        """
        meta = self.load_saved_session()
        if not meta:
            raise FileNotFoundError("No saved session metadata found")
        username = meta.get('username')
        host = meta.get('host')
        port = meta.get('port', 443)
        print(f"Resuming session for {username}@{host}:{port}")
        password = getpass.getpass(prompt='Password: ')
        return self.login(username, password, host, port)

# CLI 介面
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='VMware vCenter 登入/登出工具')
    subparsers = parser.add_subparsers(dest='command')

    login_parser = subparsers.add_parser('login')
    login_parser.add_argument('--username', required=True)
    login_parser.add_argument('--password', required=True)
    login_parser.add_argument('--host', required=True)
    login_parser.add_argument('--port', type=int, default=443)

    logout_parser = subparsers.add_parser('logout')
    status_parser = subparsers.add_parser('status')
    resume_parser = subparsers.add_parser('resume')
    clear_parser = subparsers.add_parser('clear-session')

    args = parser.parse_args()
    session = VCenterSession()

    if args.command == 'login':
        success = session.login(args.username, args.password, args.host, args.port)
        print('登入成功' if success else '登入失敗')
    elif args.command == 'logout':
        session.logout()
        print('已登出 vCenter')
    elif args.command == 'status':
        print(session.get_status())
    elif args.command == 'resume':
        if not HAVE_PYVMOMI:
            print('pyvmomi (pyVim) not available; cannot resume. Install pyvmomi and retry.')
        else:
            try:
                ok = session.resume()
                print('登入成功' if ok else '登入失敗')
            except Exception as e:
                print(f'Resume failed: {e}')
    elif args.command == 'clear-session':
        session.clear_saved_session()
        print('已清除儲存的會話資料')
    else:
        parser.print_help()
