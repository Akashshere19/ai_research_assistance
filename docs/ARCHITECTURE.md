



# Architecture

## 1. Architecture Goals

We will build ONE serious production-style Agentic AI application from scratch.
The product should reduce this manual research workflow while
keeping the evidence and sources visible to the user.

## 2. System Context
User
 ↓
Django API
 ↓
Agent execution
 ↓
External tools / documents / LLM
 ↓
Research result
 ↓
User

## 3. Django Responsibilities
Django may handle:

- Authentication
- Users
- Organizations
- Projects
- API endpoints
- Permissions
- Database models

## 4. Agent Service Responsibilities
- LangGraph execution
- Agent state
- LLM calls
- Tool execution
- RAG
- Agent workflow orchestration
## 5. Worker Responsibilities

- executes background jobs
- starts/resumes AgentRun execution
- processes documents asynchronously
- generates embeddings asynchronously
- executes long-running tasks
## 6. Database Responsibilities
It stores:
- users and organizations
- projects
- research runs
- run status
- documents metadata
- feedback
- persistent application state

PostgreSQL provides transactional consistency for application data.
## 7. Redis Responsibilities
Redis is used for:

1. Background task broker
2. Short-lived/cache data where useful
3. Pub/Sub for transient run events if required

Redis is not the primary system of record.
PostgreSQL remains responsible for persistent application data.

## 8. Initial Service Boundaries
Initial service boundaries:

1. Django Backend
   Owns API, authentication, authorization,
   application data and AgentRun metadata.

2. Agent Service
   Owns LangGraph execution, LLM calls,
   tools, agent state and AI orchestration.

3. Worker
   Executes long-running/background jobs.

4. PostgreSQL
   Persistent system of record.

5. Redis
   Background task coordination and selected transient data.
## 9. Request Flow
             Client
                ↓
            Django API
                ↓
            Create AgentRun
                ↓
            Queue background task
                ↓
            Agent Service
                ↓
            Single Research Agent
                ↓
            LLM + Tool
                ↓
              Result
                ↓
            Persist AgentRun
                ↓
              Client

## 10. Agent Run Lifecycle
                    ┌─────────────┐
                    │   CREATED   │
                    └──────┬──────┘
                           ↓
                       QUEUED
                           ↓
                       RUNNING
                       /     \
                      /       \
                     ↓         ↓
                COMPLETED    FAILED
## 11. Repository Structure
ai-research-platform/
│
├── backend/
│   ├── manage.py
│   ├── config/
│   └── apps/
│       ├── accounts/
│       ├── organizations/
│       ├── projects/
│       ├── agent_runs/
│       └── documents/
│
├── agent_service/
│   ├── graph/
│   ├── agents/
│   ├── state/
│   ├── tools/
│   └── prompts/
│
├── workers/
│
├── tests/
│
├── docs/
│
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md

## 12. Architecture Decision Records

### ADR-001: Django vs Agent Service
### Context
Django is the core framework of our project. We need to determine the optimal architecture for integrating autonomous agent capabilities (such as LLM orchestration, long-running asynchronous workflows, and vector database interactions) into our existing ecosystem.
### Options

1. Everything inside Django: Implement agents directly within the Django application using Django views, management commands, and Celery tasks.
2. Separate Agent Service: Maintain Django as the core API/web backend and build a standalone service (e.g., using FastAgent, FastAPI, or LangGraph) dedicated exclusively to agent execution.
3. Many independent microservices: Break the entire application down into fine-grained microservices, where each specific agent tool or domain task has its own isolated service.
### Decision
 Separate Agent Service. We will keep Django as our primary backend for user authentication, relational data models, database management, and standard CRUD operations, while offloading all agent-related logic to a dedicated, separate service.

### Reasons
Resource and Scalability Isolation: Agent tasks (like LLM prompting, embedding generation, and vector searches) are highly I/O and CPU bound. Separating them prevents heavy agent workloads from slowing down standard user-facing Django API endpoints.
Avoid Complexity:Django create micro services so it reduce complexity.

### Consequences
Good: Improved application reliability; core user features remain fast even during high agent utilization.Good: Flexibility to use specialized async libraries and Python versions optimized for AI tools.Bad: Increased network overhead and latency due to inter-service communication (REST API or gRPC) between Django and the Agent service.Bad: Data duplication or data sync requirements, as the Agent service will occasionally need access to user context stored in the primary Django database.


### ADR-002: PostgreSQL
PostgreSQL because it serves as the stable, reliable backbone for the core Django application.
Redis is primarily an in-memory data store. While it supports persistence, it is not built to be a primary, durable data store for highly structured relational data.
Our core data (Users, Teams, Permissions, Subscriptions) is deeply relational. MongoDB’s document model leads to data duplication or inefficient application-level joins for this type of data.
We chose pgvector as our initial vector database to minimize architectural complexity and infrastructure costs.
### ADR-003: Redis
it operates entirely in-memory, making it capable of executing sub-millisecond read and write operations
Asynchronous Task Queueing: It allows Django to hand off heavy, long-running agent tasks instantly without blocking the user interface
## 13. Current Architecture
Client
  ↓
Django API
  ↓
PostgreSQL
  ↓
Redis
  ↓
Worker
  ↓
Agent Service
  ↓
Single Agent
  ↓
LLM + Tool
## 14. Future Architecture

    Supervisor
        ↓
     Planner
        ↓
 ┌──────┬──────┬─
Web    RAG    Data
 │      │      │
 └──────┼──────┘
        ↓
      Critic
        ↓
      Writer
        ↓
   Quality Gate