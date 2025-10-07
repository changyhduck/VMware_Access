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

新增 CLI 功能：

```bash
# 以互動方式使用已儲存的會話資料並重新登入（會提示輸入密碼）
python -m login resume

# 清除儲存的會話資料
python -m login clear-session
```

加密化儲存（選用）

`login.py` 支援以環境變數 `VMWARE_SESSION_KEY` 提供的 Fernet key（來自 cryptography 套件）來加密會話 metadata 檔案。若設定該環境變數且系統安裝 `cryptography`，會話會以加密形式儲存在 `~/.vmware_session.json`（實際為二進位 token）；否則會以純文字 JSON 儲存。

產生 key（一次性）並在目前 shell 設定為環境變數：

```bash
# 產生一組 Fernet key
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 將輸出貼到環境變數（bash 範例）
export VMWARE_SESSION_KEY="<the-generated-key>"
```

注意：
- 程式不會儲存密碼；`resume` 會提示輸入密碼以重新登入。
- 若要長期儲存 key，請使用安全的憑證管理工具或 shell 的安全機制；不要把 key 放入版本控制。

會話檔路徑覆寫

預設會話檔案為 `~/.vmware_session.json`。可用環境變數 `VMWARE_SESSION_FILE` 指定不同位置，例如：

```bash
export VMWARE_SESSION_FILE="/path/to/project/.vmware_session.json"
```

當 `VMWARE_SESSION_FILE` 與 `VMWARE_SESSION_KEY` 同時設定時，程式會嘗試以 key 解密指定路徑的檔案。

使用 passphrase 派生金鑰（選用）

另一個選項是使用環境變數 `VMWARE_SESSION_PASSPHRASE` 提供的 passphrase，程式會用 PBKDF2（SHA256）和每個會話檔案的隨機 salt 來派生一個 Fernet key。salt 會儲存在同一路徑但附加 `.salt` 副檔名（例如：`~/.vmware_session.json.salt`）。範例：

```bash
# 設定 passphrase（範例）
export VMWARE_SESSION_PASSPHRASE='your-long-passphrase'

# 登入（會產生 session file 與 salt）
python3 lib/login.py login --username ... --password ... --host ...

# 之後可用同一 passphrase 執行 resume
python3 lib/login.py resume
```

注意：若使用 passphrase 派生金鑰，請妥善保存你的 passphrase；salt 與會話檔必須同時存在才能解密。

logout 行為

`logout` 現在會在登出時嘗試移除儲存的會話檔與對應的 salt 檔（若存在）。若只想刪除會話檔但保留 salt，可改用 `clear-session` 指令或將檔案手動移除。


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
