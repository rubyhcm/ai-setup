```
graph TD
    classDef database fill:#f9f,stroke:#333,stroke-width:2px;
    classDef process fill:#bbf,stroke:#333,stroke-width:2px;
    classDef decision fill:#fdb,stroke:#333,stroke-width:2px;
    classDef reward fill:#dfd,stroke:#333,stroke-width:2px;
    classDef penalty fill:#fdd,stroke:#333,stroke-width:2px;

    %% Khối dữ liệu
    subgraph Data_Source [Nguồn Dữ Liệu]
        B[(Tập Benign)]:::database --> B_Ext[Trích xuất Đặc trưng Lành tính <br/>Metadata, Obj-Tree, Fonts]
        M[(Tập Malware)]:::database --> M_Ext[Trích xuất Payload Độc hại <br/>JavaScript, OpenAction]
    end

    B_Ext --> FeaturePool[(Kho Đặc trưng Lành tính)]:::database

    %% Vòng lặp RL
    subgraph RL_Environment [Môi trường Học tăng cường]
        M_Ext --> State[Trạng thái S_t: <br/>Cấu trúc Malware hiện tại]:::process
        
        State --> Agent{RL Agent <br/> Policy Network}:::decision
        
        FeaturePool --> Agent
        
        Agent --> Action[Hành động A_t: <br/>Chọn & Chèn Đặc trưng Benign]
        
        Action --> Mutated[PDF Biến thể Mimicry x']
        
        %% Kiểm thử kép
        Mutated --> Validator{Gate 1: Validation <br/>File còn hoạt động?}:::decision
        
        Validator -->|Lỗi Cấu trúc| Penalty1[Phạt nặng R = -10]:::penalty
        
        Validator -->|Hợp lệ| Detector{Gate 2: Detection <br/>AI-based Surrogate}:::decision
        
        Detector -->|Vẫn bị phát hiện| Penalty2[Phạt nhẹ R = -1 <br/>Chưa đủ giống Benign]:::penalty
        Detector -->|Né thành công| RewardBig[Thưởng lớn R = +10 <br/>Mimicry Hoàn hảo]:::reward
        
        Penalty1 --> Update[Cập nhật Agent <br/>DQN/PPO]:::process
        Penalty2 --> Update
        RewardBig --> Update
        
        Update -.->|Vòng lặp| State
    end

    RewardBig --> Output[(Dataset Mã độc <br/>Đối kháng mô phỏng)]:::database
```