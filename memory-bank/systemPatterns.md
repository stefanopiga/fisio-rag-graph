# System Patterns

## Architecture Overview
Sistema RAG ibrido con autenticazione JWT e **architettura resiliente**, costruito su React + FastAPI + PostgreSQL + Neo4j. Implementa **lazy loading** e **graceful degradation** per operare anche con componenti offline.

## Key Technical Decisions

### Resilient Architecture (NEW)
- **Decision**: Lazy loading per database connections + graceful degradation
- **Rationale**: Sistema deve funzionare anche con servizi esterni non disponibili
- **Alternatives**: Eager initialization, fail-fast approach, monolithic dependencies
- **Trade-offs**: Slightly complex initialization vs high system resilience

### Database Connection Strategy (UPDATED)
- **Decision**: Lazy loading pool creation con fallback multi-database
- **Rationale**: Hosted databases (Neon) hanno limitazioni, sistema deve essere resiliente
- **Implementation**: `get_pool()` creates on first access, reduced pool size (min=1, max=5)
- **Trade-offs**: Deferred initialization complexity vs startup reliability

### Authentication Architecture
- **Decision**: JWT tokens con React Context per stato frontend
- **Rationale**: Separazione frontend/backend, scalabilità, offline capability
- **Alternatives**: Session-based auth, OAuth, cookie-based auth  
- **Trade-offs**: Stateless vs stateful, client vs server storage

### WebSocket Authentication
- **Decision**: JWT token passato come query parameter
- **Rationale**: WebSocket standard non supporta headers custom facilmente
- **Alternatives**: Upgrade headers, sub-protocol authentication
- **Trade-offs**: Security vs compatibility

### WebSocket Stability Patterns (NEW)
- **Active Keep-Alive**:
  - **Where Used**: `websocket_endpoint` in `agent/api.py`.
  - **Why Chosen**: Prevents timeouts from proxies or firewalls during long AI operations by keeping the connection active.
  - **Implementation**: An `asyncio` task sends a "ping" message every 20 seconds.
  - **Benefits**: Ensures stable, long-lived connections for a fluid user experience.

- **Stateful Connection Management**:
  - **Where Used**: Throughout the `websocket_endpoint` before any `send` operation.
  - **Why Chosen**: Prevents `RuntimeError` by ensuring the application never tries to write to a closed or closing connection.
  - **Implementation**: Checks `websocket.client_state == 'CONNECTED'` before sending data.
  - **Benefits**: Eliminates race conditions and makes the WebSocket handler robust against abrupt client disconnects.

- **Environment-Specific Host Configuration**:
  - **Where Used**: `if __name__ == "__main__"` block in `agent/api.py`.
  - **Why Chosen**: Resolves OS-specific instability issues (e.g., using `127.0.0.1` on Windows instead of `0.0.0.0` for development).
  - **Implementation**: A conditional check sets the `run_host` for `uvicorn`.
  - **Benefits**: Guarantees stable WebSocket behavior across different development environments.

## Design Patterns in Use

### Lazy Loading Pattern (NEW)
- **Where Used**: Database pool initialization, external service connections
- **Why Chosen**: Prevents startup failures, improves system resilience
- **Implementation**: `get_pool()` function creates pool on first database access
- **Benefits**: System starts even if external services are down

### Graceful Degradation Pattern (NEW)
- **Where Used**: Database failures, external API unavailability
- **Why Chosen**: System remains operational even with component failures
- **Implementation**: Component status checks, fallback mechanisms, degraded mode
- **Benefits**: High availability, better user experience during outages

### Multi-Database Resilience (NEW)
- **Where Used**: Neo4j for graph data, PostgreSQL for relational data
- **Why Chosen**: Different databases serve different purposes, redundancy
- **Implementation**: Neo4j as primary for some features, PostgreSQL for others
- **Benefits**: System can operate with partial database availability

### React Context Pattern
- **Where Used**: AuthProvider wrapping, useAuth hook consumption
- **Why Chosen**: Centralizza stato autenticazione, evita prop drilling
- **Implementation**: Single context, localStorage persistence

### JWT Token Management
- **Where Used**: Backend generation, frontend storage, WebSocket auth
- **Why Chosen**: Stateless, standard, includes expiration
- **Implementation**: localStorage persistence, automatic API injection

### Diagnostic Testing Pattern (NEW)
- **Where Used**: `investigate_postgres_differences.py` for connection troubleshooting
- **Why Chosen**: Isolate and diagnose connectivity issues separately from app
- **Implementation**: Comprehensive test suite for each database component
- **Benefits**: Clear problem identification, faster debugging

## Component Relationships
```
Frontend: AuthProvider → AppWrapper → LoginPage/App → Components
Backend: api.py → auth_utils → get_pool() → Database/Fallback
Resilience: Health Check → Component Status → Graceful Degradation
WebSocket: Keep-Alive Task → Stateful Send → Stable Connection
```

## Data Flow
1. **Authentication**: Form → POST /auth/login → JWT → localStorage
2. **WebSocket**: Connection → Keep-Alive Task starts → Stateful Send/Receive
3. **Database**: API → get_pool() → lazy initialization → database/fallback
4. **Health Check**: /health → component status → resilience reporting

## Key Abstractions
- **AuthContext**: Centralizza stato autenticazione
- **get_pool()**: Lazy database pool creation con error handling
- **Graceful Degradation**: Sistema operativo anche con componenti offline
- **WebSocket Keep-Alive**: Manages connection stability transparently
- **Styled Theme**: Consistent styling cross-component
- **Health Check**: Component status monitoring e reporting

## Resilience Strategies
- **Lazy Initialization**: Components initialized on-demand
- **Component Independence**: Core functionality works with partial system availability
- **Fallback Mechanisms**: Alternative storage/processing when primary systems unavailable
- **Status Monitoring**: Real-time component health tracking
- **Diagnostic Tools**: Isolated testing for troubleshooting
- **Active Keep-Alive**: Prevents connection timeouts.
- **Stateful Send**: Avoids errors on closed connections.

## Critical Bug Resolution Patterns (NEW - 2025-07-30)

### Production-Critical Fixes Applied
- **Bug Pattern**: Enum vs String Comparison
  - **Where Found**: WebSocket state checking (`WebSocketState.CONNECTED != 'CONNECTED'`)
  - **Impact**: Silent loop exit, zero responses from backend  
  - **Fix**: Import `WebSocketState` enum and use correct comparison
  - **Prevention**: Type safety, enum usage consistency

- **Bug Pattern**: Incomplete Model Definitions  
  - **Where Found**: `AgentDependencies` missing `user_id` field
  - **Impact**: Pydantic validation errors blocking request processing
  - **Fix**: Add optional fields to match usage patterns
  - **Prevention**: Model-usage alignment validation

- **Bug Pattern**: Sync/Async Mismatch
  - **Where Found**: `client.chat.completions.create()` without `await`
  - **Impact**: Event loop blocking, connection drops
  - **Fix**: Proper async/await usage + error handling
  - **Prevention**: Async code review patterns

- **Bug Pattern**: Import Path Errors
  - **Where Found**: `UUID.uuid4()` vs `uuid4()` after `from uuid import UUID`
  - **Impact**: AttributeError crashes during session creation
  - **Fix**: Correct import statements (`from uuid import UUID, uuid4`)
  - **Prevention**: Import verification testing

- **Bug Pattern**: Dependency Bypass Strategy
  - **Where Found**: Heavy dependencies blocking development (sentence_transformers)
  - **Impact**: Server startup failures in development environments
  - **Fix**: Optional imports with graceful fallbacks
  - **Prevention**: Lightweight development configuration

- **Bug Pattern**: Code Formatting in Logging Systems  
  - **Where Found**: Variable declaration on same line as comment (`debug_logger.py`)
  - **Impact**: NameError crashes during WebSocket connection initialization
  - **Fix**: Proper line separation between comments and variable declarations
  - **Prevention**: Code formatting standards, pre-commit hooks for syntax validation

### Additional Critical Patterns (2025-07-30 Latest Session)

- **Bug Pattern**: Exception Handling Flow Control
  - **Where Found**: `continue` statement outside except block in WebSocket message parsing
  - **Impact**: `UnboundLocalError` when trying to access undefined `message` variable after parsing errors
  - **Fix**: Move `continue` statement inside the `except` block with proper indentation
  - **Prevention**: Code flow analysis, exception handling block verification

- **Bug Pattern**: Context Manager Timing Issues
  - **Where Found**: WebSocket confirmation message sent outside request context manager
  - **Impact**: Confirmation messages not sent, test clients blocked waiting for initial response
  - **Fix**: Move confirmation sending inside `debug_logger.websocket_request_context`
  - **Prevention**: Context manager scope validation, initialization sequence verification

- **Bug Pattern**: Type System Enum Usage
  - **Where Found**: Multiple locations comparing `WebSocketState` enum with string literals
  - **Impact**: Logic flow failures due to type mismatches in state checking
  - **Fix**: Consistent enum usage throughout WebSocket state management
  - **Prevention**: Type system enforcement, enum comparison standards

## Development Debugging Patterns (NEW)

### Systematic Debugging Approach
- **WebSocket Message Flow Tracing**: Ultra-detailed logging at each step
- **Connection State Verification**: Real-time state monitoring  
- **Process Management**: Clean termination of interfering processes
- **Environment Isolation**: Separate test environments for debugging

## Advanced Debug Infrastructure (DISCOVERED 2025-07-30)

### Structured Logging System
- **Where Used**: `agent/debug_logger.py` + `analyze_logs.py`
- **Why Chosen**: Production-grade debugging with request tracing and post-mortem analysis
- **Implementation**: 
  ```python
  class StructuredDebugLogger:
      async def websocket_request_context(self, state):
          request_id = self.generate_request_id()
          # Auto-logging per fasi: start -> processing -> completion/error
  ```
- **Benefits**: Complete request lifecycle tracking, automatic error capture, structured analysis

### Log Analysis Framework
- **Where Used**: `analyze_logs.py` for post-incident analysis
- **Why Chosen**: Systematic identification of patterns in failures and performance
- **Implementation**: Phase-by-phase request analysis, error categorization, incomplete request detection
- **Benefits**: Data-driven debugging, trend identification, performance bottleneck detection

### Debugging Test Suite (FULLY OPERATIONAL)
- **Components**:
  - `test_simple_ws.py`: Minimal WebSocket connection testing - ✅ OPERATIONAL
  - `test_websocket_minimal.py`: Complete end-to-end stream testing - ✅ OPERATIONAL  
  - `analyze_logs.py`: Post-mortem trace analysis - ✅ OPERATIONAL
- **Strategy**: Layered testing from basic connectivity to full system integration
- **Benefits**: Rapid issue isolation, comprehensive system validation
- **Current Status**: All test files verified and functional with complete end-to-end coverage

## WebSocket Message Flow Patterns (VERIFIED 2025-07-30)

### Confirmation Message Pattern
- **Where Used**: WebSocket initial connection in `websocket_endpoint`
- **Why Critical**: Client tests expect confirmation message to proceed with chat flow
- **Implementation**: 
  ```python
  async with debug_logger.websocket_request_context(str(websocket.client_state)) as request_id:
      if websocket.client_state == WebSocketState.CONNECTED:
          confirmation = WebSocketResponse(type="connected", data={"message": "Connected"})
          await websocket.send_json(confirmation.model_dump(mode='json'))
  ```
- **Benefits**: Predictable client-server handshake, test reliability

### Request Lifecycle Tracing
- **Where Used**: Every WebSocket request through `debug_logger.websocket_request_context`
- **Why Chosen**: Complete visibility into request processing phases for debugging
- **Implementation**: Automatic phase logging from `websocket_start` → `message_received` → `processing` → `completion`
- **Benefits**: Post-mortem analysis capability, production debugging support

### Error Handling with Request Context
- **Where Used**: Exception handling in WebSocket endpoint with automatic error capture
- **Why Chosen**: Structured error tracking with request correlation for debugging
- **Implementation**: Context manager automatically logs errors with full traceback and request ID
- **Benefits**: Systematic error analysis, debugging efficiency

---
*Technical architecture with resilient design patterns - Updated 2025-07-30 - WEBSOCKET STREAMING FULLY OPERATIONAL*
