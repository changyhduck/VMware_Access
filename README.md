# 這個專案是用python程式來管理VMware虛擬化環境。
- 利用VMware提供的Restful API對VMware虛擬化系統操作。
- 本專案預計操作VMware vSphere 5.5 以後的版本都要相容。

# 本專案結構
- 主程式稱為vmware-adm.py。它用python實作，主要實作console ui程式。vmware-adm.py使用的功能實作，分類後放在lib目錄下。
- lib目錄存放被呼叫的功能。
- test目錄存放測試程式碼。
- 每一個python程式檔案會對應一個markdown檔案，且檔名一樣。例如，login.py的markdown檔案稱為login.md。

# 程式碼結構
- 每一個python程式檔案，第一部分是import和from的宣告
- 第二部分是廣域參數宣告
- 第三部分是功能函式實作
  每一支函式必須說明輸入參數和輸出參數。
- 第四部分是console介面實作
