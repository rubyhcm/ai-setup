```graph TD
    classDef database fill:#f9f,stroke:#333,stroke-width:2px;
    classDef process fill:#bbf,stroke:#333,stroke-width:2px;
    classDef decision fill:#fdb,stroke:#333,stroke-width:2px;
    classDef reward fill:#dfd,stroke:#333,stroke-width:2px;
    classDef penalty fill:#fdd,stroke:#333,stroke-width:2px;

    %% Giai đoạn 1: Chuẩn bị dữ liệu
    subgraph Giai đoạn 1: Chuẩn bị & Trích xuất
        Input[(Dữ liệu đầu vào<br/>1000 Benign + Malware)] --> Split{Phân loại}
        Split -->|Nhãn 0| BenignPool[(Tập Benign<br/>Template Vật chủ)]:::database
        Split -->|Nhãn 1| MalwarePool[(Tập Malware<br/>Mã độc gốc)]:::database
        
        MalwarePool --> Extractor[Trình Phân tích Tĩnh<br/>Trích xuất JS/Action Payload]:::process
        Extractor --> PayloadPool[(Kho Payload<br/>Độc hại)]:::database
    end

    %% Giai đoạn 2: Xây dựng Thẩm phán
    subgraph Giai đoạn 2: Xây dựng Surrogate Model
        BenignPool -.-> FeatExt[Trích xuất Đặc trưng X<br/>Cấu trúc, Entropy, Từ khóa...]:::process
        MalwarePool -.-> FeatExt
        FeatExt --> TrainModel[Huấn luyện Mô hình Phân loại<br/>Surrogate Model F_X]:::process
    end

    %% Giai đoạn 3: Vòng lặp Đối kháng
    subgraph Giai đoạn 3: Vòng lặp Đối kháng LLM + RL
        PayloadPool --> LLM[LLM Tác nhân Nội dung<br/>Viết lại, làm rối mã - Obfuscation]:::process
        LLM --> MutatedPayload[Payload Đa hình]
        
        BenignPool --> Host[File Benign Vật chủ]
        
        Host --> RLEnv[Môi trường RL]
        MutatedPayload --> RLEnv
        
        RLEnv --> RLAgent{RL Agent<br/>Quyết định vị trí &<br/>Cách chèn Action A_t}:::decision
        RLAgent --> MutatedPDF[File PDF Biến thể x']
        
        MutatedPDF --> Validator{Gate 1: Validation<br/>File có mở được không?}:::decision
        Validator -->|Không/Lỗi Cấu trúc| Penalty1[Phạt nặng R = -10]:::penalty
        
        Validator -->|Có/Hợp lệ| SurrogateCheck{Gate 2: Detection<br/>Gửi vào Surrogate Model}:::decision
        TrainModel -.-> SurrogateCheck
        
        SurrogateCheck -->|Bị phát hiện F_x'=1| Penalty2[Phạt nhẹ R = -1]:::penalty
        SurrogateCheck -->|Né thành công F_x'=0| RewardBig[Thưởng lớn R = +10]:::reward
        
        RewardBig --> Save[(Lưu vào Tập<br/>Evasive PDF)]:::database
        
        Penalty1 --> Update[Cập nhật Policy/Q-Value]:::process
        Penalty2 --> Update
        RewardBig --> Update
        
        Update -.->|Lặp lại vòng huấn luyện| RLAgent
    end
```