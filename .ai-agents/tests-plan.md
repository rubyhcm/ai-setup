# Test Plan: gRPC User Management System

## Overview

Comprehensive test strategy covering all layers with specific test cases, edge cases, and test data. Target coverage: 80% overall, with higher targets for critical paths.

## Test Structure

```
tests/
├── integration/           (Tagged with //go:build integration)
│   ├── user_repo_test.go
│   ├── auth_flow_test.go
│   └── fixtures.go
├── testdata/
│   └── test_users.json
internal/
├── service/
│   └── user_service_test.go
├── handler/
│   ├── auth_handler_test.go
│   ├── user_handler_test.go
│   └── middleware_test.go
└── domain/
    └── email_test.go (included in user.go)
```

## Domain Layer Tests

### Module: `internal/domain/email.go`

**File**: `internal/domain/email_test.go` (or included in user_test.go)
**Coverage Target**: 90%
**Test Framework**: `testing` package with testify/assert

#### Test Cases

```go
TestNewEmail
├── Case 1: Valid email format
│   Input: "user@example.com"
│   Expected: Email struct created, no error
│   Assertion: email.IsValid() == true
│
├── Case 2: Invalid email - missing @
│   Input: "userexample.com"
│   Expected: Error returned
│   Assertion: error != nil, err.Error() contains "invalid"
│
├── Case 3: Invalid email - empty local part
│   Input: "@example.com"
│   Expected: Error returned
│   Assertion: error != nil
│
├── Case 4: Invalid email - empty domain
│   Input: "user@"
│   Expected: Error returned
│   Assertion: error != nil
│
├── Case 5: Invalid email - domain without TLD
│   Input: "user@localhost"
│   Expected: Error returned (for most validators)
│   Assertion: error != nil
│
├── Case 6: Email exceeds max length (255 chars)
│   Input: 256-char email string
│   Expected: Error returned
│   Assertion: error != nil
│
├── Case 7: Valid email with special chars (allowed)
│   Input: "user+tag@example.co.uk"
│   Expected: Valid
│   Assertion: email.IsValid() == true
│
└── Case 8: Empty string
    Input: ""
    Expected: Error returned
    Assertion: error != nil

TestEmail_String
├── Case 1: Returns email string
│   Input: Email with value "test@example.com"
│   Expected: "test@example.com"
│   Assertion: email.String() == "test@example.com"
└── Case 2: String representation doesn't expose internals
    Input: Email struct
    Expected: Only email value visible
    Assertion: No struct representation

TestEmail_IsValid
├── Case 1: Valid email
│   Input: Email with "valid@example.com"
│   Expected: true
│   Assertion: email.IsValid() == true
│
├── Case 2: Invalid email
│   Input: Email with "invalid"
│   Expected: false
│   Assertion: email.IsValid() == false
│
└── Case 3: After NewEmail, IsValid matches creation result
    Input: Email from NewEmail
    Expected: IsValid() == (creation succeeded)
    Assertion: Consistency check
```

### Module: `internal/domain/user.go`

**Coverage Target**: 90%
**Test Cases**: User creation and validation

```go
TestNewUser / TestUser
├── Case 1: Create user with valid data
│   Input: id="123", email="test@example.com", name="John Doe", hash="$2a$12$..."
│   Expected: User struct created with all fields set
│   Assertion: user.ID == "123", user.Email.String() == "test@example.com"
│
├── Case 2: User ID is required
│   Input: id="", email="test@example.com", name="John Doe"
│   Expected: Error or user with validation error
│   Assertion: user.ID validation fails
│
├── Case 3: Timestamps are set correctly
│   Input: Valid user data
│   Expected: CreatedAt and UpdatedAt are not zero
│   Assertion: user.CreatedAt != zero, user.UpdatedAt != zero
│
├── Case 4: Name constraints
│   Input: name with length < 2
│   Expected: Validation fails or error
│   Assertion: Validation detects short name
│
├── Case 5: Name max length (255 chars)
│   Input: name with 256 chars
│   Expected: Validation fails
│   Assertion: Error returned
│
└── Case 6: PasswordHash is not exposed in JSON
    Input: User marshaled to JSON
    Expected: No "password_hash" field
    Assertion: JSON doesn't contain password
```

### Module: `internal/domain/errors.go`

**Coverage Target**: 90%
**Test Cases**: Domain error definitions

```go
TestDomainErrors
├── Case 1: ErrInvalidEmail is defined
│   Expected: errors.Is check works
│   Assertion: errors.Is(ErrInvalidEmail, ErrInvalidEmail) == true
│
├── Case 2: ErrUserNotFound is defined
│   Expected: Distinct from other errors
│   Assertion: errors.Is(ErrUserNotFound, ErrInvalidEmail) == false
│
├── Case 3: ErrUserExists is defined for duplicate email
│   Expected: Different error for existing user
│   Assertion: errors.Is(ErrUserExists, ErrUserNotFound) == false
│
├── Case 4: ErrInvalidPassword is defined
│   Expected: Password validation errors
│   Assertion: errors.Is works
│
└── Case 5: Error messages are human-readable
    Expected: Errors have descriptive messages
    Assertion: err.Error() contains meaningful text
```

---

## Service Layer Tests

### Module: `internal/service/user_service.go`

**File**: `internal/service/user_service_test.go`
**Coverage Target**: 85%
**Mocking**: gomock for UserRepository
**Tools**: testify/assert, testify/require

#### Test Cases - Registration

```go
TestUserService_Register/success
├── Setup: Mock FindByEmail returns nil (user doesn't exist)
│         Mock Save returns nil (save succeeds)
├── Input: email="new@example.com", name="John Doe", password="SecurePass123"
├── Expected: User created with hashed password
├── Assertions:
│   - Return value is not nil
│   - user.Email.String() == "new@example.com"
│   - user.Name == "John Doe"
│   - user.PasswordHash is not empty and != plaintext password
│   - user.ID is generated (UUID)
│   - Mock.FindByEmail was called once
│   - Mock.Save was called once

TestUserService_Register/duplicate_email
├── Setup: Mock FindByEmail returns existing user (user found)
├── Input: email="existing@example.com", name="Jane Doe", password="Pass123"
├── Expected: Error indicating user already exists
├── Assertions:
│   - error != nil
│   - errors.Is(err, domain.ErrUserExists) == true
│   - Return user is nil
│   - Mock.Save was never called

TestUserService_Register/invalid_email_format
├── Setup: No mock needed (validation before repo call)
├── Input: email="not-an-email", name="John Doe", password="Pass123"
├── Expected: Error on email validation
├── Assertions:
│   - error != nil
│   - errors.Is(err, domain.ErrInvalidEmail) == true
│   - Mock.FindByEmail was never called

TestUserService_Register/weak_password
├── Setup: No mock needed (validation before repo call)
├── Input: email="test@example.com", name="John", password="short" (< 8 chars)
├── Expected: Error on password validation
├── Assertions:
│   - error != nil
│   - errors.Is(err, domain.ErrInvalidPassword) == true
│   - Password is "too short" or similar message

TestUserService_Register/password_exceeds_bcrypt_limit
├── Setup: No mock needed
├── Input: password with 73+ characters (bcrypt max is 72)
├── Expected: Error on validation
├── Assertions:
│   - error != nil
│   - Mock.Save was never called

TestUserService_Register/invalid_name_length
├── Setup: No mock needed
├── Input: name="" (too short) or name with 256+ chars
├── Expected: Validation error
├── Assertions:
│   - error != nil
│   - errors.Is(err, domain.ErrInvalidInput) == true

TestUserService_Register/password_hashing_works
├── Setup: Mock FindByEmail returns nil, Mock Save returns nil
├── Input: email="test@example.com", name="John", password="TestPass123"
├── Expected: Password is hashed with bcrypt
├── Assertions:
│   - PasswordHash != "TestPass123"
│   - PasswordHash starts with "$2a$" or "$2b$" (bcrypt prefix)
│   - bcrypt.CompareHashAndPassword(hash, []byte("TestPass123")) == nil

TestUserService_Register/database_error
├── Setup: Mock FindByEmail returns error (e.g., context timeout)
├── Input: Valid email, name, password
├── Expected: Error propagated with context
├── Assertions:
│   - error != nil
│   - User is nil
```

#### Test Cases - Login

```go
TestUserService_Login/success
├── Setup: Existing user in repo with hashed password
│         Mock FindByEmail returns user
├── Input: email="user@example.com", password="CorrectPassword123"
├── Expected: User returned with valid JWT token
├── Assertions:
│   - error == nil
│   - user != nil
│   - token != ""
│   - Token is valid JWT (can be parsed)
│   - Token exp claim is > now
│   - Token doesn't contain plaintext password

TestUserService_Login/user_not_found
├── Setup: Mock FindByEmail returns nil (user doesn't exist)
├── Input: email="nonexistent@example.com", password="anypass"
├── Expected: Error indicating user not found
├── Assertions:
│   - error != nil
│   - errors.Is(err, domain.ErrUserNotFound) == true
│   - token == ""

TestUserService_Login/wrong_password
├── Setup: Mock FindByEmail returns user with hash of "CorrectPass123"
├── Input: email="user@example.com", password="WrongPassword"
├── Expected: Error on password verification
├── Assertions:
│   - error != nil
│   - errors.Is(err, domain.ErrInvalidPassword) == true
│   - token == ""

TestUserService_Login/invalid_email_format
├── Setup: No repo call needed
├── Input: email="invalid", password="anypass"
├── Expected: Validation error
├── Assertions:
│   - error != nil
│   - Mock.FindByEmail was never called

TestUserService_Login/empty_password
├── Setup: No repo call needed
├── Input: email="user@example.com", password=""
├── Expected: Validation error
├── Assertions:
│   - error != nil

TestUserService_Login/database_error
├── Setup: Mock FindByEmail returns error
├── Input: Valid email, password
├── Expected: Error propagated
├── Assertions:
│   - error != nil
│   - token == ""

TestUserService_Login/token_has_required_claims
├── Setup: Mock FindByEmail returns user
├── Input: Valid credentials
├── Expected: JWT has required claims
├── Assertions:
│   - Token.sub (subject) == user.ID
│   - Token.email == user email
│   - Token.exp is set and > now
│   - Token.iat (issued at) is set
```

#### Test Cases - GetByID

```go
TestUserService_GetByID/success
├── Setup: Mock FindByID returns existing user
├── Input: userID="user-123"
├── Expected: User returned
├── Assertions:
│   - error == nil
│   - user != nil
│   - user.ID == "user-123"
│   - Mock.FindByID called once with "user-123"

TestUserService_GetByID/user_not_found
├── Setup: Mock FindByID returns nil, nil (no user)
├── Input: userID="nonexistent"
├── Expected: Error indicating not found
├── Assertions:
│   - error != nil
│   - errors.Is(err, domain.ErrUserNotFound) == true
│   - user == nil

TestUserService_GetByID/empty_user_id
├── Setup: No repo call
├── Input: userID=""
├── Expected: Validation error
├── Assertions:
│   - error != nil
│   - Mock.FindByID was never called

TestUserService_GetByID/database_error
├── Setup: Mock FindByID returns error
├── Input: userID="user-123"
├── Expected: Error propagated
├── Assertions:
│   - error != nil

TestUserService_GetByID/context_timeout
├── Setup: Mock FindByID checks context
├── Input: context already cancelled
├── Expected: Context error
├── Assertions:
│   - error == context.Canceled or context.DeadlineExceeded
```

---

## Repository Layer Tests

### Module: `internal/repository/user_postgres.go`

**File**: `tests/integration/user_repo_test.go`
**Coverage Target**: 70%
**Build Tag**: `//go:build integration`
**Tools**: testcontainers-go, PostgreSQL
**Database**: Real PostgreSQL container

#### Integration Test Setup

```go
TestUserRepository
├── SetUp: Start PostgreSQL container (testcontainers)
│          Run migrations (001_create_users.up.sql)
│          Create clean database for each test
├── TearDown: Delete test data, stop container
```

#### Test Cases - Save

```go
TestPostgresUserRepository_Save/new_user_success
├── Setup: Clean users table, create connection
├── Input: User{ID: "uuid-1", Email: "test@example.com", Name: "John", Hash: "$2a$..."}
├── Expected: User inserted, no error
├── Assertions:
│   - error == nil
│   - Query COUNT(*) FROM users == 1
│   - Verify email is in database
│   - Verify created_at and updated_at are set

TestPostgresUserRepository_Save/duplicate_email
├── Setup: Insert first user with email "test@example.com"
├── Input: Second user with same email
├── Expected: Database UNIQUE constraint error
├── Assertions:
│   - error != nil
│   - pq error code indicates UNIQUE violation
│   - Query COUNT(*) FROM users == 1 (not 2)

TestPostgresUserRepository_Save/updates_existing_user
├── Setup: Insert user with ID "user-1"
├── Input: User{ID: "user-1", Email: "newemail@example.com", Name: "Jane", ...}
├── Expected: User updated
├── Assertions:
│   - error == nil (UPDATE not INSERT)
│   - Query name FROM users WHERE id='user-1' returns "Jane"
│   - updated_at timestamp is newer

TestPostgresUserRepository_Save/null_values_rejected
├── Setup: Clean table
├── Input: User{Email: "", Name: "test", ...} (empty email)
├── Expected: NOT NULL constraint error
├── Assertions:
│   - error != nil
│   - pq error indicates NOT NULL violation

TestPostgresUserRepository_Save/context_timeout
├── Setup: Create context with short timeout
├── Input: Valid user, context already expired
├── Expected: Context timeout error
├── Assertions:
│   - error == context.DeadlineExceeded
│   - Query COUNT(*) FROM users == 0 (no data inserted)
```

#### Test Cases - FindByID

```go
TestPostgresUserRepository_FindByID/existing_user
├── Setup: Insert user with ID "user-123"
├── Input: id="user-123"
├── Expected: User retrieved
├── Assertions:
│   - error == nil
│   - user != nil
│   - user.ID == "user-123"
│   - user.Email.String() == stored email
│   - user.PasswordHash is populated (not exposed to client)

TestPostgresUserRepository_FindByID/user_not_found
├── Setup: Clean users table
├── Input: id="nonexistent"
├── Expected: No error, nil user (use domain.ErrNotFound if needed)
├── Assertions:
│   - error == nil (or domain.ErrNotFound)
│   - user == nil

TestPostgresUserRepository_FindByID/empty_id
├── Setup: No database call
├── Input: id=""
├── Expected: Validation error or no results
├── Assertions:
│   - error != nil or user == nil

TestPostgresUserRepository_FindByID/context_timeout
├── Setup: Create context with short timeout
├── Input: id="user-123", context expired
├── Expected: Context timeout
├── Assertions:
│   - error == context.DeadlineExceeded

TestPostgresUserRepository_FindByID/multiple_calls_same_user
├── Setup: Insert one user
├── Input: Same id called twice
├── Expected: Same user returned both times
├── Assertions:
│   - Both calls return user.ID == id
│   - Data matches exactly
```

#### Test Cases - FindByEmail

```go
TestPostgresUserRepository_FindByEmail/existing_user
├── Setup: Insert user with email "test@example.com"
├── Input: Email("test@example.com")
├── Expected: User found
├── Assertions:
│   - error == nil
│   - user != nil
│   - user.Email.String() == "test@example.com"

TestPostgresUserRepository_FindByEmail/user_not_found
├── Setup: Empty users table
├── Input: Email("nonexistent@example.com")
├── Expected: No user found
├── Assertions:
│   - error == nil (or domain.ErrNotFound)
│   - user == nil

TestPostgresUserRepository_FindByEmail/case_insensitive
├── Setup: Insert user with email "Test@Example.com"
├── Input: Email("test@example.com") (lowercase)
├── Expected: User found (email should be case-insensitive)
├── Assertions:
│   - user != nil
│   - user.Email matches stored email

TestPostgresUserRepository_FindByEmail/database_error
├── Setup: Close database connection
├── Input: Valid email
├── Expected: Database error
├── Assertions:
│   - error != nil
│   - User is nil
```

---

## Handler Layer Tests

### Module: `internal/handler/auth_handler.go`

**File**: `internal/handler/auth_handler_test.go`
**Coverage Target**: 80%
**Tools**: gomock, testify/assert, httptest (or grpc test)

#### Test Cases - RegisterUser RPC

```go
TestAuthHandler_Register/success
├── Setup: Mock UserService.Register returns new user
├── Input: RegisterRequest{email: "test@example.com", name: "John", password: "Pass123"}
├── Expected: RegisterResponse with user_id, email, name
├── Assertions:
│   - Status == OK (gRPC)
│   - Response.user_id is not empty
│   - Response.email == request email
│   - Response.name == request name

TestAuthHandler_Register/invalid_email_format
├── Setup: No service call (handler validates first)
├── Input: RegisterRequest{email: "not-an-email", name: "John", password: "Pass123"}
├── Expected: InvalidArgument error
├── Assertions:
│   - Status == codes.InvalidArgument
│   - Error message mentions "email"
│   - Service.Register was never called

TestAuthHandler_Register/missing_field
├── Setup: No service call
├── Input: RegisterRequest{email: "", name: "John", password: "Pass123"}
├── Expected: InvalidArgument error
├── Assertions:
│   - Status == codes.InvalidArgument
│   - Error contains "required"

TestAuthHandler_Register/password_too_short
├── Setup: No service call
├── Input: RegisterRequest{email: "test@example.com", name: "John", password: "short"}
├── Expected: InvalidArgument error
├── Assertions:
│   - Status == codes.InvalidArgument
│   - Message mentions "password"

TestAuthHandler_Register/name_too_long
├── Setup: No service call
├── Input: RegisterRequest{email: "test@example.com", name: "256+ char string", password: "Pass123"}
├── Expected: InvalidArgument error
├── Assertions:
│   - Status == codes.InvalidArgument

TestAuthHandler_Register/duplicate_email_error
├── Setup: Mock UserService.Register returns domain.ErrUserExists
├── Input: Valid request for existing email
├── Expected: Already exists error
├── Assertions:
│   - Status == codes.AlreadyExists
│   - Error message is user-friendly

TestAuthHandler_Register/internal_service_error
├── Setup: Mock UserService.Register returns internal error
├── Input: Valid request
├── Expected: Internal error, no details leaked
├── Assertions:
│   - Status == codes.Internal
│   - Error message is generic (no stack trace)

TestAuthHandler_Register/context_timeout
├── Setup: Context already cancelled
├── Input: Valid request
├── Expected: DeadlineExceeded error
├── Assertions:
│   - Status == codes.DeadlineExceeded
```

#### Test Cases - LoginUser RPC

```go
TestAuthHandler_Login/success
├── Setup: Mock UserService.Login returns (user, token, nil)
├── Input: LoginRequest{email: "test@example.com", password: "CorrectPass"}
├── Expected: LoginResponse with user_id, email, token
├── Assertions:
│   - Status == OK
│   - Response.token is not empty
│   - Response.token looks like JWT (3 parts separated by '.')
│   - Response.user_id == mock user id

TestAuthHandler_Login/wrong_password
├── Setup: Mock UserService.Login returns domain.ErrInvalidPassword
├── Input: LoginRequest{email: "test@example.com", password: "WrongPass"}
├── Expected: Unauthenticated error
├── Assertions:
│   - Status == codes.Unauthenticated
│   - Message is generic ("invalid credentials")

TestAuthHandler_Login/user_not_found
├── Setup: Mock UserService.Login returns domain.ErrUserNotFound
├── Input: LoginRequest{email: "nonexistent@example.com", password: "pass"}
├── Expected: Unauthenticated error (don't leak user exists/not)
├── Assertions:
│   - Status == codes.Unauthenticated

TestAuthHandler_Login/invalid_email
├── Setup: No service call
├── Input: LoginRequest{email: "invalid", password: "pass"}
├── Expected: InvalidArgument error
├── Assertions:
│   - Status == codes.InvalidArgument

TestAuthHandler_Login/empty_password
├── Setup: No service call
├── Input: LoginRequest{email: "test@example.com", password: ""}
├── Expected: InvalidArgument error
├── Assertions:
│   - Status == codes.InvalidArgument

TestAuthHandler_Login/malformed_request
├── Setup: No service call
├── Input: Malformed protobuf message
├── Expected: InvalidArgument error
├── Assertions:
│   - Status == codes.InvalidArgument
```

### Module: `internal/handler/user_handler.go`

**File**: `internal/handler/user_handler_test.go`
**Coverage Target**: 80%

#### Test Cases - GetUserInfo RPC

```go
TestUserHandler_GetUserInfo/success
├── Setup: Mock UserService.GetByID returns user
│         Mock is called with user_id from request
├── Input: GetUserInfoRequest{user_id: "user-123"} + valid auth context
├── Expected: GetUserInfoResponse with user data
├── Assertions:
│   - Status == OK
│   - Response.user_id == "user-123"
│   - Response.email is populated
│   - Response.name is populated

TestUserHandler_GetUserInfo/user_not_found
├── Setup: Mock UserService.GetByID returns domain.ErrNotFound
├── Input: GetUserInfoRequest{user_id: "nonexistent"}
├── Expected: NotFound error
├── Assertions:
│   - Status == codes.NotFound
│   - Message is user-friendly

TestUserHandler_GetUserInfo/unauthorized_no_token
├── Setup: Middleware not invoked (no token in context)
├── Input: GetUserInfoRequest without auth context
├── Expected: Unauthenticated error (from middleware)
├── Assertions:
│   - Status == codes.Unauthenticated
│   - Service.GetByID was never called

TestUserHandler_GetUserInfo/invalid_user_id
├── Setup: No service call
├── Input: GetUserInfoRequest{user_id: ""} (empty)
├── Expected: InvalidArgument error
├── Assertions:
│   - Status == codes.InvalidArgument

TestUserHandler_GetUserInfo/service_error
├── Setup: Mock UserService.GetByID returns internal error
├── Input: Valid request
├── Expected: Internal error
├── Assertions:
│   - Status == codes.Internal
│   - No internal error details leaked

TestUserHandler_GetUserInfo/context_cancelled
├── Setup: Context cancelled before handler call
├── Input: Valid request
├── Expected: Cancelled error
├── Assertions:
│   - Status == codes.Cancelled
```

### Module: `internal/handler/middleware/auth.go`

**File**: `internal/handler/middleware_test.go`
**Coverage Target**: 85%

#### Test Cases - ValidateToken / UnaryInterceptor

```go
TestAuthMiddleware_ValidateToken/valid_token
├── Setup: Generate valid JWT with RS256
├── Input: Valid JWT token string
├── Expected: Context updated with user_id
├── Assertions:
│   - error == nil
│   - context.WithValue called to store user_id
│   - user_id can be extracted from context

TestAuthMiddleware_ValidateToken/missing_token
├── Setup: No token provided
├── Input: Empty token string
├── Expected: Unauthenticated error
├── Assertions:
│   - error != nil
│   - errors.Is(err, ErrUnauthenticated) == true

TestAuthMiddleware_ValidateToken/invalid_signature
├── Setup: Create JWT signed with wrong key
├── Input: JWT with invalid signature
├── Expected: Unauthenticated error
├── Assertions:
│   - error != nil
│   - Message mentions "invalid signature"

TestAuthMiddleware_ValidateToken/expired_token
├── Setup: Create JWT with exp claim in past
├── Input: Expired JWT token
├── Expected: Unauthenticated error
├── Assertions:
│   - error != nil
│   - Message mentions "expired"

TestAuthMiddleware_ValidateToken/wrong_algorithm
├── Setup: Create JWT with HS256 instead of RS256
├── Input: HS256 signed token
├── Expected: Unauthenticated error
├── Assertions:
│   - error != nil
│   - Message mentions "algorithm"

TestAuthMiddleware_ValidateToken/malformed_token
├── Setup: Provide invalid JWT format
├── Input: "invalid.token" (only 2 parts instead of 3)
├── Expected: Unauthenticated error
├── Assertions:
│   - error != nil

TestAuthMiddleware_ValidateToken/missing_claims
├── Setup: Create JWT without required claims (sub, exp)
├── Input: JWT without sub (user_id)
├── Expected: Unauthenticated error
├── Assertions:
│   - error != nil
│   - Message mentions "invalid claims"

TestAuthMiddleware_UnaryInterceptor/success
├── Setup: Valid token in metadata
├── Input: gRPC request with "authorization: Bearer <token>"
├── Expected: Request proceeds, context updated
├── Assertions:
│   - handler called
│   - context contains user_id
│   - Response successful

TestAuthMiddleware_UnaryInterceptor/missing_authorization
├── Setup: No authorization metadata
├── Input: gRPC request without auth
├── Expected: Unauthenticated error
├── Assertions:
│   - Status == codes.Unauthenticated
│   - Handler not called

TestAuthMiddleware_UnaryInterceptor/invalid_authorization_format
├── Setup: Authorization header malformed
├── Input: "authorization: InvalidFormat <token>"
├── Expected: Unauthenticated error
├── Assertions:
│   - Status == codes.Unauthenticated
```

---

## Integration Tests

### Module: `tests/integration/auth_flow_test.go`

**Build Tag**: `//go:build integration`
**Coverage Target**: 80% of critical paths
**Database**: Real PostgreSQL via testcontainers

#### End-to-End Test Cases

```go
TestAuthFlow_FullRegistrationLoginFlow
├── Setup: Start PostgreSQL, run migrations
├── Steps:
│   1. Register new user: Register("newuser@example.com", "John Doe", "SecurePass123")
│   2. Login with same credentials: Login("newuser@example.com", "SecurePass123")
│   3. Verify JWT token returned
│   4. Parse JWT and verify claims (user_id, email)
│   5. GetUserInfo with auth token
│   6. Verify user info matches
├── Assertions:
│   - All steps succeed without error
│   - User ID is consistent across calls
│   - JWT contains correct claims
│   - User info retrieval works with JWT

TestAuthFlow_LoginAfterRegistration
├── Setup: Database with one registered user
├── Steps:
│   1. Register user
│   2. Login immediately
│   3. Verify token is valid
├── Assertions:
│   - Login succeeds
│   - Token can be used immediately

TestAuthFlow_ConcurrentRegistrations
├── Setup: Database
├── Input: 10 concurrent register requests with different emails
├── Expected: All succeed, all users created
├── Assertions:
│   - All requests return successfully
│   - Database has 10 users
│   - No race conditions or duplicates

TestAuthFlow_DuplicateEmailPrevention
├── Setup: Register first user
├── Steps:
│   1. Register user1@example.com
│   2. Try to register user1@example.com again
├── Assertions:
│   - First registration succeeds
│   - Second registration fails with duplicate error
│   - Only one user in database

TestAuthFlow_InvalidLoginAfterRegistration
├── Setup: Register user with password "SecurePass123"
├── Steps:
│   1. Register user
│   2. Try to login with wrong password
├── Assertions:
│   - Login fails with unauthenticated error
│   - No token returned

TestAuthFlow_UserInfoBoundaries
├── Setup: Register user with max-length fields
├── Input: email (255 chars), name (255 chars)
├── Steps:
│   1. Register
│   2. Login
│   3. GetUserInfo
├── Assertions:
│   - All operations succeed
│   - Data retrieved correctly

TestAuthFlow_DatabaseRecovery
├── Setup: Database with multiple users
├── Chaos: Kill database connection mid-request
├── Expected: Service reconnects and retries (or returns proper error)
├── Assertions:
│   - Subsequent requests succeed after recovery
```

---

## Test Execution Strategy

### Running Tests

```bash
# Unit tests only (no integration tests)
go test ./internal/... -v

# Unit tests with coverage report
go test ./internal/... -cover -coverprofile=coverage.out

# Integration tests (requires Docker)
go test -tags=integration ./tests/integration/... -v

# All tests with race detector
go test -race ./... -tags=integration -v

# Specific test case
go test -run TestUserService_Register ./internal/service/...

# Coverage for specific package
go test ./internal/domain/... -cover -coverprofile=domain.coverage
```

### Coverage Targets

| Layer | Target | Tool |
|-------|--------|------|
| domain/ | 90% | `go tool cover` |
| service/ | 85% | `go tool cover` |
| handler/ | 80% | `go tool cover` |
| middleware/ | 85% | `go tool cover` |
| repository/ | 70% | `go tool cover` (integration tests) |
| **Overall** | **80%** | `go test -cover ./...` |

### CI/CD Integration

```bash
# Pre-commit
go test -race ./internal/... -count=1

# Pull request
go test -cover ./... && go tool cover -html=coverage.out

# Deployment
go test -tags=integration ./... && go test -race ./...
```

---

## Test Data Fixtures

### File: `testdata/test_users.json`

```json
[
  {
    "id": "fixture-user-1",
    "email": "test1@example.com",
    "name": "Test User 1",
    "password_plaintext": "TestPassword123"
  },
  {
    "id": "fixture-user-2",
    "email": "test2@example.com",
    "name": "Test User 2",
    "password_plaintext": "SecurePass456"
  }
]
```

### File: `internal/testutil/fixtures.go`

```go
// NewTestUser creates a user fixture
func NewTestUser() *domain.User

// NewTestEmail creates a valid email fixture
func NewTestEmail() domain.Email

// ValidBcryptHash returns a known bcrypt hash for testing
func ValidBcryptHash(plaintext string) string

// GenerateValidJWT creates a valid JWT for testing
func GenerateValidJWT(userID string) string

// GenerateExpiredJWT creates an expired JWT
func GenerateExpiredJWT(userID string) string
```

---

## Continuous Testing

### Development Workflow

1. **Before commit**: `go test -race ./internal/...`
2. **Before push**: `go test -cover ./...` (verify coverage maintained)
3. **CI/CD**: All tests + integration tests + coverage report

### Test Maintenance

- Update tests when requirements change
- Run tests with `-race` flag regularly
- Monitor coverage trends
- Review failing tests to understand what broke
