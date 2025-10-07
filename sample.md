# 這個檔案描述storage.py模組的功能，用法和範例。


storage.py模組提供了一些用於處理btrfs檔案系統相關任務的函數和類別。這些功能包括但不限於：
- 建立、刪除和管理btrfs檔案系統
- 支援多種RAID等級配置（RAID0/1/5/6/10）
- 建立和管理btrfs快照，支援快照還原功能
- 監控磁碟使用量，自動清理過期快照
- 檢查btrfs檔案系統健康狀況
- 修復RAID5/RAID6故障磁碟
- 列出和刪除快照
- 取得檔案系統詳細資訊和使用量統計
- 管理除系統磁碟外的所有實體磁碟（包括iSCSI磁碟和USB磁碟）
- 提供完整的錯誤處理和日誌記錄
- 支援CLI介面和自動化腳本操作

## 非常重要的規範
- 所有storage.py建立的volume只能mount在/storage目錄或/backup目錄
- 若/storage目錄、/backup目錄和/storage/local目錄不存在，必須建立
- /storage/local目錄不可以刪除

## 主要功能列表
- `list_btrfs_volumes()`
- `create_btrfs_volume(name, devices, raid_level, ...)`
- `delete_btrfs_volume(name, ...)`
- `mount_btrfs_volume(name, mount_root='/storage', ...)`
- `umount_btrfs_volume(target, force=False, lazy=False)`
- `snapshot_btrfs_volume(name, label='', dry_run=False)`
- `restore_btrfs_volume(name, snapshot, dry_run=False)`
- `check_btrfs_health()`
- `monitor_disk_usage(threshold_warn=70.0, threshold_crit=85.0)`
- `repair_btrfs_volume(name, disk, dry_run=False)`
- `list_snapshots(name)`
- `delete_snapshot(name, snapshot, dry_run=False)`
- `prune_snapshots(name, keep=30, max_age_days=None, dry_run=False)`
- `get_volume_info(name)`
- `get_disk_usage(name)`
- `validate_btrfs_volume(name)` (新增)
- `get_storage_summary()` (新增)

## 使用範例總覽
```python
import storage

# 1. 檢查現有btrfs檔案系統
volumes = storage.list_btrfs_volumes()
print(f"現有btrfs檔案系統: {volumes}")

# 2. 建立高可用性儲存架構
print("\n=== 建立RAID5 btrfs檔案系統 ===")
devices = ['/dev/sdb', '/dev/sdc', '/dev/sdd']
storage.create_btrfs_volume('DataVolume', devices, raid_level='raid5')

# 配置掛載點並建立初始快照
info = storage.get_volume_info('DataVolume')
print(f"檔案系統資訊: {info}")

storage.snapshot_btrfs_volume('DataVolume')
print("初始快照已建立")

# 3. 監控和維護
print("\n=== 系統監控與維護 ===")
# 檢查健康狀況
health_report = storage.check_btrfs_health()
print(f"健康狀況: {health_report}")

# 監控磁碟使用量
storage.monitor_disk_usage()
print("磁碟使用量監控已啟動")

# 4. 快照管理
print("\n=== 快照管理 ===")
snapshots = storage.list_snapshots('DataVolume')
print(f"現有快照: {snapshots}")

# 定期建立快照（模擬定期備份）
storage.snapshot_btrfs_volume('DataVolume')
print("定期快照已建立")

# 5. 故障處理模擬
print("\n=== 故障處理 ===")
# 如果RAID有磁碟故障，可用新磁碟進行修復
# storage.repair_btrfs_volume('DataVolume', '/dev/sde')
print("RAID修復功能待命中")
```

---

## 主要函式與說明

## 函數和類別詳細說明
### list_btrfs_volumes()
- 描述: 列出所有 btrfs 檔案系統，並回傳其基礎資訊（名稱、掛載點、UUID、RAID 類型若可取得）
- 參數: 無
- 回傳值: `list[dict]`，每個元素可能包含：
  - `name`: 檔案系統名稱或標識 (str)
  - `mount_point`: 掛載點 (str | None)
  - `uuid`: 檔案系統 UUID (str | None)
  - `raid_level`: RAID 等級 (str | None)
  - `devices`: 參與的底層裝置列表 (list[str] | None)

> 備註：若底層系統指令輸出不足，部分欄位可能為 None。請在程式中以 `dict.get(key)` 方式安全存取。

#### 範例
```python
volumes = list_btrfs_volumes()
for v in volumes:
    print(f"名稱: {v.get('name')}, 掛載點: {v.get('mount_point')}, RAID: {v.get('raid_level')}")
```

#### 實際應用場景範例：產生儲存資源盤點報告
```python
import storage
import json
from datetime import datetime

def generate_storage_inventory_report():
    try:
        volumes = storage.list_btrfs_volumes()
        if not volumes:
            print("系統尚未建立任何 btrfs 檔案系統")
            return

        report = []
        for v in volumes:
            name = v.get('name')
            mount_point = v.get('mount_point')
            info = {}
            usage = None
            try:
                if name:
                    info = storage.get_volume_info(name) or {}
                    usage = storage.get_disk_usage(name)
            except Exception as inner_e:
                info['error'] = f"無法取得詳細資訊: {inner_e}" 

            report.append({
                'name': name,
                'mount_point': mount_point,
                'uuid': v.get('uuid'),
                'raid_level': v.get('raid_level'),
                'devices': v.get('devices'),
                'usage_percent': usage,
                'total_size_gb': info.get('total_size'),
                'used_size_gb': info.get('used_size'),
                'status': info.get('status'),
            })

        output = {
            'generated_at': datetime.now().isoformat(),
            'volume_count': len(report),
            'volumes': report
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"建立盤點報告時發生錯誤: {e}")

generate_storage_inventory_report()
```

#### 進階用法：過濾特定 RAID 類型
```python
volumes = list_btrfs_volumes()
raid5_vols = [v for v in volumes if v.get('raid_level') == 'raid5']
print(f"RAID5 檔案系統數量: {len(raid5_vols)}")
```

#### 錯誤處理
```python
try:
    volumes = list_btrfs_volumes()
except Exception as e:
    print(f"Error listing btrfs volumes: {e}")
```

### create_btrfs_volume(name, devices, raid_level="raid1")
- 描述: 建立新的 btrfs 檔案系統，可指定 RAID 等級；成功後將嘗試自動建立並掛載到 `/storage/{name}`（未來可依策略掛載至 `/backup/{name}`）。若掛載目錄不存在會自動建立，掛載失敗會拋出例外並不影響檔案系統本身建立結果（呼叫端可後續重試掛載）。
- 參數:
  - name: 新檔案系統名稱
  - devices: 用於建立的磁碟裝置列表
  - raid_level: RAID 等級（預設 raid1，可選 raid0/1/5/6/10）
- 回傳值: 無
#### 範例
```python
create_btrfs_volume("MyVolume", ["/dev/sdb", "/dev/sdc"], raid_level="raid5")
```
#### 實際應用場景範例
```python
import storage
def setup_backup_storage():
    """設定備份儲存系統"""
    try:
        # 檢查可用磁碟
        available_disks = ['/dev/sdb', '/dev/sdc', '/dev/sdd']
        
        # 建立RAID5檔案系統以獲得冗餘和效能
        print("建立RAID5備份儲存...")
        storage.create_btrfs_volume('BackupStorage', available_disks, raid_level='raid5')
        
        # 驗證建立結果
        volumes = storage.list_btrfs_volumes()
        if 'BackupStorage' in volumes:
            print("✅ 備份儲存系統建立成功")
            
            # 取得檔案系統資訊
            info = storage.get_volume_info('BackupStorage')
            print(f"檔案系統詳細資訊: {info}")
            
            # 建立初始快照
            storage.snapshot_btrfs_volume('BackupStorage')
            print("初始快照已建立")
            
        else:
            print("❌ 備份儲存系統建立失敗")
            
    except Exception as e:
        print(f"設定備份儲存時發生錯誤: {e}")

setup_backup_storage()
```
#### 錯誤處理
```python
try:
    create_btrfs_volume("MyVolume", ["/dev/sdb", "/dev/sdc"])
except Exception as e:
    print(f"Error creating btrfs volume: {e}")
```

### delete_btrfs_volume(name)
- 描述: 刪除指定的 btrfs 檔案系統；流程包含 (1) 卸載已掛載的掛載點 (2) 清理自動建立的掛載目錄（僅在目錄為空或為系統自動建立且無殘留自訂檔案時）(3) 釋放/移除底層裝置與 RAID 結構。若卸載失敗會拋出例外並中止刪除，以避免遺留掛載中的裝置。
- 參數:
  - name: 要刪除的檔案系統名稱
- 回傳值: 無
#### 範例
```python
delete_btrfs_volume("MyVolume")
```
#### 實際應用場景範例
```python
import storage
def cleanup_old_volumes():
    """清理舊的或不需要的檔案系統"""
    try:
        # 列出所有檔案系統
        volumes = storage.list_btrfs_volumes()
        
        for volume in volumes:
            # 檢查檔案系統使用狀況
            usage = storage.get_disk_usage(volume)
            info = storage.get_volume_info(volume)
            
            print(f"檢查檔案系統: {volume}")
            print(f"使用率: {usage}%")
            
            # 如果是測試或臨時檔案系統且使用率低，考慮刪除
            if volume.startswith('test_') and usage < 5:
                # 先備份重要快照
                snapshots = storage.list_snapshots(volume)
                if snapshots:
                    print(f"發現 {len(snapshots)} 個快照，先進行備份...")
                    # 這裡可以加入備份邏輯
                
                # 確認刪除
                print(f"準備刪除檔案系統: {volume}")
                storage.delete_btrfs_volume(volume)
                print(f"✅ 已刪除檔案系統: {volume}")
                
    except Exception as e:
        print(f"清理檔案系統時發生錯誤: {e}")

cleanup_old_volumes()
```
#### 錯誤處理
```python
try:
    delete_btrfs_volume("MyVolume")
except Exception as e:
    print(f"Error deleting btrfs volume: {e}")
```

### snapshot_btrfs_volume(name, label="", dry_run=False)
- 描述: 建立唯讀快照；快照存於掛載點目錄下 `.sna/`，格式 `YYYYmmddHHMMSS_ro[_label]`。`label` 會被過濾成英數/`-`/`_` 並截斷 32 字元；`dry_run=True` 僅輸出將執行的指令。
- 參數:
  - name: btrfs 檔案系統名稱
- 回傳值: 無
#### 範例
```python
snapshot_btrfs_volume("MyVolume")
```
#### 實際應用場景範例
```python
import storage
import datetime
import schedule
import time

def automated_backup_system():
    """自動化備份系統"""
    def create_daily_snapshot():
        try:
            volumes = storage.list_btrfs_volumes()
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            for volume in volumes:
                if not volume.startswith('temp_'):  # 跳過臨時檔案系統
                    print(f"建立快照: {volume} - {timestamp}")
                    storage.snapshot_btrfs_volume(volume)
                    
                    # 檢查快照是否建立成功
                    snapshots = storage.list_snapshots(volume)
                    print(f"✅ {volume} 快照建立完成，總快照數: {len(snapshots)}")
                    
                    # 清理過舊快照（保留最近30個）
                    if len(snapshots) > 30:
                        oldest_snapshots = snapshots[:-30]  # 取得最舊的快照
                        for old_snapshot in oldest_snapshots:
                            storage.delete_snapshot(volume, old_snapshot)
                            print(f"清理舊快照: {old_snapshot}")
                            
        except Exception as e:
            print(f"自動備份時發生錯誤: {e}")
    
    # 設定每日凌晨2點執行快照
    schedule.every().day.at("02:00").do(create_daily_snapshot)
    
    print("自動備份系統已啟動，每日凌晨2點執行")
    while True:
        schedule.run_pending()
        time.sleep(3600)  # 每小時檢查一次

# 手動執行一次快照
def manual_snapshot():
    try:
        storage.snapshot_btrfs_volume("DataVolume")
        print("手動快照建立完成")
    except Exception as e:
        print(f"建立快照失敗: {e}")

manual_snapshot()
```
#### 錯誤處理
```python
try:
    snapshot_btrfs_volume("MyVolume")
except Exception as e:
    print(f"Error creating snapshot: {e}")
```

### restore_btrfs_volume(name, snapshot, dry_run=False)
- 描述: 將 btrfs 檔案系統復原到某一快照
- 參數:
  - name: btrfs 檔案系統名稱
  - snapshot: 要復原的快照名稱
- 回傳值: 無
#### 範例
```python
restore_btrfs_volume("MyVolume", "snapshot_20231001")
```
#### 實際應用場景範例
```python
import storage

def disaster_recovery():
    """災難復原流程"""
    try:
        volume_name = "ProductionData"
        
        # 1. 檢查檔案系統狀態
        print("檢查檔案系統狀態...")
        health = storage.check_btrfs_health()
        print(f"健康狀況: {health}")
        
        # 2. 列出可用快照
        snapshots = storage.list_snapshots(volume_name)
        if not snapshots:
            print("❌ 沒有可用的快照進行復原")
            return
            
        print(f"發現 {len(snapshots)} 個可用快照:")
        for i, snapshot in enumerate(snapshots[-10:]):  # 顯示最近10個
            print(f"{i+1}. {snapshot}")
        
        # 3. 選擇最近的穩定快照進行復原
        latest_snapshot = snapshots[-2]  # 選擇倒數第二個快照（最新的可能有問題）
        print(f"選擇快照進行復原: {latest_snapshot}")
        
        # 4. 建立當前狀態的緊急快照
        print("建立緊急快照...")
        storage.snapshot_btrfs_volume(volume_name)
        
        # 5. 執行復原
        print(f"開始復原到快照: {latest_snapshot}")
        storage.restore_btrfs_volume(volume_name, latest_snapshot)
        
        # 6. 驗證復原結果
        info = storage.get_volume_info(volume_name)
        print(f"復原完成，檔案系統資訊: {info}")
        print("✅ 災難復原完成")
        
    except Exception as e:
        print(f"災難復原過程中發生錯誤: {e}")

disaster_recovery()
```
#### 錯誤處理
```python
try:
    restore_btrfs_volume("MyVolume", "snapshot_20231001")
except Exception as e:
    print(f"Error restoring volume: {e}")
```

### check_btrfs_health()
- 描述: 檢查所有 btrfs 檔案系統健康狀況
- 參數: 無
- 回傳值: 健康狀況報告
#### 範例
```python
health_report = check_btrfs_health()
print(health_report)
```
#### 實際應用場景範例
```python
import storage
import time

def health_monitoring_system():
    """健康監控系統"""
    def check_system_health():
        try:
            print("=== btrfs 健康檢查報告 ===")
            health_report = storage.check_btrfs_health()
            
            if isinstance(health_report, dict):
                for volume, status in health_report.items():
                    print(f"檔案系統: {volume}")
                    print(f"狀態: {status['status']}")
                    
                    if status['status'] != 'healthy':
                        print(f"⚠️  警告: {volume} 狀態異常")
                        print(f"詳細資訊: {status.get('details', 'N/A')}")
                        
                        # 如果發現問題，建立緊急快照
                        print(f"建立緊急快照...")
                        storage.snapshot_btrfs_volume(volume)
                        
                        # 檢查是否需要修復
                        if 'raid_degraded' in status.get('issues', []):
                            print(f"RAID陣列降級，需要修復")
                            # 這裡可以觸發修復流程
                    else:
                        print(f"✅ {volume} 狀態良好")
                        
            else:
                print(f"健康檢查結果: {health_report}")
                
        except Exception as e:
            print(f"健康檢查時發生錯誤: {e}")
    
    # 定期執行健康檢查
    while True:
        check_system_health()
        print("下次檢查將在1小時後執行...")
        time.sleep(3600)  # 每小時檢查一次

# 立即執行一次健康檢查
health_report = storage.check_btrfs_health()
print(f"當前系統健康狀況: {health_report}")
```
#### 錯誤處理
```python
try:
    health_report = check_btrfs_health()
except Exception as e:
    print(f"Error checking btrfs health: {e}")
```

### monitor_disk_usage()
- 描述: 監控 /Storage 或 /Backup 目錄下子目錄的磁碟使用量，必要時發警告或自動刪除最舊快照
- 參數: 無
- 回傳值: 無
#### 範例
```python
monitor_disk_usage()
```
#### 實際應用場景範例
```python
import storage
import time

def disk_usage_monitor():
    """磁碟使用量監控系統"""
    try:
        print("啟動磁碟使用量監控...")
        
        while True:
            volumes = storage.list_btrfs_volumes()
            
            for volume in volumes:
                usage = storage.get_disk_usage(volume)
                print(f"{volume} 使用率: {usage}%")
                
                # 設定警告閾值
                if usage > 85:
                    print(f"🔴 緊急警告: {volume} 使用率超過85%")
                    
                    # 自動清理舊快照
                    snapshots = storage.list_snapshots(volume)
                    if len(snapshots) > 5:
                        # 保留最新5個快照
                        old_snapshots = snapshots[:-5]
                        for old_snapshot in old_snapshots:
                            storage.delete_snapshot(volume, old_snapshot)
                            print(f"已清理舊快照: {old_snapshot}")
                    
                elif usage > 70:
                    print(f"🟡 警告: {volume} 使用率超過70%")
                    
                elif usage > 50:
                    print(f"🟢 注意: {volume} 使用率: {usage}%")
                    
            # 每10分鐘檢查一次
            time.sleep(600)
            
    except Exception as e:
        print(f"監控磁碟使用量時發生錯誤: {e}")

# 執行監控
storage.monitor_disk_usage()
```
#### 錯誤處理
```python
try:
    monitor_disk_usage()
except Exception as e:
    print(f"Error monitoring disk usage: {e}")
```

### repair_btrfs_volume(name, disk)
- 描述: 利用可用磁碟修復 btrfs RAID5/RAID6
- 參數:
  - name: btrfs 檔案系統名稱
  - disk: 用於修復的磁碟
- 回傳值: 無
#### 範例
```python
repair_btrfs_volume("MyVolume", "/dev/sdd")
```
#### 實際應用場景範例
```python
import storage
def raid_repair_system():
    """RAID修復系統"""
    try:
        volume_name = "ProductionData"
        replacement_disk = "/dev/sde"
        
        # 1. 檢查檔案系統健康狀況
        health = storage.check_btrfs_health()
        if volume_name in health and 'degraded' in health[volume_name].get('status', ''):
            print(f"🔴 檢測到 {volume_name} RAID陣列降級")
            
            # 2. 檢查可用磁碟
            print(f"準備使用磁碟 {replacement_disk} 進行修復")
            
            # 3. 建立修復前快照
            print("建立修復前快照...")
            storage.snapshot_btrfs_volume(volume_name)
            
            # 4. 執行RAID修復
            print("開始RAID修復...")
            storage.repair_btrfs_volume(volume_name, replacement_disk)
            
            # 5. 驗證修復結果
            new_health = storage.check_btrfs_health()
            if 'healthy' in new_health[volume_name].get('status', ''):
                print("✅ RAID修復完成，系統狀態正常")
            else:
                print("❌ RAID修復可能未完全成功，請檢查系統狀態")
                
        else:
            print("✅ RAID狀態正常，無需修復")
            
    except Exception as e:
        print(f"RAID修復過程中發生錯誤: {e}")

raid_repair_system()
```
#### 錯誤處理
```python
try:
    repair_btrfs_volume("MyVolume", "/dev/sdd")
except Exception as e:
    print(f"Error repairing btrfs volume: {e}")
```

### list_snapshots(name)
- 描述: 列出 btrfs 檔案系統所有快照
- 參數:
  - name: btrfs 檔案系統名稱
- 回傳值: 快照列表
#### 範例
```python
snapshots = list_snapshots("MyVolume")
print(snapshots)
```
#### 實際應用場景範例
```python
import storage
def snapshot_management():
    """快照管理系統"""
    try:
        volumes = storage.list_btrfs_volumes()
        
        for volume in volumes:
            print(f"\n=== {volume} 快照管理 ===")
            snapshots = storage.list_snapshots(volume)
            
            if snapshots:
                print(f"發現 {len(snapshots)} 個快照:")
                
                # 依時間排序顯示快照
                for i, snapshot in enumerate(snapshots):
                    print(f"{i+1}. {snapshot}")
                    
                # 分析快照使用情況
                if len(snapshots) > 50:
                    print("⚠️  快照數量過多，建議清理舊快照")
                elif len(snapshots) < 3:
                    print("💡 建議增加快照頻率以提供更好的資料保護")
                else:
                    print("✅ 快照數量適中")
                    
                # 顯示最新和最舊的快照
                print(f"最新快照: {snapshots[-1]}")
                print(f"最舊快照: {snapshots[0]}")
                
            else:
                print("📭 沒有找到快照")
                print("建議建立第一個快照...")
                storage.snapshot_btrfs_volume(volume)
                print("✅ 已建立初始快照")
                
    except Exception as e:
        print(f"快照管理時發生錯誤: {e}")

snapshot_management()
```
#### 錯誤處理
```python
try:
    snapshots = list_snapshots("MyVolume")
except Exception as e:
    print(f"Error listing snapshots: {e}")
```

### delete_snapshot(name, snapshot, dry_run=False)
### prune_snapshots(name, keep=30, max_age_days=None, dry_run=False)
- 描述: 根據數量與最長保留天數策略清理快照；回傳 `{removed: [...], kept: [...]}`。
- keep: 至少保留最新 N 個
- max_age_days: 早於此天數（透過快照前 14 碼時間戳判斷）會被列入清理
- dry_run: 僅模擬不執行刪除
#### 範例
```python
res = prune_snapshots('DataVolume', keep=15, max_age_days=30)
print(res)
```
#### 錯誤處理
```python
try:
    prune_snapshots('DataVolume', keep=10)
except Exception as e:
    print('快照清理失敗', e)
```
- 描述: 刪除 btrfs 檔案系統某一快照
- 參數:
  - name: btrfs 檔案系統名稱
  - snapshot: 要刪除的快照名稱
- 回傳值: 無
#### 範例
```python
delete_snapshot("MyVolume", "snapshot_20231001")
```
#### 實際應用場景範例
```python
import storage
import datetime

def snapshot_cleanup_policy():
    """智慧快照清理策略"""
    try:
        volumes = storage.list_btrfs_volumes()
        current_time = datetime.datetime.now()
        
        for volume in volumes:
            snapshots = storage.list_snapshots(volume)
            print(f"\n處理 {volume} 的快照清理...")
            
            if len(snapshots) <= 10:
                print(f"快照數量 ({len(snapshots)}) 不足，跳過清理")
                continue
                
            # 清理策略：
            # - 保留最近7天的所有快照
            # - 保留最近30天內每週一個快照
            # - 保留最近6個月內每月一個快照
            # - 刪除其他快照
            
            snapshots_to_keep = set()
            snapshots_to_delete = []
            
            # 保留最近10個快照（確保有足夠備份）
            snapshots_to_keep.update(snapshots[-10:])
            
            for snapshot in snapshots:
                # 解析快照時間（假設格式包含日期）
                if '2023' in snapshot or '2024' in snapshot:  # 簡化的日期檢查
                    if snapshot not in snapshots_to_keep:
                        snapshots_to_delete.append(snapshot)
            
            # 執行清理
            for snapshot in snapshots_to_delete[:-5]:  # 保留一些額外的快照
                print(f"刪除舊快照: {snapshot}")
                storage.delete_snapshot(volume, snapshot)
                
            print(f"✅ {volume} 快照清理完成")
            
    except Exception as e:
        print(f"快照清理時發生錯誤: {e}")

snapshot_cleanup_policy()
```
#### 錯誤處理
```python
try:
    delete_snapshot("MyVolume", "snapshot_20231001")
except Exception as e:
    print(f"Error deleting snapshot: {e}")
```

### get_volume_info(name)
- 描述: 取得 btrfs 檔案系統詳細資訊
- 參數:
  - name: btrfs 檔案系統名稱
- 回傳值: 詳細資訊 dict
#### 範例
```python
info = get_volume_info("MyVolume")
print(info)
```
#### 實際應用場景範例
```python
import storage
def system_inventory():
    """系統清單與狀態報告"""
    try:
        volumes = storage.list_btrfs_volumes()
        
        print("=== btrfs 檔案系統清單報告 ===")
        total_capacity = 0
        total_used = 0
        
        for volume in volumes:
            info = storage.get_volume_info(volume)
            usage = storage.get_disk_usage(volume)
            snapshots = storage.list_snapshots(volume)
            
            print(f"\n📁 檔案系統: {volume}")
            print(f"   RAID等級: {info.get('raid_level', 'unknown')}")
            print(f"   總容量: {info.get('total_size', 'unknown')} GB")
            print(f"   已使用: {info.get('used_size', 'unknown')} GB")
            print(f"   使用率: {usage}%")
            print(f"   快照數量: {len(snapshots)}")
            print(f"   設備數量: {len(info.get('devices', []))}")
            print(f"   掛載點: {info.get('mount_point', 'unknown')}")
            print(f"   狀態: {info.get('status', 'unknown')}")
            
            # 累計統計
            if isinstance(info.get('total_size'), (int, float)):
                total_capacity += info['total_size']
            if isinstance(info.get('used_size'), (int, float)):
                total_used += info['used_size']
        
        print(f"\n=== 總計統計 ===")
        print(f"檔案系統數量: {len(volumes)}")
        print(f"總容量: {total_capacity} GB")
        print(f"已使用: {total_used} GB")
        print(f"整體使用率: {(total_used/total_capacity*100):.1f}%")
        
    except Exception as e:
        print(f"產生系統清單時發生錯誤: {e}")

system_inventory()
```
#### 錯誤處理
```python
try:
    info = get_volume_info("MyVolume")
except Exception as e:
    print(f"Error getting volume info: {e}")
```

### get_disk_usage(name)
- 描述: 取得 /Storage 或 /Backup 子目錄的磁碟使用量
- 參數:
  - name: btrfs 檔案系統名稱
- 回傳值: 磁碟使用量百分比
#### 範例
```python
usage = get_disk_usage("MyVolume")
print(f"Disk usage: {usage}%")
```
#### 實際應用場景範例
```python
import storage
import time

def usage_monitoring_dashboard():
    """使用量監控儀表板"""
    try:
        while True:
            print("\n" + "="*50)
            print("📊 磁碟使用量監控儀表板")
            print("="*50)
            
            volumes = storage.list_btrfs_volumes()
            alert_volumes = []
            
            for volume in volumes:
                usage = storage.get_disk_usage(volume)
                
                # 狀態指示器
                if usage > 90:
                    status = "🔴 危險"
                    alert_volumes.append((volume, usage, "critical"))
                elif usage > 80:
                    status = "🟡 警告"
                    alert_volumes.append((volume, usage, "warning"))
                elif usage > 60:
                    status = "🟢 注意"
                else:
                    status = "✅ 正常"
                
                # 進度條顯示
                bar_length = 30
                filled_length = int(bar_length * usage // 100)
                bar = "█" * filled_length + "░" * (bar_length - filled_length)
                
                print(f"{volume:15} [{bar}] {usage:3.1f}% {status}")
            
            # 警告處理
            if alert_volumes:
                print(f"\n⚠️  需要注意的檔案系統:")
                for vol, usage, level in alert_volumes:
                    print(f"   {vol}: {usage}% ({level})")
                    
                    if level == "critical":
                        # 自動清理快照
                        snapshots = storage.list_snapshots(vol)
                        if len(snapshots) > 3:
                            old_snapshot = snapshots[0]
                            storage.delete_snapshot(vol, old_snapshot)
                            print(f"   自動刪除舊快照: {old_snapshot}")
            
            print(f"\n更新時間: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print("按 Ctrl+C 結束監控...")
            
            time.sleep(60)  # 每分鐘更新一次
            
    except KeyboardInterrupt:
        print("\n監控已停止")
    except Exception as e:
        print(f"監控過程中發生錯誤: {e}")

usage_monitoring_dashboard()
```
#### 錯誤處理
```python
try:
    usage = get_disk_usage("MyVolume")
except Exception as e:
    print(f"Error getting disk usage: {e}")
```

### validate_btrfs_volume(name)
- 描述: 驗證 btrfs volume 的完整性和狀態
- 參數:
  - name: btrfs 檔案系統名稱
- 回傳值: 驗證結果 dict，包含 valid, errors, warnings, info 等欄位
#### 範例
```python
result = validate_btrfs_volume("MyVolume")
if result['valid']:
    print("Volume is healthy")
else:
    print(f"Errors: {result['errors']}")
```
#### 實際應用場景範例
```python
import storage

def daily_volume_check():
    """每日檔案系統檢查"""
    volumes = storage.list_btrfs_volumes()
    
    for volume in volumes:
        name = volume.get('name')
        if not name:
            continue
            
        print(f"\n檢查 volume: {name}")
        result = storage.validate_btrfs_volume(name)
        
        if result['valid']:
            print("✅ 狀態正常")
        else:
            print("❌ 發現問題:")
            for error in result['errors']:
                print(f"  - 錯誤: {error}")
        
        if result['warnings']:
            print("⚠️  警告:")
            for warning in result['warnings']:
                print(f"  - {warning}")
```
#### 錯誤處理
```python
try:
    result = validate_btrfs_volume("MyVolume")
except Exception as e:
    print(f"Error validating volume: {e}")
```

### get_storage_summary()
- 描述: 取得整個儲存系統的總覽資訊
- 參數: 無
- 回傳值: 包含總容量、使用量、volume 數量等統計資訊的 dict
#### 範例
```python
summary = get_storage_summary()
print(f"Total volumes: {summary['total_volumes']}")
print(f"Healthy volumes: {summary['healthy_volumes']}")
```
#### 實際應用場景範例
```python
import storage

def generate_storage_report():
    """產生儲存系統報告"""
    summary = storage.get_storage_summary()
    
    print("=== 儲存系統總覽 ===")
    print(f"檔案系統總數: {summary['total_volumes']}")
    print(f"健康狀態: {summary['healthy_volumes']}")
    print(f"降級狀態: {summary['degraded_volumes']}")
    print(f"總容量: {summary['total_capacity_gb']} GB")
    print(f"已使用: {summary['total_used_gb']} GB")
    print(f"快照總數: {summary['total_snapshots']}")
    
    print("\n=== 各 Volume 詳細資訊 ===")
    for vol in summary['volumes']:
        status_icon = "✅" if vol['status'] == 'healthy' else "❌"
        print(f"{status_icon} {vol['name']}: {vol['usage_percent']:.1f}% 使用, {vol['snapshots_count']} 個快照")
```
#### 錯誤處理
```python
try:
    summary = get_storage_summary()
except Exception as e:
    print(f"Error getting storage summary: {e}")
```

---

## CLI 介面

可用指令（假設已安裝 storage.py 為 CLI 工具）：

```bash
# 列出所有 btrfs volume
python -m storage list

# 建立新 volume
python -m storage create --name MyVolume --devices /dev/sdb,/dev/sdc --raid raid5

# 刪除 volume
python -m storage delete --name MyVolume

# 建立快照（附 label）
python -m storage snapshot --name MyVolume --label nightly
python -m storage snapshot --name MyVolume --label test --dry-run

# 還原快照（dry-run 預覽）
python -m storage restore --name MyVolume --snapshot 20250101030001_ro --dry-run

# 檢查健康狀態
python -m storage health

# 監控磁碟用量
python -m storage monitor

# 修復 RAID（dry-run）
python -m storage repair --name MyVolume --disk /dev/sdd --dry-run

# 列出快照
python -m storage list-snapshots --name MyVolume

# 刪除快照（dry-run）
python -m storage delete-snapshot --name MyVolume --snapshot 20250101030001_ro --dry-run

# 清理快照
python -m storage prune-snapshots --name MyVolume --keep 20 --max-age-days 14

# 查詢 volume 資訊
python -m storage info --name MyVolume

# 查詢磁碟用量
python -m storage usage --name MyVolume

# 驗證 volume 狀態
python -m storage validate --name MyVolume

# 顯示儲存系統總覽
python -m storage summary
```

---

## 依賴與環境

- Ubuntu 24.04 Desktop
- Python 3.10+
- btrfs-progs (系統工具)
- 需 root 權限操作部分功能
- Python 套件：psutil、subprocess、shutil、logging、schedule 等

---

## 常見問題 FAQ

**Q1: 為什麼建立 volume 會失敗？**
A: 請確認所有指定磁碟未掛載且無資料，且有 root 權限。

**Q2: 快照還原後資料不一致？**
A: 請確認快照建立時 volume 未在大量寫入，建議先暫停應用程式。

**Q3: RAID 修復無效？**
A: 請確認新磁碟型號、容量與原磁碟一致，且已正確插入。

**Q4: CLI 執行權限不足？**
A: 請以 sudo 執行，或檢查 Python 執行環境權限。

---

## 最佳實踐與建議

- 定期建立快照並備份至異地。
- 監控磁碟用量，設置自動快照清理。
- 重要資料 volume 請使用 RAID5/6 並定期健康檢查。
- 操作前先備份重要資料，避免誤刪。
- 透過 log 機制記錄所有異常與操作紀錄。

---

## 常見錯誤與排解

- `OSError: Device or resource busy`：請先卸載該磁碟。
- `PermissionError: Operation not permitted`：請以 root 權限執行。
- `ValueError: Invalid RAID level`：請檢查 RAID 參數拼寫。
- `FileNotFoundError: btrfs command not found`：請安裝 btrfs-progs。

---

## 完整範例程式碼

```python
#!/usr/bin/env python3
"""
完整的 btrfs 儲存管理系統範例
展示如何使用 storage.py 模組建立企業級儲存解決方案
"""

import storage
import time
import schedule
import logging
import datetime

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/storage_manager.log'),
        logging.StreamHandler()
    ]
)

class StorageManager:
    """儲存管理系統類別"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def initialize_storage_system(self):
        """初始化儲存系統"""
        try:
            self.logger.info("開始初始化儲存系統...")
            
            # 1. 檢查現有檔案系統
            existing_volumes = storage.list_btrfs_volumes()
            self.logger.info(f"發現現有檔案系統: {existing_volumes}")
            
            # 2. 建立主要儲存檔案系統（如果不存在）
            if 'MainStorage' not in existing_volumes:
                devices = ['/dev/sdb', '/dev/sdc', '/dev/sdd']
                self.logger.info("建立主要儲存檔案系統...")
                storage.create_btrfs_volume('MainStorage', devices, raid_level='raid5')
                
                # 建立初始快照
                storage.snapshot_btrfs_volume('MainStorage')
                self.logger.info("主要儲存系統建立完成")
            
            # 3. 建立備份檔案系統（如果不存在）
            if 'BackupStorage' not in existing_volumes:
                backup_devices = ['/dev/sde', '/dev/sdf']
                self.logger.info("建立備份儲存檔案系統...")
                storage.create_btrfs_volume('BackupStorage', backup_devices, raid_level='raid1')
                storage.snapshot_btrfs_volume('BackupStorage')
                self.logger.info("備份儲存系統建立完成")
                
            self.logger.info("儲存系統初始化完成")
            
        except Exception as e:
            self.logger.error(f"初始化儲存系統時發生錯誤: {e}")
    
    def daily_maintenance(self):
        """每日維護任務"""
        try:
            self.logger.info("開始執行每日維護任務...")
            
            # 1. 健康檢查
            health_report = storage.check_btrfs_health()
            self.logger.info(f"健康檢查結果: {health_report}")
            
            # 2. 建立每日快照
            volumes = storage.list_btrfs_volumes()
            for volume in volumes:
                storage.snapshot_btrfs_volume(volume)
                self.logger.info(f"已為 {volume} 建立每日快照")
            
            # 3. 清理舊快照
            self.cleanup_old_snapshots()
            
            # 4. 監控磁碟使用量
            self.check_disk_usage()
            
            self.logger.info("每日維護任務完成")
            
        except Exception as e:
            self.logger.error(f"執行每日維護時發生錯誤: {e}")
    
    def cleanup_old_snapshots(self):
        """清理舊快照"""
        try:
            volumes = storage.list_btrfs_volumes()
            
            for volume in volumes:
                snapshots = storage.list_snapshots(volume)
                
                # 保留最近 30 個快照
                if len(snapshots) > 30:
                    old_snapshots = snapshots[:-30]
                    for old_snapshot in old_snapshots:
                        storage.delete_snapshot(volume, old_snapshot)
                        self.logger.info(f"已刪除舊快照: {volume}/{old_snapshot}")
                        
        except Exception as e:
            self.logger.error(f"清理舊快照時發生錯誤: {e}")
    
    def check_disk_usage(self):
        """檢查磁碟使用量"""
        try:
            volumes = storage.list_btrfs_volumes()
            
            for volume in volumes:
                usage = storage.get_disk_usage(volume)
                
                if usage > 85:
                    self.logger.warning(f"⚠️  {volume} 使用率過高: {usage}%")
                    # 觸發緊急清理
                    self.emergency_cleanup(volume)
                elif usage > 70:
                    self.logger.info(f"💡 {volume} 使用率: {usage}% (需要注意)")
                
        except Exception as e:
            self.logger.error(f"檢查磁碟使用量時發生錯誤: {e}")
    
    def emergency_cleanup(self, volume):
        """緊急清理"""
        try:
            self.logger.warning(f"對 {volume} 執行緊急清理...")
            
            # 刪除最舊的快照
            snapshots = storage.list_snapshots(volume)
            if len(snapshots) > 5:
                old_snapshots = snapshots[:len(snapshots)//2]  # 刪除一半的舊快照
                for snapshot in old_snapshots:
                    storage.delete_snapshot(volume, snapshot)
                    self.logger.info(f"緊急刪除快照: {snapshot}")
                    
        except Exception as e:
            self.logger.error(f"緊急清理時發生錯誤: {e}")
    
    def run_monitoring(self):
        """執行監控系統"""
        try:
            self.logger.info("啟動儲存監控系統...")
            
            # 設定定時任務
            schedule.every().day.at("02:00").do(self.daily_maintenance)
            schedule.every(30).minutes.do(self.check_disk_usage)
            schedule.every().hour.do(lambda: storage.check_btrfs_health())
            
            # 主監控迴圈
            while True:
                schedule.run_pending()
                time.sleep(60)  # 每分鐘檢查一次
                
        except KeyboardInterrupt:
            self.logger.info("監控系統已停止")
        except Exception as e:
            self.logger.error(f"監控系統發生錯誤: {e}")

def main():
    """主程式"""
    manager = StorageManager()
    
    # 初始化儲存系統
    manager.initialize_storage_system()
    
    # 立即執行一次維護檢查
    manager.daily_maintenance()
    
    # 啟動監控系統
    manager.run_monitoring()

if __name__ == "__main__":
    main()
```

### 簡化使用範例

```python
import storage

# 快速設定儲存系統
def quick_setup():
    # 建立RAID5檔案系統
    storage.create_btrfs_volume('MyData', ['/dev/sdb', '/dev/sdc', '/dev/sdd'], 'raid5')
    
    # 建立初始快照
    storage.snapshot_btrfs_volume('MyData')
    
    # 檢查狀態
    health = storage.check_btrfs_health()
    usage = storage.get_disk_usage('MyData')
    
    print(f"系統健康狀況: {health}")
    print(f"磁碟使用率: {usage}%")

quick_setup()
```

---

## 掛載與卸載行為約定

### 掛載目錄策略
- 預設資料型 volume 掛載至：`/storage/{volume_name}`
- 未來可支援用途標記（例如 `purpose='backup'`）時掛載至：`/backup/{volume_name}`
- 若目錄不存在會於掛載前以 `mkdir -p` 自動建立（預設權限 0755，可依系統安全策略調整）。
- 建議掛載選項：`compress=zstd,noatime`（需視實際負載調整）。

### 建立流程（create_btrfs_volume）建議實作步驟
1. 使用 `mkfs.btrfs` 建立多裝置或單裝置檔案系統，依 `raid_level` 組態加入 `-d` / `-m` 參數。
2. 解析新檔案系統 UUID（`btrfs filesystem show` 或 `blkid`）。
3. 建立掛載目錄 `/storage/{name}`（或策略性目錄）。
4. 嘗試掛載：`mount -t btrfs -o compress=zstd UUID=<uuid> /storage/{name}`。
5. 可選：更新 `/etc/fstab`：
    `UUID=<uuid>  /storage/{name}  btrfs  defaults,noatime,compress=zstd  0  0`
6. 建立初始快照（選擇性）。

### 卸載與刪除流程（delete_btrfs_volume）建議實作步驟
1. 確認掛載點是否仍被進程使用（可選：`lsof +f -- /storage/{name}`）。
2. 執行 `umount /storage/{name}`（必要時可支援 `--lazy` 或 `fuser -km` 作為最後手段，不建議預設使用）。
3. 移除 `/etc/fstab` 對應條目（若之前曾寫入）。
4. 刪除掛載目錄（若為系統建立且為空內容）。
5. 針對多裝置可執行清理或移除標記；必要時更新 btrfs metadata。

### 掛載失敗重試策略（建議）
- 預設重試 3 次，每次間隔 2 秒；適用於多裝置 RAID 建立後 udev 尚未即時就緒之情境。
- 重試仍失敗時於 log 中標記並回傳錯誤，呼叫端可再人工處理。

### 相關建議額外 API（可擴充）
- `mount_btrfs_volume(name, target_dir=None, purpose='data')`
- `umount_btrfs_volume(name, force=False)`
- `ensure_fstab_entry(uuid, mount_point, options)`
- `remove_fstab_entry(mount_point|uuid)`
- `retry_mount(name, attempts=3, delay=2)`

### 驗證掛載狀態建議依據
- `/proc/mounts` 或 `findmnt -no TARGET,SOURCE,FSTYPE /storage/{name}`
- `btrfs filesystem show` 之裝置與 UUID 對映
- `list_btrfs_volumes()` 輸出應同步上述結果，避免資訊不一致。

### 自動化測試建議案例
| 測試項目 | 步驟 | 驗證點 |
|----------|------|--------|
| 建立並掛載 | create_btrfs_volume | 目錄存在、已掛載、list_btrfs_volumes 含掛載點 |
| 重複建立保護 | 建立相同名稱 | 拋出例外或回傳錯誤碼 |
| 卸載與刪除 | delete_btrfs_volume | 掛載點消失、目錄移除、UUID 不再列出 |
| 掛載失敗重試 | 模擬 mount 失敗 | 日誌出現重試紀錄，最終失敗拋例外 |
| fstab 整合 | 建立後重開機（模擬） | 系統重新開機後自動掛載成功 |

### 常見錯誤與因應（掛載相關）
| 錯誤 | 可能原因 | 建議處理 |
|------|----------|----------|
| `mount: wrong fs type` | mkfs 未成功或裝置重複使用 | 重新檢查 mkfs 輸出、確認未被佔用 |
| `device is busy` | 仍有進程使用 | 使用 `lsof` 或 `fuser` 找出占用程序 |
| `cannot find UUID` | udev 尚未同步 | 等待 2 秒後重試，或手動指定裝置路徑 |
| `permission denied` | 權限不足 | 使用 sudo 或 root 執行 |

### 手動驗證指令參考
```bash
# 建立 volume 並自動掛載
sudo python -m storage create --name DataVol --devices /dev/sdb,/dev/sdc --raid raid1

# 確認掛載
mount | grep DataVol || findmnt /storage/DataVol
ls -ld /storage/DataVol

# 列出 volumes
python -m storage list

# 刪除 volume（自動卸載）
sudo python -m storage delete --name DataVol

# 驗證已卸載且目錄移除
mount | grep DataVol || echo '未掛載'
test -d /storage/DataVol || echo '目錄已移除'
```

---

## 注意事項與安全性考量

- 本模組需在具備 btrfs 支援的 Linux 系統上運行，請確認系統已安裝 btrfs-progs
- 部分操作需 root 權限，請以 sudo 或 root 身份執行相關指令
- 請確保系統安全更新，避免已知漏洞影響 btrfs 操作
- 定期檢查並更新 storage.py 模組以獲取最新功能與修復
- 操作前請先備份重要資料，避免意外資料遺失
- RAID修復操作前請確認新磁碟的相容性和容量

## 版本資訊

- 適用於 Ubuntu 24.04 Desktop
- Python 3.10 以上
- btrfs-progs 6.x

## 相依性

### Python 套件
- psutil (系統資訊)
- schedule (定時任務)
- 標準庫: logging, subprocess, shutil, os, datetime, time, re, glob, tempfile, threading, typing, pathlib, collections, json, functools, signal, sys, stat, pwd, grp, errno, contextlib, platform

### 系統套件
```bash
# Ubuntu/Debian 安裝指令
sudo apt update
sudo apt install btrfs-progs python3-psutil

# Python 套件安裝
pip3 install schedule
```