# Architecture: gRPC User Management System

## System Diagram - Layered Architecture

```mermaid
graph TB
    Client["gRPC Client"]

    subgraph "Handler Layer"
        Auth["Auth Handler"]
        User["User Handler"]
        Middleware["Auth Middleware"]
    end

    subgraph "Service Layer"
        UserSvc["UserService"]
    end

    subgraph "Repository Layer"
        UserRepo["PostgresUserRepository"]
    end

    subgraph "Domain Layer"
        UserEntity["User Entity"]
        UserVO["Email ValueObject"]
        DomainErr["Domain Errors"]
    end

    subgraph "Infrastructure"
        DB["PostgreSQL Database"]
        Crypto["Crypto: bcrypt, JWT/RS256"]
        Logger["Structured Logger"]
    end

    Client -->|"Register/Login"| Auth
    Client -->|"Get User Info"| User
    User --> Middleware
    Middleware --> UserSvc
    Auth --> UserSvc
    UserSvc --> UserRepo
    UserSvc --> Crypto
    UserSvc --> Logger
    UserRepo --> DB
    UserRepo --> Logger
    UserEntity --> UserVO
    UserEntity --> DomainErr
```

## Dependency Graph

```mermaid
graph TB
    subgraph "Allowed Dependencies"
        Handler["Handler Layer"] --> Service["Service Layer"]
        Service --> Repository["Repository Layer"]
        Service --> Infra["Infrastructure"]
        Repository --> Domain["Domain Layer"]
        Infra --> Domain
    end

    subgraph "Forbidden"
        ForbiddenHandler["❌ Handler → Domain<br/>❌ Handler → Repo"]
        ForbiddenService["❌ Service → Handler"]
        ForbiddenDomain["❌ Domain → Service<br/>❌ Domain → Repo<br/>❌ Domain → Infra"]
    end

    style Handler fill:#90EE90
    style Service fill:#90EE90
    style Repository fill:#90EE90
    style Infra fill:#90EE90
    style Domain fill:#90EE90
    style ForbiddenHandler fill:#FFB6C1
    style ForbiddenService fill:#FFB6C1
    style ForbiddenDomain fill:#FFB6C1
```

## Registration Flow Sequence

```mermaid
sequenceDiagram
    participant Client as gRPC Client
    participant Handler as AuthHandler
    participant Service as UserService
    participant Repo as Repository
    participant DB as PostgreSQL
    participant Crypto as Crypto/bcrypt

    Client->>Handler: RegisterUser(email, name, password)
    Handler->>Handler: Validate input (email, password constraints)
    Handler->>Service: Register(ctx, email, name, password)
    Service->>Service: Validate business rules (email format)
    Service->>Repo: FindByEmail(ctx, email)
    Repo->>DB: Query user by email
    DB-->>Repo: null (not found)
    Repo-->>Service: nil, nil
    Service->>Crypto: Hash password with bcrypt
    Crypto-->>Service: password_hash
    Service->>Repo: Save(ctx, user)
    Repo->>DB: INSERT into users
    DB-->>Repo: user_id
    Repo-->>Service: nil
    Service-->>Handler: user (id, email, name), nil
    Handler-->>Client: RegisterUserResponse (user_id, email)
```

## Login & JWT Generation Flow

```mermaid
sequenceDiagram
    participant Client as gRPC Client
    participant Handler as AuthHandler
    participant Service as UserService
    participant Repo as Repository
    participant DB as PostgreSQL
    participant Crypto as Crypto/JWT

    Client->>Handler: LoginUser(email, password)
    Handler->>Handler: Validate input
    Handler->>Service: Login(ctx, email, password)
    Service->>Repo: FindByEmail(ctx, email)
    Repo->>DB: Query user by email
    DB-->>Repo: user record
    Repo-->>Service: user, nil
    Service->>Crypto: Verify password with bcrypt
    Crypto-->>Service: true, nil
    Service->>Crypto: Generate JWT token (RS256)
    Crypto-->>Service: token string
    Service-->>Handler: user, token, nil
    Handler-->>Client: LoginUserResponse (user_id, email, token)
```

## User Info Retrieval with Auth

```mermaid
sequenceDiagram
    participant Client as gRPC Client
    participant Middleware as AuthMiddleware
    participant Handler as UserHandler
    participant Service as UserService
    participant Repo as Repository
    participant DB as PostgreSQL

    Client->>Middleware: GetUserInfo(user_id) + JWT Token
    Middleware->>Middleware: Parse and validate JWT
    Middleware->>Middleware: Extract user_id from token
    Middleware->>Handler: Context + user_id
    Handler->>Service: GetByID(ctx, user_id)
    Service->>Repo: FindByID(ctx, user_id)
    Repo->>DB: Query user by id
    DB-->>Repo: user record
    Repo-->>Service: user, nil
    Service-->>Handler: user, nil
    Handler-->>Client: GetUserInfoResponse (user_id, email, name)
```

## Domain Model Class Diagram

```mermaid
classDiagram
    class User {
        +string ID
        +Email Email
        +string Name
        +string PasswordHash
        +time.Time CreatedAt
        +time.Time UpdatedAt
    }

    class Email {
        -string value
        +String() string
        +IsValid() bool
    }

    class UserService {
        +Register(ctx, email, name, password) *User, error
        +Login(ctx, email, password) *User, string, error
        +GetByID(ctx, userID) *User, error
        -validateEmail(email) error
        -validatePassword(password) error
    }

    class UserRepository {
        <<interface>>
        +FindByID(ctx, id) *User, error
        +FindByEmail(ctx, email) *User, error
        +Save(ctx, user) error
    }

    class PostgresUserRepository {
        -db *sql.DB
        -logger *slog.Logger
        +FindByID(ctx, id) *User, error
        +FindByEmail(ctx, email) *User, error
        +Save(ctx, user) error
    }

    class AuthHandler {
        -userService UserService
        -logger *slog.Logger
        +Register(ctx, req) *pb.RegisterResponse, error
        +Login(ctx, req) *pb.LoginResponse, error
    }

    class UserHandler {
        -userService UserService
        -logger *slog.Logger
        +GetUserInfo(ctx, req) *pb.GetUserInfoResponse, error
    }

    class AuthMiddleware {
        -publicKey *rsa.PublicKey
        -logger *slog.Logger
        +ValidateToken(ctx, token) context.Context, error
        +UnaryInterceptor() grpc.UnaryServerInterceptor
    }

    UserService --> UserRepository: "depends on"
    UserService --> Email: "uses"
    AuthHandler --> UserService: "depends on"
    UserHandler --> UserService: "depends on"
    AuthMiddleware --> "validates JWT"
    User --> Email: "contains"
    PostgresUserRepository --> UserRepository: "implements"
```

## Error Handling Flow

```mermaid
graph TB
    Input["User Input"]
    Validate["Handler Layer<br/>Validation"]
    ValidErr{"Valid?"}
    BadRequest["Return 400<br/>Bad Request"]
    Service["Service Layer<br/>Business Logic"]
    BizErr{"Business<br/>Rules OK?"}
    DomainErr["Return domain error"]
    Repo["Repository Layer<br/>Data Access"]
    RepoErr{"Success?"}
    InternalErr["Return 500<br/>Internal Error"]
    Success["Return 200/201<br/>Success Response"]

    Input --> Validate
    Validate --> ValidErr
    ValidErr -->|No| BadRequest
    ValidErr -->|Yes| Service
    Service --> BizErr
    BizErr -->|No| DomainErr
    BizErr -->|Yes| Repo
    Repo --> RepoErr
    RepoErr -->|No| InternalErr
    RepoErr -->|Yes| Success

    style BadRequest fill:#FFB6C1
    style InternalErr fill:#FFB6C1
    style DomainErr fill:#FFD700
    style Success fill:#90EE90
```

## Data Model - Users Table

```mermaid
erDiagram
    USERS ||--o{ PASSWORDS : hashes
    USERS {
        string id PK "UUID v4"
        string email UK "Unique, indexed"
        string name
        string password_hash "bcrypt, never exposed"
        timestamp created_at "Auto-set"
        timestamp updated_at "Auto-set, updated on each change"
    }

    JWT_TOKENS {
        string user_id FK "Links to USERS"
        string token "RS256 signed"
        timestamp issued_at
        timestamp expires_at "15 min default"
    }
```

## Request/Response Flow - gRPC Unary

```mermaid
graph LR
    Client["Client"]
    gRPC["gRPC Transport<br/>Protocol Buffers"]
    Interceptor["Interceptor Chain"]
    Handler["Handler"]
    Service["Service"]
    Repo["Repository"]
    DB["Database"]

    Client -->|"1. Register<br/>Request"| gRPC
    gRPC -->|"2. Unmarshal<br/>Protobuf"| Interceptor
    Interceptor -->|"3. Validate<br/>Auth"| Handler
    Handler -->|"4. Parse &<br/>Validate"| Service
    Service -->|"5. Business<br/>Logic"| Repo
    Repo -->|"6. Query<br/>Prepare Statement"| DB
    DB -->|"7. Result"| Repo
    Repo -->|"8. Domain<br/>Entity"| Service
    Service -->|"9. Response<br/>Entity"| Handler
    Handler -->|"10. Protobuf<br/>Message"| gRPC
    gRPC -->|"11. RegisterResponse"| Client
```

## Configuration Hierarchy

```mermaid
graph TB
    Env["Environment Variables"]
    Config["Config Struct<br/>infra/config.go"]
    Logger["Logger Setup<br/>slog"]
    DB["Database Setup<br/>postgres.go"]
    Crypto["Crypto Setup<br/>bcrypt, JWT"]
    Server["gRPC Server<br/>cmd/api/main.go"]

    Env -->|"DB_URL,<br/>JWT_KEY,<br/>PORT"| Config
    Config --> Logger
    Config --> DB
    Config --> Crypto
    Logger --> Server
    DB --> Server
    Crypto --> Server
```