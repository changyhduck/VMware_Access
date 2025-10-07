# 這個檔案描述 login.py 模組的功能、用法和範例。

login.py 模組提供 VMware vCenter 管理程式的登入與登出功能，並支援連線狀態管理、錯誤處理與自動化腳本操作。

## 主要功能
- 使用帳號、密碼登入 VMware vCenter
- 登出 vCenter
- 取得連線狀態
- 錯誤處理與日誌記錄
- 支援 CLI 介面與自動化腳本

## 主要函式列表
- `login(username, password, vcenter_host, port=443)`
- `logout()`
- `get_status()`

## 使用範例總覽
```python
import login

# 1. 登入 vCenter
success = login.login('administrator@vsphere.local', 'your_password', 'vcenter.example.com')
if success:
	print("登入成功")
else:
	print("登入失敗")

# 2. 取得連線狀態
status = login.get_status()
print(f"目前連線狀態: {status}")

# 3. 登出 vCenter
login.logout()
print("已登出 vCenter")
```

---

## 主要函式與說明

### login(username, password, vcenter_host, port=443)
- 描述: 使用指定帳號密碼登入 VMware vCenter，成功後建立連線物件。
- 參數:
  - username: vCenter 帳號
  - password: 密碼
  - vcenter_host: vCenter 主機位址
  - port: 連線埠號（預設 443）
- 回傳值: 登入成功回傳 True，失敗回傳 False

#### 範例
```python
login.login('administrator@vsphere.local', 'your_password', 'vcenter.example.com')
```

#### 錯誤處理
```python
try:
	login.login('administrator@vsphere.local', 'your_password', 'vcenter.example.com')
except Exception as e:
	print(f"登入失敗: {e}")
```

### logout()
- 描述: 登出 vCenter，釋放連線資源。
- 參數: 無
- 回傳值: 無

#### 範例
```python
login.logout()
```

#### 錯誤處理
```python
try:
	login.logout()
except Exception as e:
	print(f"登出失敗: {e}")
```

### get_status()
- 描述: 取得目前 vCenter 連線狀態（已連線/未連線/錯誤）。
- 參數: 無
- 回傳值: 狀態字串

#### 範例
```python
status = login.get_status()
print(status)
```

---

## CLI 介面

可用指令（假設已安裝 login.py 為 CLI 工具）：

```bash
# 登入 vCenter
python -m login login --username administrator@vsphere.local --password your_password --host vcenter.example.com

# 登出 vCenter
python -m login logout

# 查詢連線狀態
python -m login status
```

---

## 依賴與環境

- Ubuntu 24.04 Desktop / macOS
- Python 3.10+
- pyvmomi 套件
- 需網路可連線至 vCenter

安裝 pyvmomi：
```bash
pip install pyvmomi
```

---

## 常見問題 FAQ

**Q1: 為什麼登入失敗？**
A: 請確認帳號密碼正確，vCenter 主機可連線，且 pyvmomi 已安裝。

**Q2: 登出後仍顯示已連線？**
A: 請確認 logout() 已執行且無例外，並檢查連線物件是否釋放。

**Q3: CLI 執行權限不足？**
A: 請以正確 Python 環境執行，或檢查網路與防火牆設定。

---

## 最佳實踐與建議

- 登入後請妥善管理連線物件，避免資源洩漏。
- 登出前可先確認連線狀態。
- 建議將密碼儲存於安全環境變數或憑證管理工具。
- 失敗時請記錄日誌以利排查。

---

## 常見錯誤與排解

- `vim.fault.InvalidLogin`: 帳號或密碼錯誤
- `socket.error`: 網路連線失敗
- `ModuleNotFoundError: No module named 'pyVim'`: 未安裝 pyvmomi

---

## 完整範例程式碼

```python
#!/usr/bin/env python3
"""
VMware vCenter 登入/登出管理範例
"""
from pyVim.connect import SmartConnect, Disconnect
import ssl

class VCenterSession:
	def __init__(self):
		self.si = None
		self.status = '未連線'

	def login(self, username, password, vcenter_host, port=443):
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
			print(f"成功登入 vCenter: {vcenter_host}")
			return True
		except Exception as e:
			self.status = f"登入失敗: {e}"
			print(self.status)
			return False

	def logout(self):
		try:
			if self.si:
				Disconnect(self.si)
				self.status = '已登出'
				print("已成功登出 vCenter")
		except Exception as e:
			print(f"登出失敗: {e}")

	def get_status(self):
		return self.status

# 使用範例
session = VCenterSession()
session.login('administrator@vsphere.local', 'your_password', 'vcenter.example.com')
print(session.get_status())
session.logout()
```

---

## 注意事項與安全性考量

- 請勿將密碼明文寫入程式碼，建議使用環境變數或憑證管理。
- 登入失敗請檢查網路、帳號、密碼、vCenter 主機狀態。
- 登出後請確認資源已釋放。

## 版本資訊

- 適用於 Ubuntu 24.04 Desktop / macOS
- Python 3.10 以上
- pyvmomi 8.x

## 相依性

### Python 套件
- pyvmomi
- 標準庫: ssl, logging, os, sys

### 安裝指令
```bash
pip install pyvmomi
```
