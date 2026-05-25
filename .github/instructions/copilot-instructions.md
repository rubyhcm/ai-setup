# GitHub Copilot Instructions

This is a consolidated file generated from `.rules/`.

---

# AI Toolchain Rules

This project enforces the strict usage of **RTK (Rust Token Killer)**, **ICM (Interactive Context Management)**, and **GitNexus** across all AI agents, IDEs (Cursor, Kiro), and Assistants (Claude, Copilot). 

> **Important Setup Note:** RTK, ICM, and GitNexus are installed globally on the local host machine. They are available in the system `$PATH`. Do **NOT** attempt to install them, and do not expect them to be listed in project-level dependency files (e.g., `go.mod`, `package.json`). Assume they are always ready to use.

## 1. RTK & ICM (Token Efficiency & Output Management)
Repository: https://github.com/rtk-ai/rtk

**RTK** and **ICM** are required to filter noise, compress standard terminal outputs, and reduce token consumption. 
Whenever an AI agent executes a shell command, it MUST use RTK/ICM to wrap the command.

- **Shell Commands:** Always prefix standard information-gathering commands with `rtk` (unless a transparent shell hook is already active).
  - Use `rtk git status`, `rtk git diff`, `rtk git log` instead of raw git commands.
  - Use `rtk ls`, `rtk find` instead of standard `ls` or `find`.
  - Use `rtk test <command>` (e.g., `rtk test go test ./...`) so that the AI only receives failure traces and ignores passing noise.
  - Use `rtk read <file>` instead of `cat <file>` to view file contents with smart truncation.
- **ICM (Interactive Context Management):** Use `icm` commands when instructed or available to manage chat context, clear redundant history, and focus the context window on relevant code sections.

## 2. GitNexus (Code Intelligence & Impact Analysis)
Repository: https://github.com/abhigyanpatwari/GitNexus

**GitNexus** is our Code Intelligence Engine. It builds a local knowledge graph of the codebase to provide "X-ray vision" into dependencies and execution flows.
All AI agents must leverage GitNexus for repository understanding, refactoring, and impact analysis.

- **MCP Tools:** If your environment supports MCP (Model Context Protocol), use GitNexus MCP tools:
  - `query({query: "..."})` for semantic and graph-based codebase search.
  - `impact({target: "...", direction: "upstream|downstream"})` before modifying any shared interface or critical struct. This analyzes the blast radius of your changes.
  - `context({name: "..."})` to get a 360-degree view of a symbol (callers, callees, functional cluster).
  - `detect_changes()` to map current git diffs to functional processes.
- **CLI Fallback:** If MCP is unavailable, use the equivalent GitNexus CLI commands to perform graph queries and impact analysis *before* making cross-cutting codebase changes.

## 3. Git Operations & Autonomy Constraints
AI Agents MUST NOT autonomously stage or commit changes to version control without explicit, granular user permission.
- **STRICT FORBIDDEN:** Do NOT execute ANY `git add` command (even for a single specific file) unless the user has explicitly told you to "stage this file", "git add this", or "prepare a commit with these changes".
- **STRICT FORBIDDEN:** Do NOT use wildcard staging like `git add .` or `git add -A` under any circumstances.
- **STRICT FORBIDDEN:** Do NOT execute `git commit` unless the user explicitly asks you to "commit the changes".
- **REQUIRED ACTION:** If you have finished a task and the user hasn't mentioned git, simply stop and report that the files are modified in the working directory. Do NOT attempt to stage them "just in case".

## Enforcement Checklist for Agents
1. Did I wrap my test execution or git commands with `rtk`?
2. Did I use GitNexus (`impact` or `context`) to verify the blast radius before refactoring a core domain struct or service interface?
3. Am I optimizing my context window using ICM principles rather than dumping entire files?
4. Did I refrain from running ANY `git add` or `git commit` command? (I must only do this if the user explicitly said to stage/commit).

---

# Architecture Rules

## Clean Architecture Layers

```
Layer            | Responsibility                  | Allowed Imports
-----------------|---------------------------------|------------------
domain/          | Entities, value objects, rules   | standard library only
service/         | Use cases, orchestration         | domain/
repository/      | Data access implementation       | domain/ (for types)
handler/         | HTTP/gRPC entry points           | service/
infra/           | DB, cache, queue connections     | domain/ (for types)
pkg/             | Shared utilities                 | standard library
```

## Dependency Rules

```
                    handler/
                      |
                      v
                   service/  <-- defines interfaces for dependencies
                   /      \
                  v        v
          repository/    infra/
                  \        /
                   v      v
                  domain/
                      |
                      v
                  (nothing)

FORBIDDEN:
  - Circular dependencies between packages
  - domain/ importing any internal package
  - handler/ importing repository/ directly
  - service/ importing infra/ directly
```

## Project Structure Template

```
project-root/
|-- cmd/
|   +-- api/
|       +-- main.go                  # Entry point, DI wiring
|
|-- internal/
|   |-- domain/
|   |   |-- user.go                  # Entity
|   |   |-- errors.go                # Domain errors
|   |   +-- value_objects.go         # Value objects
|   |
|   |-- service/
|   |   |-- user_service.go          # Use case + interface definition
|   |   +-- user_service_test.go     # Unit tests
|   |
|   |-- repository/
|   |   |-- user_postgres.go         # Repository implementation
|   |   +-- user_postgres_test.go    # Integration tests
|   |
|   |-- handler/
|   |   |-- user_handler.go          # HTTP/gRPC handler
|   |   |-- user_handler_test.go     # Handler tests
|   |   |-- middleware/
|   |   |   |-- auth.go              # Auth middleware
|   |   |   |-- logging.go           # Logging middleware
|   |   |   +-- recovery.go          # Panic recovery
|   |   +-- router.go                # Route registration
|   |
|   +-- infra/
|       |-- postgres.go              # DB connection
|       |-- redis.go                 # Cache connection
|       +-- config.go                # App configuration
|
|-- pkg/
|   |-- logger/                      # Structured logger
|   +-- validator/                   # Input validator
|
|-- api/
|   |-- proto/                       # Protobuf definitions
|   +-- openapi/                     # OpenAPI specs
|
|-- configs/
|   |-- config.dev.yaml
|   +-- config.prod.yaml
|
|-- migrations/
|   |-- 001_create_users.up.sql
|   +-- 001_create_users.down.sql
|
|-- tests/
|   +-- integration/                 # Integration tests
|
|-- Makefile
|-- go.mod
|-- go.sum
+-- .golangci.yml
```

## gRPC Workflow (MANDATORY for all gRPC features)

Every new gRPC service or method MUST follow this exact order:

```
Step 1 — PROTO DEFINITION
  File: proto/<module>/<service>.proto
  - Define service, rpc methods, request/response messages
  - Use google.protobuf.Timestamp for time fields
  - Add field validation comments (required, min, max)
  - Follow proto3 syntax, package naming: <project>.<module>.v1

Step 2 — CODE GENERATION
  Run after every proto change:
    buf generate           # preferred (uses buf.gen.yaml)
    OR
    make proto             # if Makefile target exists
    OR
    protoc --go_out=. --go-grpc_out=. proto/<module>/<service>.proto

  Generated files land in: internal/grpc/pb/<module>/

  NEVER edit generated files manually.
  Re-run generation whenever .proto changes.

Step 3 — HANDLER IMPLEMENTATION
  File: internal/grpc/<service>_server.go
  - Embed pb.Unimplemented<Service>Server for forward compatibility
  - Constructor: New<Service>Server(usecase, logger) *<Service>Server
  - Each RPC method: validate input → call usecase → map to proto response
  - Map domain errors to gRPC status codes (see error mapping below)
  - Use component-scoped logger: logger.With(zap.String("component", "<Service>"))

Step 4 — SERVICE REGISTRATION
  File: internal/grpc/server.go (or internal/api/init.go)
  - pb.Register<Service>Server(grpcServer, handler)
  - Register BEFORE server.Serve()
  - Add to DI wiring in internal/api/init.go if needed
```

### gRPC Project Structure

```
proto/
  <module>/
    <service>.proto          ← Step 1: define here

internal/grpc/
  pb/
    <module>/
      <service>.pb.go        ← Step 2: generated, DO NOT edit
      <service>_grpc.pb.go   ← Step 2: generated, DO NOT edit
  <service>_server.go        ← Step 3: implement here
  <service>_server_test.go   ← Step 3: tests
  server.go                  ← Step 4: register here
```

### gRPC Error Mapping

```go
// Domain error → gRPC status code
domain.ErrNotFound         → codes.NotFound
domain.ErrAlreadyExists    → codes.AlreadyExists
domain.ErrPermissionDenied → codes.PermissionDenied
domain.ErrUnauthenticated  → codes.Unauthenticated
domain.ErrInvalidInput     → codes.InvalidArgument
domain.ErrTimeout          → codes.DeadlineExceeded
domain.ErrInternal         → codes.Internal

// Use status.Errorf — never return raw errors from gRPC handlers
return nil, status.Errorf(codes.NotFound, "resource not found")
```

### gRPC Handler Rules

```
REQUIRED: Embed pb.Unimplemented<Service>Server in handler struct
REQUIRED: Validate all input fields before calling usecase
REQUIRED: Map ALL domain errors to appropriate gRPC status codes
REQUIRED: Never leak internal error details in gRPC status messages
REQUIRED: Use context deadline from incoming ctx — do NOT create new timeout
REQUIRED: Log each RPC call with: method, duration, status code, partner/user id
FORBIDDEN: Business logic inside gRPC handler (delegate to usecase)
FORBIDDEN: Direct repository access from handler
FORBIDDEN: Returning raw Go errors — always wrap with status.Errorf
FORBIDDEN: Editing generated pb/*.go files
```

## API Design Rules

```
REQUIRED: gRPC-first — all business APIs use gRPC + protobuf
REQUIRED: HTTP only for health checks (/healthz) and metrics (/metrics)
REQUIRED: Proto versioning: package <project>.<module>.v1
REQUIRED: Pagination for list RPCs (use page_token + page_size pattern)
REQUIRED: Request validation at handler layer before calling usecase
FORBIDDEN: Business logic in handler (delegate to usecase)
FORBIDDEN: Database queries in handler
```

## Dependency Injection

```
REQUIRED: Constructor injection via NewXxx(deps...)
REQUIRED: All wiring in cmd/api/main.go
REQUIRED: Interfaces for all external dependencies

Example:
  // cmd/agent/main.go
  db := postgres.NewConnection(cfg.DB)
  userRepo := repository.NewPostgresUserRepo(db)
  userSvc := service.NewUserService(userRepo, logger)
  userHandler := handler.NewUserHandler(userSvc)

OPTIONAL: wire (Google) or fx (Uber) for complex DI
FORBIDDEN: Global variables for dependencies
FORBIDDEN: init() for dependency setup
```

## Database Rules

```
REQUIRED: Migrations for all schema changes (golang-migrate or goose)
REQUIRED: Transactions for multi-table operations
REQUIRED: Connection pooling configuration
REQUIRED: Prepared statements / parameterized queries
FORBIDDEN: Raw SQL string concatenation
FORBIDDEN: Schema changes without migration files
FORBIDDEN: Database logic in domain/ layer
```

---

# DATABASE DESIGN & MIGRATION RULES

## 0. Global Principles

All schemas MUST follow:

- **Consistency** — naming, structure, constraints
- **Explicitness** — no implicit assumptions
- **Backward compatibility** — support zero-downtime migrations
- **Safety first** — avoid destructive operations
- **Access pattern driven design** — optimize for real queries

## 0.1 Target DBMS Awareness (CRITICAL)

Agent MUST detect or be provided target DBMS.

**PostgreSQL**
- Use `TIMESTAMPTZ`
- Support: Partial Index, CHECK, COMMENT ON, gen_random_uuid()

**MySQL (8+)**
- Use `TIMESTAMP` or `DATETIME`
- NO Partial Index → use composite index workaround
- NO `COMMENT ON` → use inline column/table comments
- Use `UUID()` or application-generated UUID
- CHECK constraints are supported (MySQL 8+)

Agent MUST generate SQL compatible with the target DBMS.

## 1. Table Requirements

### 1.1 Primary Key (REQUIRED)

Every table MUST have a primary key:

Standard (recommended):
```sql
-- PostgreSQL
id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY

-- MySQL
id BIGINT AUTO_INCREMENT PRIMARY KEY
```

Distributed systems (optional):
```sql
id UUID PRIMARY KEY
```

### 1.2 Audit Fields (REQUIRED)

Every table MUST include:

```sql
-- PostgreSQL
created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP

-- MySQL
created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
```

Rules:
- Prefer native auto-update (`ON UPDATE`) if supported.
- Otherwise, use trigger to update `updated_at`.

### 1.3 Soft Delete (OPTIONAL)

```sql
deleted_at TIMESTAMP NULL
```

Rules:
- DO NOT use `is_deleted`.
- All queries MUST include: `deleted_at IS NULL`.

### 1.4 Versioning (OPTIONAL – Optimistic Locking)

```sql
version INT NOT NULL DEFAULT 1
```

Used for concurrency control.

### 1.5 Concurrency Control (ADVANCED)

- Optimistic Locking: use `version`
- Pessimistic Locking: use `SELECT ... FOR UPDATE` in critical transactions

## 2. Column Design Rules

### 2.1 Naming Convention

- MUST use `snake_case`.
- MUST be descriptive.
- Foreign keys MUST follow: `<referenced_table_singular>_id` (e.g., `user_id`, `order_id`).

### 2.2 NULL Handling

- Columns MUST be `NOT NULL` by default.
- Only allow `NULL` if truly optional.

### 2.3 Default Values

- MUST define defaults when meaningful.
- Defaults MUST reflect business logic.

### 2.4 Column Limit

- If table > 20 columns → SHOULD evaluate vertical partitioning.

## 3. Enum / Status Fields

### 3.1 Allowed Strategies

**Option A – Native ENUM** (low-change values)
- Suitable for stable enums.

**Option B – VARCHAR + CHECK**
```sql
status VARCHAR(20) CHECK (status IN ('ACTIVE', 'PENDING', 'CANCELED'))
```

**Option C – Lookup Table (RECOMMENDED for flexibility)**
```sql
status_id INT REFERENCES statuses(id)
```

### 3.2 Rules

- MUST document enum meaning via comments.
- DO NOT use magic numbers without explanation.
- DO NOT auto-index enum fields.

## 4. Indexing Strategy

### 4.1 When to Create Index

Only if used in:
- `WHERE`
- `JOIN`
- `ORDER BY`

### 4.2 Selectivity

Prefer high-selectivity columns.

### 4.3 Composite Index (PREFERRED)

Follow leftmost prefix rule.

### 4.4 Soft Delete Optimization

```sql
-- PostgreSQL (Partial Index)
CREATE INDEX idx_users_active ON users(email)
WHERE deleted_at IS NULL;

-- MySQL workaround (Composite Index)
CREATE INDEX idx_users_email_deleted_at ON users(email, deleted_at);
```

### 4.5 Covering Index (ADVANCED)

Include all selected columns in index to avoid table lookup.

## 5. Constraints

### 5.1 Foreign Keys (REQUIRED)

```sql
FOREIGN KEY (user_id)
REFERENCES users(id)
ON DELETE <RESTRICT | CASCADE | SET NULL>
```

Rules:
- MUST explicitly define `ON DELETE` behavior.
- DO NOT default blindly.

### 5.2 Unique Constraints

MUST enforce business uniqueness.

```sql
-- PostgreSQL (Soft Delete — Partial Unique Index)
CREATE UNIQUE INDEX uk_email_active
ON users(email)
WHERE deleted_at IS NULL;

-- MySQL (Soft Delete workaround)
UNIQUE KEY uk_email_deleted_at (email, deleted_at)
```

## 6. Comment Requirements (MANDATORY)

Agent MUST generate comments:

```sql
-- PostgreSQL
COMMENT ON TABLE users IS 'User information';
COMMENT ON COLUMN users.email IS 'Unique email address';

-- MySQL (inline)
email VARCHAR(255) COMMENT 'Unique email address'
```

## 7. Migration Rules

### 7.1 Versioning

Every migration MUST have version (timestamp or incremental).

### 7.2 Idempotency

Every migration MUST be idempotent — safe to run multiple times without error.

**CREATE TABLE:**
```sql
CREATE TABLE IF NOT EXISTS users (...);
```

**ADD COLUMN:**
```sql
-- PostgreSQL
ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(20) NULL;

-- MySQL (no native IF NOT EXISTS for ADD COLUMN — use stored procedure or migration tool check)
```

**CREATE INDEX:**
```sql
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
```

**DROP TABLE / DROP COLUMN:**
```sql
DROP TABLE IF EXISTS legacy_users;
ALTER TABLE users DROP COLUMN IF EXISTS old_field;  -- PostgreSQL only
```

**CREATE/DROP CONSTRAINT:**
```sql
-- PostgreSQL: check existence before adding
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_orders_user_id'
  ) THEN
    ALTER TABLE orders ADD CONSTRAINT fk_orders_user_id
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT;
  END IF;
END $$;
```

### 7.3 Transaction Safety (CRITICAL)

**Wrap every migration in a transaction** to ensure atomicity:

```sql
-- PostgreSQL (supports transactional DDL)
BEGIN;

ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(20) NULL;
CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone);

COMMIT;
-- On failure: ROLLBACK is automatic
```

**Rules:**
- PostgreSQL: ALL DDL statements (CREATE, ALTER, DROP) are transactional → wrap in `BEGIN/COMMIT`
- MySQL: DDL causes implicit commit → **transactions do NOT protect DDL in MySQL**
  - Use migration tools (Flyway, Liquibase, golang-migrate) to track execution state
  - Keep each MySQL migration file atomic (single logical change)
- NEVER mix DML + DDL in same transaction on MySQL
- On failure: migration MUST leave the database in its original state (for PostgreSQL) or be re-runnable (for MySQL via idempotency)

**PostgreSQL example — full safe migration:**
```sql
BEGIN;

CREATE TABLE IF NOT EXISTS orders (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id     BIGINT NOT NULL,
    status      VARCHAR(20) NOT NULL DEFAULT 'PENDING'
                    CHECK (status IN ('PENDING', 'CONFIRMED', 'CANCELED')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at  TIMESTAMPTZ NULL,
    version     INT NOT NULL DEFAULT 1,
    CONSTRAINT fk_orders_user_id FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE RESTRICT
);

COMMENT ON TABLE orders IS 'Customer orders';
COMMENT ON COLUMN orders.status IS 'Order lifecycle: PENDING, CONFIRMED, CANCELED';

CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_status_active ON orders(status)
WHERE deleted_at IS NULL;

COMMIT;
```

**MySQL example — idempotent migration (no transaction for DDL):**
```sql
-- Each statement must be independently idempotent
CREATE TABLE IF NOT EXISTS orders (
    id         BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id    BIGINT NOT NULL,
    status     VARCHAR(20) NOT NULL DEFAULT 'PENDING'
                   COMMENT 'Order status: PENDING, CONFIRMED, CANCELED',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
) COMMENT = 'Customer orders';

-- Index: check via migration tool, or use CREATE INDEX IF NOT EXISTS (MySQL 8.0.29+)
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
```

### 7.4 Rollback

Every `UP` MUST have `DOWN`.

```sql
-- DOWN migration must reverse UP exactly
-- PostgreSQL
BEGIN;
DROP TABLE IF EXISTS orders;
COMMIT;
```

### 7.5 Safety

DO NOT drop columns/tables or modify data destructively without explicit instruction.

### 7.6 Zero-Downtime Strategy (CRITICAL)

Use **Expand → Migrate → Contract**:
1. Add new column (nullable)
2. Backfill data
3. Switch application
4. Remove old column (later)

- DO NOT rename columns directly or drop columns immediately.

## 7.7 Migration Checklist

Before committing any migration file, verify:
- [ ] Wrapped in `BEGIN/COMMIT` (PostgreSQL)
- [ ] All `CREATE` use `IF NOT EXISTS`
- [ ] All `DROP` use `IF EXISTS`
- [ ] DOWN migration exists and reverses UP exactly
- [ ] No `SELECT *` or unparameterized queries
- [ ] No destructive data change without explicit instruction

## 8. Query Rules

### 8.1 Select Rule

```sql
-- ❌ NOT allowed
SELECT *

-- ✅ REQUIRED
SELECT id, email FROM users
```

### 8.2 Soft Delete Awareness

```sql
WHERE deleted_at IS NULL
```

### 8.3 Pagination (IMPORTANT)

Avoid:
```sql
LIMIT 10 OFFSET 10000
```

Use Keyset Pagination:
```sql
WHERE id > last_id
ORDER BY id
LIMIT 10
```

## 9. Schema Design Strategy

### 9.1 Normalization

- Default: 3NF.
- Denormalize ONLY if required.

### 9.2 Access Pattern Driven

Design based on:
- Query patterns
- Read/write ratio
- Data volume

### 9.3 Partitioning (ADVANCED)

Use for large tables:
- Time-based (e.g., `created_at`)
- Hash-based

## 10. Output Requirements for Agent

When generating schema/migration, Agent MUST:

- Provide executable SQL.
- Include: Primary keys, Audit fields, Constraints, Indexes.
- Include comments (DB-specific).
- Handle soft delete indexing correctly.
- Provide both `UP` and `DOWN` migrations.
- Ensure DBMS compatibility.

## Final Principles

- Prefer clarity over brevity
- Prefer explicit over implicit
- Prefer safe schema over premature optimization
- Design for real-world production systems, not theoretical models

---

# Design Patterns for Go Backend

```
Agent MUST read this file before designing and generating code.
Choose the right pattern for the problem. Do NOT force a pattern when not needed.
Go prefers SIMPLICITY. If a pattern only adds a wrapper without adding value → skip.
```

---

## CREATIONAL PATTERNS

### Factory Method
```
WHEN: Creating objects with many variants (payment processor, notifier, storage)
GO IDIOM: Constructor function NewXxx() returning interface

func NewStorage(storageType string) (Storage, error) {
    switch storageType {
    case "s3":
        return &S3Storage{}, nil
    case "gcs":
        return &GCSStorage{}, nil
    default:
        return nil, fmt.Errorf("unknown storage type: %s", storageType)
    }
}

NOTE: Prefer Functional Options over complex Factory
```

### Functional Options (Go-idiomatic Builder)
```
WHEN: Object with many optional configs (server, client, service)
GO IDIOM: Option functions

type Option func(*Server)

func WithPort(p int) Option {
    return func(s *Server) { s.port = p }
}

func WithTimeout(t time.Duration) Option {
    return func(s *Server) { s.timeout = t }
}

func NewServer(opts ...Option) *Server {
    s := &Server{port: 8080, timeout: 30 * time.Second} // defaults
    for _, opt := range opts {
        opt(s)
    }
    return s
}

// Usage:
srv := NewServer(WithPort(9090), WithTimeout(60*time.Second))
```

### Singleton
```
WHEN: DB connection pool, logger, config (ONLY when truly needed)
GO IDIOM: sync.Once

var (
    instance *DB
    once     sync.Once
)

func GetDB() *DB {
    once.Do(func() {
        instance = &DB{...}
    })
    return instance
}

WARNING: Avoid overuse. Prefer Dependency Injection.
```

---

## STRUCTURAL PATTERNS

### Repository Pattern (DEFAULT for data access)
```
WHEN: Every entity needs data access
GO IDIOM: "Accept interfaces, return structs" (Consumer-side interfaces)

// service/user_service.go (CONSUMER defines interface)
type UserRepository interface {
    FindByID(ctx context.Context, id string) (*domain.User, error)
    Save(ctx context.Context, user *domain.User) error
}

type UserService struct {
    repo UserRepository
}

func NewUserService(repo UserRepository) *UserService {
    return &UserService{repo: repo}
}

// repository/user_postgres.go (PRODUCER returns struct)
type PostgresUserRepo struct {
    db *sql.DB
}

func NewPostgresUserRepo(db *sql.DB) *PostgresUserRepo {
    return &PostgresUserRepo{db: db}
}

func (r *PostgresUserRepo) FindByID(ctx context.Context, id string) (*domain.User, error) {
    // implementation
}

REQUIRED: Interface at CONSUMER (service/), NOT in domain/
REQUIRED: Small interfaces (1-3 methods). If > 5 methods → split
```

### Adapter
```
WHEN: Wrapping external service/library (payment gateway, email provider)
GO IDIOM: Interface + wrapper struct

type EmailSender interface {
    Send(ctx context.Context, to, subject, body string) error
}

type sendgridAdapter struct {
    client *sendgrid.Client
}

func NewSendgridAdapter(apiKey string) *sendgridAdapter {
    return &sendgridAdapter{client: sendgrid.NewClient(apiKey)}
}

func (a *sendgridAdapter) Send(ctx context.Context, to, subject, body string) error {
    // wrap sendgrid-specific logic
}

DEFAULT USE, EXCEPT WHEN:
  - Library already has a good interface (e.g., AWS SDK v2)
  - Only 1 implementation and no need for mocking
  - Wrapper just forwards 1:1 without adding logic
```

### Decorator / Middleware
```
WHEN: Adding behavior without modifying original code (logging, auth, metrics, rate limit)
GO IDIOM: HTTP middleware chain, function wrapping

// HTTP Middleware
func LoggingMiddleware(logger *slog.Logger) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            start := time.Now()
            next.ServeHTTP(w, r)
            logger.Info("request", "method", r.Method, "path", r.URL.Path, "duration", time.Since(start))
        })
    }
}

// Service Decorator
type loggingUserService struct {
    next   UserService
    logger *slog.Logger
}

func WithLogging(svc UserService, logger *slog.Logger) UserService {
    return &loggingUserService{next: svc, logger: logger}
}
```

### Facade
```
WHEN: Aggregating multiple services into one entry point (order = inventory + payment + shipping)
GO IDIOM: Struct aggregating dependencies

type OrderFacade struct {
    inventory InventoryService
    payment   PaymentService
    shipping  ShippingService
}

func (f *OrderFacade) PlaceOrder(ctx context.Context, order Order) error {
    if err := f.inventory.Reserve(ctx, order.Items); err != nil {
        return fmt.Errorf("reserve inventory: %w", err)
    }
    if err := f.payment.Charge(ctx, order.Total); err != nil {
        f.inventory.Release(ctx, order.Items) // compensate
        return fmt.Errorf("charge payment: %w", err)
    }
    if err := f.shipping.Schedule(ctx, order); err != nil {
        // handle compensation...
        return fmt.Errorf("schedule shipping: %w", err)
    }
    return nil
}
```

---

## BEHAVIORAL PATTERNS

### Strategy
```
WHEN: Changing algorithm at runtime (pricing, sorting, compression, notification)
GO IDIOM: Interface + dependency injection

type PricingStrategy interface {
    Calculate(ctx context.Context, order Order) (Money, error)
}

type standardPricing struct{}
type premiumPricing struct{ discount float64 }

type OrderService struct {
    pricing PricingStrategy
}

func NewOrderService(pricing PricingStrategy) *OrderService {
    return &OrderService{pricing: pricing}
}
```

### Observer / Event-Driven
```
WHEN: One action triggers many side effects (user created → send email + create audit log)
GO IDIOM: Channel-based or Event Bus

type EventType string

const (
    UserCreated EventType = "user.created"
    OrderPlaced EventType = "order.placed"
)

type Event struct {
    Type    EventType
    Payload interface{}
}

type EventBus struct {
    handlers map[EventType][]func(context.Context, Event) error
    mu       sync.RWMutex
}

func (eb *EventBus) Subscribe(t EventType, h func(context.Context, Event) error) {
    eb.mu.Lock()
    defer eb.mu.Unlock()
    eb.handlers[t] = append(eb.handlers[t], h)
}

func (eb *EventBus) Publish(ctx context.Context, e Event) error {
    eb.mu.RLock()
    handlers := eb.handlers[e.Type]
    eb.mu.RUnlock()
    for _, h := range handlers {
        if err := h(ctx, e); err != nil {
            return fmt.Errorf("handle %s: %w", e.Type, err)
        }
    }
    return nil
}

NOTE: For microservices, use message broker (NATS, Kafka, RabbitMQ)
```

### Circuit Breaker (DEFAULT for external calls)
```
WHEN: Calling external services (API, payment, third-party)
GO IDIOM: gobreaker library

import "github.com/sony/gobreaker/v2"

cb := gobreaker.NewCircuitBreaker[*http.Response](gobreaker.Settings{
    Name:        "payment-api",
    MaxRequests: 3,
    Interval:    10 * time.Second,
    Timeout:     30 * time.Second,
    ReadyToTrip: func(counts gobreaker.Counts) bool {
        return counts.ConsecutiveFailures > 5
    },
})

resp, err := cb.Execute(func() (*http.Response, error) {
    return httpClient.Do(req)
})

REQUIRED: Every external HTTP/gRPC call MUST have a circuit breaker
```

---

## CONCURRENCY PATTERNS (GO-SPECIFIC)

### Worker Pool
```
WHEN: Processing many tasks concurrently with limits (batch processing, file upload)
GO IDIOM: Buffered channel + goroutines

func WorkerPool(ctx context.Context, numWorkers int, jobs <-chan Job, results chan<- Result) {
    var wg sync.WaitGroup
    for i := 0; i < numWorkers; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for {
                select {
                case job, ok := <-jobs:
                    if !ok { return }
                    results <- process(ctx, job)
                case <-ctx.Done():
                    return
                }
            }
        }()
    }
    wg.Wait()
    close(results)
}

REQUIRED: Context or done channel for cancellation
```

### Fan-Out / Fan-In
```
WHEN: Parallel calls then collecting results (parallel API calls, batch fetch)
GO IDIOM: errgroup.Group

import "golang.org/x/sync/errgroup"

g, ctx := errgroup.WithContext(ctx)
results := make([]*Result, len(items))

for i, item := range items {
    i, item := i, item
    g.Go(func() error {
        res, err := process(ctx, item)
        if err != nil {
            return fmt.Errorf("process item %d: %w", i, err)
        }
        results[i] = res
        return nil
    })
}

if err := g.Wait(); err != nil {
    return fmt.Errorf("fan-out: %w", err)
}
```

### Pipeline
```
WHEN: Data flows through multiple processing steps (ETL, data transformation)
GO IDIOM: Channel chaining

func generate(ctx context.Context, data []int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for _, d := range data {
            select {
            case out <- d:
            case <-ctx.Done():
                return
            }
        }
    }()
    return out
}

func transform(ctx context.Context, in <-chan int) <-chan string {
    out := make(chan string)
    go func() {
        defer close(out)
        for v := range in {
            select {
            case out <- fmt.Sprintf("processed: %d", v):
            case <-ctx.Done():
                return
            }
        }
    }()
    return out
}
```

---

## DEPENDENCY INJECTION (DEFAULT)

### Constructor Injection
```
GO IDIOM: NewXxx(deps...) pattern

func NewUserService(repo UserRepository, logger *zap.Logger, eventBus *EventBus) *UserService {
    return &UserService{
        repo:     repo,
        logger:   logger.With(zap.String("component", "UserService")), // component-scoped logger
        eventBus: eventBus,
    }
}

REQUIRED: Every dependency injected via constructor
REQUIRED: Create a component-scoped child logger in constructor using logger.With().
          This pre-attaches "component" field to ALL log statements from this struct
          without repeating it on every log call.

          // BAD — repeated on every log call:
          s.logger.Info("creating user", zap.String("component", "UserService"), ...)
          s.logger.Error("failed", zap.String("component", "UserService"), ...)

          // GOOD — set once in constructor, auto-appended everywhere:
          s.logger = logger.With(zap.String("component", "UserService"))
          s.logger.Info("creating user", ...)   // → {"component":"UserService","msg":"creating user"}
          s.logger.Error("failed", ...)         // → {"component":"UserService","msg":"failed"}

          Benefit: logs are filterable by component in Kibana/Loki/Datadog:
          component="UserService" AND level="error"

FORBIDDEN: Global variables for dependencies
OPTIONAL: wire (Google) or fx (Uber) for complex DI
```

---

## PATTERN SELECTION GUIDE

```
Situation                               --> Pattern
Creating objects with many variants     --> Factory Method
Complex config with many options        --> Functional Options
Data access for an entity               --> Repository (DEFAULT)
Wrapping external service               --> Adapter (DEFAULT, unless over-engineering)
Adding logging/metrics/auth             --> Decorator / Middleware
Calling external API/service            --> Circuit Breaker (DEFAULT)
Changing algorithm at runtime           --> Strategy
One action triggers many side effects   --> Observer / Event Bus
Batch/parallel processing with limits   --> Worker Pool
Parallel calls collecting results       --> Fan-Out / Fan-In (errgroup)
Data through multiple processing steps  --> Pipeline
Injecting dependencies                  --> Constructor Injection (DEFAULT)
```

---

## ANTI-PATTERNS (FORBIDDEN)

```
FORBIDDEN: God struct (struct > 10 fields or > 7 methods)
FORBIDDEN: Circular dependencies between packages
FORBIDDEN: Global mutable state (use DI instead)
FORBIDDEN: Interface pollution (interface with only 1 impl and no need for mocking)
FORBIDDEN: Premature abstraction (pattern for only 1 use case)
FORBIDDEN: Deep inheritance thinking (Go uses composition)
FORBIDDEN: Empty interface{} when a concrete type can be used
FORBIDDEN: Over-wrapping (adapter around adapter)
```

---

# Go Backend Conventions

## Go Version & Project Layout

```
Go 1.21+

cmd/           -- Entry points (main.go)
internal/      -- Private application code
  domain/      -- Entities, value objects, business rules
  service/     -- Use cases, application logic
  repository/  -- Data access implementations
  handler/     -- HTTP/gRPC handlers
pkg/           -- Public shared libraries
api/           -- Proto files, OpenAPI specs
configs/       -- Configuration files
migrations/    -- Database migrations
```

## Error Handling

```go
// REQUIRED: wrap with context using %w
return fmt.Errorf("get user: %w", err)

// REQUIRED: check specific errors
errors.Is(err, domain.ErrNotFound)
errors.As(err, &myErr)

// REQUIRED: domain errors defined as sentinel vars
var (
    ErrNotFound     = errors.New("not found")
    ErrInvalid      = errors.New("invalid")
    ErrUnauthorized = errors.New("unauthorized")
    ErrAlreadyExists = errors.New("already exists")
)

// FORBIDDEN:
return errors.New("user not found")           // no context
_, err := doSomething(); // ignore error       // silent swallowing
panic("something failed")                     // only allowed in main/init
```

## Context Usage

```go
// REQUIRED: context.Context as FIRST parameter in all service/repository methods
func (s *UserService) GetByID(ctx context.Context, id string) (*domain.User, error)
func (r *PostgresUserRepo) FindByID(ctx context.Context, id string) (*domain.User, error)

// REQUIRED: propagate context through entire call chain
// FORBIDDEN: context.Background() inside service/repository (use passed ctx)
// FORBIDDEN: service method without context.Context as first param
```

## Naming Conventions

```
REQUIRED: CamelCase for exported, camelCase for unexported
REQUIRED: Interface names WITHOUT "I" prefix: Reader not IReader, UserRepository not IUserRepository
REQUIRED: Error variables prefixed with Err: ErrNotFound, ErrInvalid, ErrTimeout
REQUIRED: Package names: lowercase, single word, no underscores
REQUIRED: Receiver names: short (1-2 chars), consistent
          - s for service (s *UserService)
          - r for repository (r *PostgresUserRepo)
          - h for handler (h *UserHandler)
REQUIRED: Acronyms fully capitalized: HTTPHandler, JSONParser, URLPath, gRPCServer
```

## Interfaces (Go Idiom: "Accept interfaces, return structs")

```go
// REQUIRED: Interface defined at CONSUMER (service/ defines repo interface)
// service/user_service.go
type UserRepository interface {
    FindByID(ctx context.Context, id string) (*domain.User, error)
    Save(ctx context.Context, user *domain.User) error
}

// REQUIRED: Producer (repository/) returns concrete struct
// repository/user_postgres.go
type PostgresUserRepo struct { db *sql.DB }
func NewPostgresUserRepo(db *sql.DB) *PostgresUserRepo { ... }

// REQUIRED: Small interfaces (1-3 methods). Split if > 5 methods
// FORBIDDEN: Interface defined in domain/ then imported back (Java-style anti-pattern)
// FORBIDDEN: Interface with only 1 implementation and no need for mocking
```

## Struct & Function Rules

```
REQUIRED: Structs with > 3 required fields use constructor NewXxx()
REQUIRED: Functional Options for > 2 optional configs
REQUIRED: Methods should not exceed 50 lines (extract helpers)
REQUIRED: Max 3 levels of nesting (if/for), use early return pattern
FORBIDDEN: Struct with > 10 fields (split into embedded structs)
FORBIDDEN: Function with > 5 parameters (use options struct)
```

## Logging (Mandatory Component Pattern + Architecture V3)

### Component Logger Pattern

```go
// REQUIRED: Use zap for structured logging
// REQUIRED: Create component-scoped logger ONCE in constructor

func NewUserService(repo UserRepository, logger *zap.Logger) *UserService {
    return &UserService{
        repo:   repo,
        logger: logger.With(zap.String("component", "UserService")), // ONCE here
    }
}

// Then use throughout the struct — component field auto-attached
func (s *UserService) Create(ctx context.Context, ...) error {
    s.logger.Info("creating user", zap.String("email", email))
    // → {"component":"UserService","msg":"creating user","email":"..."}
}

// gRPC servers: PascalCase component name ("AuthServer")
// Use cases/services: snake_case component name ("auth_usecase")

// FORBIDDEN:
logger.Info("msg", zap.String("component", "UserService"), ...) // repeated on every call
s.logger = logger  // storing raw logger without .With() in constructor
fmt.Println("debug")                                            // no structured logging
s.logger.Info("user created", zap.String("password", pw))      // log sensitive data
```

### Log Classification (MANDATORY)

```
Every log statement MUST belong to one category:
  1. ASSERTION_CHECK   — input/security/data-invariant validation failure
  2. RETURN_VALUE_CHECK — err != nil, nil unexpected, external call failure
  3. EXCEPTION         — unhandled/propagated exceptions, DB/network/auth errors
  4. LOGIC_BRANCH      — rare/unexpected branch, fallback, feature flag decision
  5. OBSERVING_POINT   — request/job/transaction start & end
```

### Logging Decision Engine

```
FOR each potential log position:

IF (unexpected OR high-impact OR hard-to-debug)  → MUST LOG
ELSE IF (important state / decision point)       → SHOULD LOG
ELSE                                             → DO NOT LOG
```

### Priority Enforcement

```
Highest priority (add logs here first):
  1. EXCEPTION (catch blocks)
  2. RETURN_VALUE_CHECK (err != nil paths)

Reason: lowest real-world coverage (8–42%), highest debugging value
```

### Rules per Category

```
RETURN_VALUE_CHECK ⚠️:
  MUST:   err != nil, nil unexpected, external call failure, retry triggered
  SHOULD: external API response (optional sampling)
  NEVER:  pure function return, simple getter

EXCEPTION 🚨:
  MUST:   exception not fully handled / propagated, DB/network/auth/payment error
  SHOULD: retryable exception (include retry_count)
  NEVER:  fully handled + no side effect

LOGIC_BRANCH:
  MUST:   rare/unexpected branch, fallback logic, feature flag decision
  SHOULD: business decision (approve/reject)
  NEVER:  trivial if/else

OBSERVING_POINT:
  MUST:   request/job/transaction start & end
  SHOULD: important state (user_id, request_id, latency)
  NEVER:  repetitive debug info

ASSERTION_CHECK:
  MUST:   input validation failure, security failure, data invariant violation
  NEVER:  assertions guaranteed by tests
```

### Decision Matrix

```
Critical + Unhandled   → ERROR (MUST)
Recoverable + Retry    → WARN
Important State        → INFO
High-frequency trivial → NO LOG
```

### Error Handling + Logging Rule

```go
// IF error is returned: MUST LOG OR delegate to upper layer
// IF delegated: DO NOT log here (avoid duplication)

// WRONG — missing log:
if err != nil {
    return fmt.Errorf("get user: %w", err)
}

// CORRECT — log then delegate:
if err != nil {
    s.logger.Error("failed to get user", zap.String("user_id", id), zap.Error(err))
    return fmt.Errorf("get user: %w", err)
}

// CORRECT — delegate intentionally (upper layer will log):
// return fmt.Errorf("get user: %w", err)  // only if caller always logs
```

### Log Format

```json
{
  "level": "ERROR | WARN | INFO",
  "category": "EXCEPTION | RETURN_VALUE_CHECK | ASSERTION_CHECK | LOGIC_BRANCH | OBSERVING_POINT",
  "message": "clear and specific message",
  "context": { "request_id": "...", "trace_id": "...", "user_id": "...", "retry_count": 0 }
}
```

### Anti-Patterns (STRICTLY FORBIDDEN)

```
❌ Blind logging:     log("start function") / log("end function")
❌ Missing error log: if err != nil { return err }  // no log anywhere
❌ Duplicate logs:    same error logged at multiple layers
❌ Sensitive data:    password, token, full PII
```

### Log Density Control

```
High-frequency paths (loops, hot APIs) → use sampling (log only 1/N requests)
```

### Validation Checklist (Before Finishing Code)

```
[ ] All exceptions logged or delegated
[ ] All err != nil paths handled
[ ] No duplicate logs across layers
[ ] No sensitive data leaked
[ ] Log messages are meaningful (not generic)
[ ] High-value areas (exception, return-check) covered
```

## Configuration

```go
// REQUIRED: All configurable values in configs/config.yaml via Viper
// REQUIRED: Config struct with mapstructure tags

type Config struct {
    Server struct {
        Port    int           `mapstructure:"port"`
        Timeout time.Duration `mapstructure:"timeout"`
    } `mapstructure:"server"`
    Auth struct {
        TokenExpiry          time.Duration `mapstructure:"token_expiry"`
        TokenRefreshInterval time.Duration `mapstructure:"token_refresh_interval"`
        BcryptCost           int           `mapstructure:"bcrypt_cost"`
    } `mapstructure:"auth"`
    DB struct {
        MaxOpenConns int           `mapstructure:"max_open_conns"`
        MaxIdleConns int           `mapstructure:"max_idle_conns"`
        ConnTimeout  time.Duration `mapstructure:"conn_timeout"`
    } `mapstructure:"db"`
}

// GOOD: use config
time.Sleep(cfg.Auth.TokenRefreshInterval)

// FORBIDDEN:
time.Sleep(5 * time.Second)          // magic number
const maxRetries = 3                 // hardcoded constant for business logic
"postgres://user:secret@host/db"     // hardcoded connection string
"my-secret-jwt-key"                  // hardcoded secret
```

## Concurrency

```go
// REQUIRED: goroutine must have cancellation mechanism (context or done channel)
// REQUIRED: channel must be closed by SENDER
// REQUIRED: sync.WaitGroup or errgroup for goroutine lifecycle
// REQUIRED: sync.Mutex for shared state, prefer channels for communication

// REQUIRED: recover from panics in goroutines
go func() {
    defer func() {
        if r := recover(); r != nil {
            logger.Error("goroutine panic", zap.Any("error", r))
        }
    }()
    select {
    case <-ctx.Done():
        return
    case job := <-jobs:
        process(job)
    }
}()

// FORBIDDEN: goroutine without context or done channel
go func() { doWork() }() // no cancellation

// FORBIDDEN: unbounded goroutine spawning — use worker pool
// FORBIDDEN: shared state without synchronization
```

## Domain Errors Pattern

```go
// internal/domain/errors.go
var (
    ErrNotFound       = errors.New("not found")
    ErrAlreadyExists  = errors.New("already exists")
    ErrInvalidInput   = errors.New("invalid input")
    ErrUnauthorized   = errors.New("unauthorized")
    ErrForbidden      = errors.New("forbidden")
    ErrTimeout        = errors.New("timeout")
    ErrInternal       = errors.New("internal error")
)

// Wrap with context when propagating
return fmt.Errorf("find user by email %s: %w", email, domain.ErrNotFound)

// Check with errors.Is
if errors.Is(err, domain.ErrNotFound) {
    return nil, status.Errorf(codes.NotFound, "user not found")
}
```

---

# Project Overview & Coding Guidelines

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Go 1.21+ |
| API Protocol | gRPC (primary) + HTTP (health/metrics only) |
| Protocol Buffers | proto3, buf tool for code generation |
| Database | PostgreSQL (primary) or MySQL 8+ |
| ORM/Query | GORM |
| Logging | go.uber.org/zap (structured logging) |
| Configuration | github.com/spf13/viper |
| Testing | testify, gomock, testcontainers-go |
| Linting | golangci-lint |

## Core Principles (Non-Negotiable)

1. **Clean Architecture** — Strict layer separation. Domain knows nothing. Handler knows only service.
2. **gRPC-First** — All business APIs via gRPC + protobuf. HTTP only for `/healthz` and `/metrics`.
3. **No Global State** — Constructor injection everywhere. Zero `var` singletons for business dependencies.
4. **Error Wrapping** — Always `fmt.Errorf("%w", err)`. Never swallow errors silently.
5. **Context Propagation** — Every service/repo method takes `ctx context.Context` as first arg.
6. **Component Logger** — Create scoped logger once in constructor: `logger.With(zap.String("component", "..."))`.
7. **Config via Viper** — No magic numbers, no hardcoded timeouts, no hardcoded secrets.
8. **Table-Driven Tests** — All tests use `t.Run()`. Every case asserts both value and error.
9. **Parameterized Queries** — No SQL string concatenation. Ever.
10. **Zero-Downtime Migrations** — Expand → Migrate → Contract pattern for all schema changes.

## File Naming Conventions

```
domain entity:        internal/domain/user.go
domain errors:        internal/domain/errors.go
service:              internal/service/user_service.go
service test:         internal/service/user_service_test.go
service mock:         internal/service/mock_user_repository_test.go
repository:           internal/repository/user_postgres.go
handler (gRPC):       internal/handler/user_grpc_handler.go
handler (HTTP):       internal/handler/user_http_handler.go
middleware:           internal/handler/middleware/auth.go
infrastructure:       internal/infra/postgres.go
config:               internal/infra/config.go
migrations (up):      migrations/001_create_users.up.sql
migrations (down):    migrations/001_create_users.down.sql
proto:                api/proto/user/v1/user.proto
generated proto:      internal/grpc/pb/user/v1/user.pb.go
```

## How AI Agents Should Approach a Feature Request

When asked to implement a new feature, follow this sequence:

1. **Understand the domain** — What entities are involved? What are the business rules?
2. **Define domain layer** — Create/update entities in `internal/domain/`
3. **Define domain errors** — Add to `internal/domain/errors.go` if new error types needed
4. **Write service interface** — Define repository interface in service file (consumer-side)
5. **Implement service** — Business logic in `internal/service/`
6. **Write service tests** — Table-driven tests with gomock, cover success + all error paths
7. **Implement repository** — Data access in `internal/repository/`, implement service's interface
8. **Create migration** — SQL migration file for any schema changes
9. **Define proto** — Add RPC methods to `.proto` file in `api/proto/`
10. **Generate code** — Run `buf generate`
11. **Implement gRPC handler** — In `internal/handler/`, embed UnimplementedXxxServer
12. **Register handler** — In `cmd/api/main.go` DI wiring
13. **Write handler tests** — Test request validation and error mapping

## Key Patterns to Apply by Default

- **Repository pattern** for every entity that touches the database
- **Adapter pattern** for every external service (email, SMS, payment, storage)
- **Circuit breaker** for every external HTTP/gRPC call
- **Middleware/decorator** for cross-cutting concerns (auth, logging, metrics, rate-limit)
- **Functional options** for structs with optional configuration
- **errgroup** for parallel operations that need error collection

## What NOT To Do

- Do NOT put business logic in gRPC handlers — delegate to service layer
- Do NOT define interfaces in `domain/` and import them back (Java-style anti-pattern)
- Do NOT use `SELECT *` in any query
- Do NOT hardcode timeouts, limits, or configuration values
- Do NOT log sensitive data (passwords, tokens, PII, secrets)
- Do NOT create goroutines without a cancellation mechanism
- Do NOT write tests without assertions (coverage trap)
- Do NOT use `OFFSET` pagination for large tables — use keyset pagination
- Do NOT rename or drop database columns in a single migration — use Expand-Migrate-Contract

---

# Security Rules - Go Backend

## Input Validation (Handler Layer)

```
REQUIRED: Validate ALL user input at handler layer
REQUIRED: Use struct tags for validation (go-playground/validator)
REQUIRED: Whitelist allowed values, not blacklist
REQUIRED: Limit request body size (http.MaxBytesReader)
REQUIRED: Validate Content-Type header
FORBIDDEN: Trust client-side validation alone
FORBIDDEN: Pass unvalidated input to service layer

Example:
  type CreateUserRequest struct {
      Email    string `json:"email" validate:"required,email,max=255"`
      Name     string `json:"name" validate:"required,min=2,max=100"`
      Password string `json:"password" validate:"required,min=8,max=72"`
  }

  // Limit request body
  r.Body = http.MaxBytesReader(w, r.Body, 1<<20) // 1MB
```

## SQL Injection Prevention

```
REQUIRED: Parameterized queries ALWAYS
REQUIRED: Use query builder or ORM methods (GORM .Where(), sqlx.Select)
FORBIDDEN: String concatenation for SQL
FORBIDDEN: GORM .Raw() or .Exec() with fmt.Sprintf

SAFE:
  db.Where("email = ?", email).First(&user)
  db.Raw("SELECT * FROM users WHERE id = ?", id).Scan(&user)

UNSAFE:
  db.Raw("SELECT * FROM users WHERE email = '" + email + "'")
  db.Raw(fmt.Sprintf("SELECT * FROM users WHERE id = %s", id))
```

## Authentication & JWT

```
REQUIRED: Validate JWT algorithm (prevent "none" algorithm attack)
REQUIRED: Set and validate expiration (exp claim)
REQUIRED: Use RS256 or ES256 (asymmetric) for production
REQUIRED: Store secrets in env vars or vault (NEVER hardcode)
REQUIRED: Implement token refresh mechanism
REQUIRED: bcrypt with cost >= 12 for password hashing
FORBIDDEN: HS256 with weak secrets
FORBIDDEN: JWT in URL query parameters
FORBIDDEN: Store sensitive data in JWT payload

Example:
  token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
      if _, ok := token.Method.(*jwt.SigningMethodRSA); !ok {
          return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
      }
      return publicKey, nil
  })
```

## Cryptography

```
REQUIRED: crypto/rand for security-sensitive random values
REQUIRED: bcrypt or argon2 for password hashing
REQUIRED: AES-256-GCM for symmetric encryption
REQUIRED: TLS 1.2+ for all external connections
FORBIDDEN: math/rand for security purposes
FORBIDDEN: MD5 or SHA1 for password hashing
FORBIDDEN: ECB mode for encryption
FORBIDDEN: Hardcoded encryption keys
```

## JSON Handling

```
REQUIRED: Use json.Decoder with size limit
REQUIRED: Decode into typed structs (not map[string]interface{})
REQUIRED: DisallowUnknownFields when strict parsing needed
FORBIDDEN: Unlimited json.Unmarshal on user input

Example:
  decoder := json.NewDecoder(http.MaxBytesReader(w, r.Body, 1<<20))
  decoder.DisallowUnknownFields()
  if err := decoder.Decode(&req); err != nil {
      // handle error
  }
```

## Context & Timeout

```
REQUIRED: Context timeout for ALL external calls (DB, HTTP, gRPC)
REQUIRED: Propagate context through entire call chain
REQUIRED: Default timeout: 30s for HTTP, 5s for DB, 10s for cache
FORBIDDEN: External call without context timeout
FORBIDDEN: context.Background() in service/repository layer

Example:
  ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
  defer cancel()
  err := db.QueryRowContext(ctx, "SELECT ...").Scan(&result)
```

## Goroutine Safety

```
REQUIRED: Goroutine must have cancellation (context or done channel)
REQUIRED: Recover from panics in goroutines
REQUIRED: Use sync.Mutex for shared state
FORBIDDEN: Goroutine without lifecycle management
FORBIDDEN: Unbounded goroutine spawning

Example:
  go func() {
      defer func() {
          if r := recover(); r != nil {
              logger.Error("goroutine panic", "error", r)
          }
      }()
      select {
      case <-ctx.Done():
          return
      case msg := <-ch:
          process(msg)
      }
  }()
```

## CORS

```
REQUIRED: Explicit allowed origins (not "*" in production)
REQUIRED: Explicit allowed methods and headers
REQUIRED: Credentials mode only with specific origins
FORBIDDEN: Access-Control-Allow-Origin: * with credentials
```

## Logging Security

```
REQUIRED: Structured logging with appropriate levels
REQUIRED: Audit log for auth events (login, logout, permission change)
REQUIRED: Log request ID for traceability
FORBIDDEN: Log passwords, tokens, API keys, PII
FORBIDDEN: Log full request/response bodies in production
FORBIDDEN: Expose stack traces to end users
```

## Rate Limiting

```
REQUIRED: Rate limiting on authentication endpoints
REQUIRED: Rate limiting on API endpoints (per user/IP)
REQUIRED: Return gRPC status codes.ResourceExhausted when rate limit exceeded
RECOMMENDED: Use token bucket or sliding window algorithm
RECOMMENDED: Include retry delay in gRPC status details (google.golang.org/grpc/status + errdetails)

Example:
  st := status.New(codes.ResourceExhausted, "rate limit exceeded")
  ds, _ := st.WithDetails(&errdetails.RetryInfo{
      RetryDelay: durationpb.New(retryAfter),
  })
  return nil, ds.Err()
```

## OWASP Top 10 (2025) Quick Reference

```
A01 Broken Access Control    --> RBAC, check permissions per endpoint
A02 Cryptographic Failures   --> TLS, bcrypt, AES-GCM, no hardcoded keys
A03 Injection                --> Parameterized queries, input validation
A04 Insecure Design          --> Threat modeling, secure defaults
A05 Security Misconfiguration--> No debug in prod, minimal permissions
A06 Vulnerable Components    --> govulncheck + Snyk, regular dependency updates
A07 Auth Failures            --> MFA, secure JWT, session management
A08 Data Integrity Failures  --> Signed updates, secure deserialization
A09 Logging Failures         --> Audit logs, monitoring, alerting
A10 SSRF                     --> Validate URLs, block internal networks
```

## Security Scanning Toolchain

```
MANDATORY:
  gosec ./...                           # Go-specific security patterns
  govulncheck ./...                     # Go dependency CVE check

MANDATORY (if installed):
  semgrep --config=p/golang \
          --config=p/owasp-top-ten ./.. # SAST: multi-language rules
  snyk test --all-projects              # Dependency vulnerability scan
  snyk code test                        # SAST: Snyk code analysis
  sonar-scanner                         # SAST: SonarQube security hotspots,
                                        #       bugs, vulnerabilities, code smells
                                        # Config: sonar-project.properties (repo root)
                                        # Requires: SONAR_TOKEN env var (see .env.local)
                                        # Host: https://sonarcloud.io

Coverage gate:
  go test ./... -coverprofile=coverage.out
  go tool cover -func=coverage.out | grep total
  # MUST be >= 80% overall
```

---

# Testing Rules — Go Backend

## Table-Driven Tests (MANDATORY)

All tests MUST use table-driven format with `t.Run()`:

```go
func TestUserService_GetByID(t *testing.T) {
    tests := []struct {
        name    string
        id      string
        setup   func(*MockUserRepository)
        want    *domain.User
        wantErr error
    }{
        {
            name: "success - user found",
            id:   "user-123",
            setup: func(m *MockUserRepository) {
                m.EXPECT().FindByID(gomock.Any(), "user-123").
                    Return(&domain.User{ID: "user-123", Name: "John"}, nil)
            },
            want:    &domain.User{ID: "user-123", Name: "John"},
            wantErr: nil,
        },
        {
            name: "error - user not found",
            id:   "user-999",
            setup: func(m *MockUserRepository) {
                m.EXPECT().FindByID(gomock.Any(), "user-999").
                    Return(nil, domain.ErrNotFound)
            },
            want:    nil,
            wantErr: domain.ErrNotFound,
        },
        {
            name:    "error - empty id",
            id:      "",
            setup:   func(m *MockUserRepository) {},
            want:    nil,
            wantErr: domain.ErrInvalidInput,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            ctrl := gomock.NewController(t)
            defer ctrl.Finish()

            repo := NewMockUserRepository(ctrl)
            tt.setup(repo)

            svc := service.NewUserService(repo, zaptest.NewLogger(t))
            got, err := svc.GetByID(context.Background(), tt.id)

            // REQUIRED: always assert error
            if tt.wantErr != nil {
                require.Error(t, err)
                assert.ErrorIs(t, err, tt.wantErr)
                return
            }
            require.NoError(t, err)

            // REQUIRED: always assert return value
            assert.Equal(t, tt.want.ID, got.ID)
            assert.Equal(t, tt.want.Name, got.Name)
        })
    }
}
```

## Assertion Rules (ANTI COVERAGE TRAP)

```
MANDATORY: Every test case MUST have assertions:
  - assert returned value (NEVER just call function and ignore result)
  - assert error (wantErr → require.Error + assert.ErrorIs, no error → require.NoError)
  - assert state changes (if side effects, verify mock expectations)

FORBIDDEN: Test that only calls a function without any assertion
FORBIDDEN: Empty assertions: assert.True(t, true)
FORBIDDEN: Test that does not check error return
FORBIDDEN: Mock returning a value that is never verified

// NOT ACCEPTED:
func TestBad(t *testing.T) {
    svc := NewService(repo)
    svc.Process(ctx, input) // no assertion = coverage trap
}
```

## Mocking

```go
// REQUIRED: gomock for interface mocking
// REQUIRED: testify/assert + testify/require for assertions

// Add generate directive in the source file:
//go:generate mockgen -source=user_service.go -destination=mock_user_repository_test.go -package=service_test

// Mock setup pattern:
ctrl := gomock.NewController(t)
defer ctrl.Finish()  // verifies all expectations were met

repo := NewMockUserRepository(ctrl)
repo.EXPECT().FindByID(gomock.Any(), "user-123").Return(user, nil).Times(1)
```

## Test File Placement

```
Unit tests:        internal/service/user_service_test.go      (same package: package service_test)
Handler tests:     internal/handler/user_handler_test.go       (same package: package handler_test)
Integration tests: tests/integration/user_test.go              (build tag: //go:build integration)
Test helpers:      internal/testutil/helpers.go                (shared test utilities)
Test fixtures:     testdata/                                   (JSON, SQL, YAML test data)
```

## Test Naming Convention

```
Format: Test<Struct>_<Method>/<scenario>

Examples:
  TestUserService_GetByID/success
  TestUserService_GetByID/not_found
  TestUserService_GetByID/empty_id
  TestUserService_Create/invalid_email
  TestUserHandler_Create/unauthorized
  TestUserHandler_Create/success
```

## Integration Tests (Testcontainers)

```go
//go:build integration

package integration_test

func TestUserRepo_Integration(t *testing.T) {
    ctx := context.Background()

    // Start real postgres container
    pg, err := testcontainers.GenericContainer(ctx, testcontainers.GenericContainerRequest{
        ContainerRequest: testcontainers.ContainerRequest{
            Image:        "postgres:16-alpine",
            ExposedPorts: []string{"5432/tcp"},
            Env: map[string]string{
                "POSTGRES_PASSWORD": "test",
                "POSTGRES_DB":       "testdb",
            },
            WaitingFor: wait.ForListeningPort("5432/tcp"),
        },
        Started: true,
    })
    require.NoError(t, err)
    defer pg.Terminate(ctx)

    // Run tests against real DB
    host, _ := pg.Host(ctx)
    port, _ := pg.MappedPort(ctx, "5432")
    dsn := fmt.Sprintf("postgres://postgres:test@%s:%s/testdb?sslmode=disable", host, port.Port())

    db := mustConnect(t, dsn)
    repo := repository.NewPostgresUserRepo(db)

    // Clean state before each test
    t.Cleanup(func() { db.Exec("TRUNCATE TABLE users RESTART IDENTITY CASCADE") })

    // Test cases...
}

// Run:
// go test -tags=integration ./tests/integration/...
```

## Coverage Policy (Hard Gates)

```
domain/:     90%  — pure business logic, easy to test, no excuses
service/:    85%  — use cases with mocked dependencies
handler/:    80%  — request/response handling
repository/: 70%  — external deps, supplement with integration tests
Critical paths (auth, payment): 95%

Overall project minimum: 80% HARD GATE
  → Review FAILS and code must not be merged if below 80%

IMPORTANT: Coverage % is a guideline, not the goal.
Quality of assertions matters MORE than coverage number.
```

## gRPC Handler Testing

```go
func TestUserServer_Create(t *testing.T) {
    tests := []struct {
        name     string
        req      *pb.CreateUserRequest
        setup    func(*MockUserUsecase)
        wantResp *pb.CreateUserResponse
        wantCode codes.Code
    }{
        {
            name: "success",
            req:  &pb.CreateUserRequest{Email: "test@example.com", Name: "Test"},
            setup: func(m *MockUserUsecase) {
                m.EXPECT().Create(gomock.Any(), gomock.Any()).
                    Return(&domain.User{ID: "1", Email: "test@example.com"}, nil)
            },
            wantCode: codes.OK,
        },
        {
            name: "invalid argument - empty email",
            req:  &pb.CreateUserRequest{Email: "", Name: "Test"},
            setup: func(m *MockUserUsecase) {
                m.EXPECT().Create(gomock.Any(), gomock.Any()).
                    Return(nil, domain.ErrInvalid)
            },
            wantCode: codes.InvalidArgument,
        },
        {
            name: "already exists",
            req:  &pb.CreateUserRequest{Email: "exists@example.com", Name: "Test"},
            setup: func(m *MockUserUsecase) {
                m.EXPECT().Create(gomock.Any(), gomock.Any()).
                    Return(nil, domain.ErrAlreadyExists)
            },
            wantCode: codes.AlreadyExists,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            ctrl := gomock.NewController(t)
            defer ctrl.Finish()

            uc := NewMockUserUsecase(ctrl)
            tt.setup(uc)

            srv := NewUserServer(uc, zap.NewNop())
            resp, err := srv.Create(context.Background(), tt.req)

            if tt.wantCode != codes.OK {
                require.Error(t, err)
                st, ok := status.FromError(err)
                require.True(t, ok)
                assert.Equal(t, tt.wantCode, st.Code())
                return
            }
            require.NoError(t, err)
            assert.NotNil(t, resp)
        })
    }
}
```

## Race Detection

```bash
# REQUIRED: Run with race detector in CI
go test -race ./...

# REQUIRED: Run locally before commit for any concurrent code
go test -race ./internal/...

# ZERO tolerance for race conditions
```

## Running Tests

```bash
# Unit tests
go test ./...

# With coverage
go test ./... -coverprofile=coverage.out
go tool cover -func=coverage.out | grep total

# Race detection
go test -race ./...

# Integration tests only
go test -tags=integration ./tests/integration/...

# Specific test
go test -run TestUserService_GetByID ./internal/service/...

# Verbose output
go test -v -run TestUserService ./internal/service/...
```
