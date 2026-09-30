# Database Design

## 1. Purpose

PostgreSQL is the primary system of record for persistent application data.

The database stores information that must survive:

- application restarts
- worker restarts
- browser disconnections
- agent execution failures

The database is not responsible for temporary agent runtime state.

---

## 2. AgentRun

`AgentRun` represents one execution of an AI research request.

For example:

> "Research the Indian robotics market and identify major competitors."

The request creates one `AgentRun`.

The run can then move through the following lifecycle:

CREATED → QUEUED → RUNNING → COMPLETED

or:

RUNNING → FAILED

---

## 3. AgentRun Fields

| Field | Purpose |
|---|---|
| id | Unique identifier for the research run |
| project | Project that owns the run |
| request | Original user research request |
| status | Current lifecycle state |
| created_at | Time when the run was created |
| started_at | Time when execution started |
| completed_at | Time when execution finished |
| error_message | Failure information when the run fails |

---

## 4. ID Strategy

AgentRun uses UUID as its primary key.

Reason:

- IDs are not sequential
- IDs are harder to guess
- suitable for externally exposed API resources
- avoids exposing database row counts

Example:

`550e8400-e29b-41d4-a716-446655440000`

---

## 5. Status Lifecycle

The initial lifecycle contains five states:

### CREATED

The AgentRun has been created in the database but has not yet been queued.

### QUEUED

The run has been submitted for background execution.

### RUNNING

The worker has started executing the research request.

### COMPLETED

The research execution finished successfully.

### FAILED

The research execution failed.

Lifecycle:

CREATED → QUEUED → RUNNING → COMPLETED
                         │
                         └──→ FAILED

Failure:

RUNNING → FAILED

---

## 6. Relationships

An AgentRun belongs to a Project.

Conceptually:

Project
  |
  └── AgentRun

A Project can contain multiple AgentRuns.

An AgentRun belongs to exactly one Project.

---

## 7. Data Invariants

The following rules should be maintained:

- Every AgentRun must have a request.
- Every AgentRun must have a status.
- New AgentRuns start with `CREATED`.
- `started_at` is NULL until execution begins.
- `completed_at` is NULL until execution finishes.
- `error_message` is NULL unless execution fails.
- UUID is used as the AgentRun identifier.

---

## 8. Persistence Responsibility

PostgreSQL stores durable application state.

The Agent Service is responsible for agent execution and runtime state.

The database does not store temporary LLM execution state.

Future agent execution state may be handled by the Agent Service/LangGraph infrastructure.

---

## 9. Future Extensions

The database model will later be extended with entities such as:

- Conversation
- Message
- AgentStep
- ToolExecution
- Document
- DocumentChunk
- Evaluation
- Feedback

These are intentionally not implemented in the initial version.