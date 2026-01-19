# DAALAB Complete Architecture Flow

## Service Architecture (After Refactoring)

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER BROWSER                             │
│                    (Access: localhost:8010)                      │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│               API SERVER (Frontend Gateway)                      │
│                      Port: 8010                                  │
│                                                                   │
│  Responsibilities:                                               │
│  • Serve static HTML/CSS/JS files                               │
│  • Handle authentication (login/signup)                          │
│  • Manage code file storage (Supabase)                          │
│  • Forward execution requests to Load Balancer                   │
│  • Direct AI analysis (complexity analyzer)                      │
│                                                                   │
│  Key Change: NO LONGER runs containers directly!                │
│              Forwards to scheduler-worker system                 │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      LOAD BALANCER                               │
│                      Port: 8080                                  │
│                                                                   │
│  Responsibilities:                                               │
│  • Round-robin load distribution                                │
│  • Health monitoring of schedulers                               │
│  • Automatic failover                                            │
│  • Simple traffic routing (no job awareness)                     │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         SCHEDULER                                │
│                      Port: 8000                                  │
│                                                                   │
│  Responsibilities:                                               │
│  • Receive job requests                                          │
│  • Analyze code complexity (via AI service)                      │
│  • Estimate execution costs                                      │
│  • Select optimal worker (queue_cost algorithm)                  │
│  • Track job status                                              │
│                                                                   │
│  Algorithms: queue_cost, round_robin, load_balance               │
└─────────────────────┬───────────────────┬───────────────────────┘
                      │                   │
         ┌────────────┘                   └────────────┐
         ▼                                             ▼
┌─────────────────────┐                    ┌─────────────────────┐
│    WORKER 1         │                    │    WORKER 2         │
│    Port: 8001       │                    │    Port: 8002       │
│                     │                    │                     │
│  • Execute Python   │                    │  • Execute Python   │
│  • Execute C++      │                    │  • Execute C++      │
│  • Run in Docker    │                    │  • Run in Docker    │
│  • Track queue      │                    │  • Track queue      │
│  • Monitor resources│                    │  • Monitor resources│
└─────────────────────┘                    └─────────────────────┘
```

## Request Flow Example

### Python Code Execution

```
1. User submits code via browser (http://localhost:8010)
   ↓
2. API Server authenticates user and saves code to Supabase
   ↓
3. API Server forwards to Load Balancer:
   POST http://localhost:8080/api/run-code
   {
     "code": "print('Hello')",
     "language": "python",
     "user_id": "abc123"
   }
   ↓
4. Load Balancer forwards to Scheduler:
   POST http://localhost:8000/api/run-code
   ↓
5. Scheduler:
   a) Analyzes code complexity (via AI service)
   b) Estimates execution cost
   c) Selects optimal worker (e.g., Worker 1 has shorter queue)
   ↓
6. Scheduler dispatches to Worker 1:
   POST http://localhost:8001/execute
   ↓
7. Worker 1 runs code in Docker container:
   docker run python:3.13-slim python code.py
   ↓
8. Worker returns result to Scheduler
   ↓
9. Scheduler returns to Load Balancer
   ↓
10. Load Balancer returns to API Server
   ↓
11. API Server saves runtime to Supabase and returns to user
```

## Service Ports Summary

| Service              | Port | Purpose                                    |
|---------------------|------|--------------------------------------------|
| API Server          | 8010 | Frontend gateway + UI + Auth + DB          |
| Load Balancer       | 8080 | Traffic distribution + failover            |
| Scheduler           | 8000 | Job orchestration + complexity analysis    |
| Worker 1            | 8001 | Code execution in Docker containers        |
| Worker 2            | 8002 | Code execution in Docker containers        |

## Frontend API Changes

### Before (Direct Execution)
```javascript
// OLD: Direct to scheduler or worker
fetch('http://localhost:8000/api/code/python', {...})
fetch('http://localhost:8001/ask', {...})
```

### After (Via Load Balancer)
```javascript
// NEW: Through load balancer for better distribution
fetch('http://localhost:8080/api/code/python', {...})
fetch('http://localhost:8080/ask', {...})
```

## Key Benefits of This Architecture

1. **Separation of Concerns**
   - API Server: Frontend, auth, database
   - Load Balancer: Traffic distribution
   - Scheduler: Job orchestration
   - Workers: Execution only

2. **Scalability**
   - Add more workers: Update WORKER_URLS
   - Add more schedulers: Update SCHEDULER_URLS
   - Frontend scales independently

3. **Fault Tolerance**
   - Load balancer provides failover
   - Workers can be restarted independently
   - Job queue prevents loss

4. **Complexity-Aware Scheduling**
   - AI analyzes code complexity
   - Cost-based worker selection
   - Optimal resource utilization

5. **No Direct Container Execution in API Server**
   - Retired ContainerRunner/CppContainerRunner from api_server.py
   - All execution delegated to worker nodes
   - Better resource management

## Starting All Services

```powershell
.\start_all.ps1
```

This starts:
1. Worker 1 (8001)
2. Worker 2 (8002)
3. Scheduler (8000)
4. Load Balancer (8080)
5. API Server (8010)

Access the frontend at: **http://localhost:8010**
