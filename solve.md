專案難題與解決方案總結
一、 資料架構與 ETL 穩定性 (Data Integrity & ETL Pipeline)

1. 破解資料庫「無聲失敗」：
挑戰： 使用 INSERT IGNORE 導致寫入衝突時資料直接消失，卻沒有報錯。
解決： 重新梳理資料表相依性，建立嚴格的「父節點先於子節點」寫入順序。開發時適時關閉外鍵檢查進行壓力測試，確保管線在正式環境的純淨度。

2. 高階「記憶體字典」對應機制：
挑戰： API 回傳的是字串代碼（如 job_code），但資料庫正規化要求寫入整數 id。
解決： 堅持 3NF 正規化設計。在批次處理中實作 In-Memory Cache，利用 Python 字典進行 ID 快速「兌換」，避免頻繁敲擊資料庫，在維持資料品質的同時兼顧效能。

3. 真實世界資料的邊界處理：
挑戰： 爬蟲資料極度不穩定，常出現 NoneType 導致崩潰。
解決： 導入防禦性編程，利用 .get() or [] 等 Fallback 機制處理缺失值，確保 ETL 流程在遇到髒資料時具備自癒與容錯能力。

二、 極端環境下的效能優化 (Performance Optimization in Constraints)
1. 雲端記憶體管理與 OOM 救援：
挑戰： 1GB 記憶體被龐大 SQL 檔與 Docker 塞爆，導致 VM 鎖死（OOM）。
解決：
系統層： 手動建立 2GB Swap 虛擬記憶體作為硬體緩衝。
維運層： 修改部署策略，拔除自動匯入腳本，改用 cat 手動緩步灌入資料。

2. Streamlit 互動效能調優：
挑戰： 使用者每次互動都會觸發 SQL 重新連線，導致 CPU 噴高。
解決： 實作 Connection Pool (連線池) 與 @st.cache_data。透過 max_entries 與 ttl 嚴格控管快取數量，避免快取反向吞噬記憶體，達到互動流暢與資源負載的平衡。

三、 生態系與相容性除錯 (DevOps & Environment Parity)
1. Docker 跨版本衝突：
挑戰： 遭遇 KeyError: 'ContainerConfig'，主因是 Docker Compose 版本與 Image 結構不相容。
解決： 迅速定位工具版本落差，手動升級 Docker Compose V2，並清理殘留容器鏡像，達成開發環境與部署環境的對齊。

2. Python 相依性深度除錯：
挑戰： Docker 映像檔 Python 版本過舊（3.9），與現代 Pandas（>3.11）不相容。
解決： 重構 Dockerfile，更新基底映像檔並優化 requirements.txt。同時處理 C 語言編譯環境問題（build-essential）與套件（bcrypt, numpy）衝突。

四、 工程細節與觀測性 (Observability & Engineering Best Practices)
1. 效能與監控的平衡：
挑戰： 十六萬筆資料處理時，頻繁 print 導致 I/O 拖慢速度。
解決： 利用「取餘數」技巧（% 1000）實作進度監控，在「觀測程式進度」與「執行效率」間取得平衡。

2. 資料庫鎖定與跳號理解：
挑戰： Auto Increment ID 不連續。
解決： 深入研究 MySQL 並發寫入機制，理解 INSERT IGNORE 對序號的預先配發。解決 ID 與邏輯撞車的問題，並手動重設 auto_increment = 1000 避開邏輯地雷。