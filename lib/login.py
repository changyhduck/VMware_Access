"""
login.py
VMware vCenter 登入/登出管理模組
依據 login.md 規範實作
"""
from pyVim.connect import SmartConnect, Disconnect
import ssl
import logging

class VCenterSession:
    def __init__(self):
        self.si = None
        self.status = '未連線'
        self.logger = logging.getLogger(__name__)

    def login(self, username, password, vcenter_host, port=443):
        """使用指定帳號密碼登入 VMware vCenter"""
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
        except Exception as e:
            self.logger.error(f"登出失敗: {e}")

    def get_status(self):
        """取得目前 vCenter 連線狀態"""
        return self.status

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
    else:
        parser.print_help()
