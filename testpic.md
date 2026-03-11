graph TD
    subgraph GCP [GCP 雲端基礎設施]
        subgraph Docker [Docker 容器化環境]
            direction TB
            
            %% 資料管線
            Scrapy[Scrapy 爬蟲\n(抓取人力銀行資料)] -->|原始非結構化資料| MinIO[(MinIO\n物件儲存)]
            MinIO -->|讀取| ETL[Python ETL\n(資料清洗與轉換)]
            ETL -->|乾淨結構化資料| MySQL[(MySQL\n關聯式資料庫)]
            
            %% 應用與前端
            MySQL <-->|數據查詢 & 帳密驗證| Streamlit[Streamlit 前端介面\n(互動式資料視覺化)]
            
            %% 系統功能
            subgraph Features [核心系統功能]
                F1(職務技能需求表 Top.10)
                F2(技能適配度與薪資落點檢測)
                F3(後臺註冊與登入機制)
            end
            Streamlit --- Features
        end
    end
    
    User((轉職者 / 使用者)) <-->|操作與檢視| Streamlit