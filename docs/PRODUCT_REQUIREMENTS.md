##                     Product: AI Business Research & Decision Assistant

## 1. Product definition

A B2B SaaS where a user submits a complex research request, such as a company, a market question, or a due-diligence topic. The system plans the work, gathers evidence from the web and the user's uploaded documents, analyzes it, has the results checked, and returns a cited report with recommended next investigations. The user can watch progress live and approve or redirect the run at key points.

What makes it a real agentic problem rather than a chatbot: the workload varies from run to run, the steps depend on what earlier steps find, the work takes minutes, some of it fails, and the output needs a grounding standard (citations).

Non-goals for v1: no fine-tuning, no autonomous actions with side effects (emailing, purchasing), no real-time market data feeds, and no billing integration.

## 2. Target user
  Business/market analyst working for a company.


## 3. User Problem  
   Analysts need to gather information from multiple web sources and
private documents, compare evidence, identify unsupported claims,
and prepare research reports.

This process is currently time-consuming and requires manually
switching between search engines, documents, spreadsheets and
analysis tools.

The product should reduce this manual research workflow while
keeping the evidence and sources visible to the user.

## 4. User stories
As an analyst, I submit "research Company X, its competitors and risks" and get a structured report with citations.
As an analyst, I watch progress in real time (plan, sources found, sections drafted).
As an analyst, I approve or edit the research plan before expensive work starts.
As an analyst, I upload private documents (PDFs, decks) and have them used alongside web research.
As an analyst, I click any claim and see its source.
As an org admin, I invite members and keep our data isolated from other organizations.
As an org admin, I see usage and cost per run.
As a user, I give feedback (thumbs and comments) on a report.
As an engineer (you), I can replay a failed run and see every LLM call, tool call, and cost.

## 5. Functional requirements


The application must eventually support:

User authentication
Organization/project management
Research request creation
Agent execution
Tool calling
Web research
Document ingestion
RAG
Structured agent state
Multi-agent orchestration
Conversation/context management
Streaming execution events
Background jobs
Human approval
Report generation
Source citations
Evaluation
Feedback
Run history
Failure/retry handling

## 6. Non-functional requirements


Durability: a worker crash must not lose a run.
Tenant isolation: no cross-organization data leakage, including in vector search.
Cost bounds: per-run token and step budgets, with hard stops.
Loop safety: a maximum on steps, retries, and wall-clock time.
Observability: every run traceable end to end.
Latency: first event within seconds, since full reports take minutes.
Testability: the test suite runs without real LLM calls.
Security: treat all fetched web content and uploaded documents as untrusted input (prompt injection).  



The system should eventually satisfy:

Area	Requirement
Reliability	: Retries, timeouts, failure recovery
Scalability :	Multiple concurrent research runs
Security	: Authentication, authorization, tenant isolation
Performance	: Async execution and parallel work where useful
Observability: 	Logs, traces, latency, tokens, cost
Maintainability	: Clear service boundaries
Testability	: Unit → integration → E2E
AI reliability : 	Structured outputs, validation, evaluation
Cost : 	Token/model tracking
Persistence	: Durable research runs
UX	: Streaming progress
Deployment	: Dockerized production architecture


## 7. Primary Use Case
Primary use case:

A business analyst wants to research a product or company.

The user submits a research question.
The system creates a research plan.
The user reviews the plan.
The system gathers information from approved web sources
and uploaded documents.
The system verifies important claims.
The system produces a cited research report.


## 8. Example User Request

The user posts a request, and Django creates an AgentRun and enqueues it.
A worker starts the graph, and the Planner drafts a plan.
The run pauses (interrupt) for user approval, and the state is checkpointed.
On approval, the graph resumes, and independent steps run in parallel across the specialist agents.
Every LLM call, tool call, and transition is recorded as an event, and events stream to the UI.
The Critic checks the claims, and unsupported claims loop back for repair, up to a fixed cap.
The Writer produces the cited report, and the run is finalized with cost and latency totals.



POST /api/agent/runs/
          │
          ▼
      Create Run
          │
          ▼
    Start background job
          │
          ▼
     LangGraph
          │
          ▼
       Planner
          │
          ▼
      Research Plan
          │
     ┌────┼─────┐
     ▼    ▼     ▼
   Web   RAG   Data
     │    │     │
     └────┼─────┘
          ▼
       Evidence
          │
          ▼
       Critic
          │
          ▼
    Validated Evidence
          │
          ▼
     Report Agent
          │
          ▼
      Quality Gate
          │
          ▼
      Final Report
          │
          ▼
       Persist Run
          │
          ▼
     Stream Result

## 9. Proposed Agent Architecture

                    ┌─────────────────────┐
                    │ Supervisor /        │
                    │ Orchestrator        │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │ Planner Agent       │
                    └──────────┬──────────┘
                               │
             ┌─────────────────┼─────────────────┐
             │                 │                 │
             ▼                 ▼                 ▼
      Research Agent     Document/RAG       Data Analysis
                              Agent             Agent
             │                 │                 │
             └─────────────────┼─────────────────┘
                               │
                               ▼
                     Critic / Verification
                            Agent
                               │
                               ▼
                       Report Generation
                             Agent


	Agent	             Why it might deserve to be an agent
1	Supervisor	          Routes work among specialists and decides when to stop.
2	Planner      	      Turns a vague request into a structured, reviewable plan.
3	Web Research	      A tool-using loop: search, read, decide whether to search again.
4	Document/RAG	      Retrieves from the user's uploads and decides how to query.
5	Data Analysis	      Works with numbers and tables extracted from sources.
6	Critic / Fact-Checker	Independent verification. It should be separate so it isn't grading its own work.
7	Report Writer	            Synthesizes findings into a structured, cited report.
8	Next-Steps Recommender	    Proposes what to investigate next.




## 9.1 Expected System Behavior


                         Internet
                            │
                            ▼
                  ┌───────────────────┐
                  │ Nginx / LB        │
                  └─────────┬─────────┘
                            │
                            ▼
                  ┌───────────────────┐
                  │ Django + DRF      │
                  │ API               │
                  └─────────┬─────────┘
                            │
             ┌──────────────┼──────────────┐
             │              │              │
             ▼              ▼              ▼
        PostgreSQL        Redis        WebSocket
             │              │              │
             │              ▼              │
             │       ┌──────────────┐      │
             │       │ Worker       │      │
             │       │ Celery/etc.  │      │
             │       └──────┬───────┘      │
             │              │              │
             └──────────────┼──────────────┘
                            ▼
                  ┌───────────────────┐
                  │ Agent Service     │
                  │ LangGraph         │
                  └─────────┬─────────┘
                            │
                ┌───────────┼───────────┐
                ▼           ▼           ▼
             Tools         RAG       LLM Provider
                │           │
                │           ▼
                │      Vector Search
                │
                ▼
         External Services


## 10. Success Criteria
- User can create a research run.
- API immediately returns a run ID.
- Research execution happens asynchronously.
- User can approve the generated plan.
- Research sources are persisted.
- Important report claims have source references.
- Failed runs can be resumed.
- User can view run status.
- Run records contain latency and token/cost information.


## 11. Constraints

- Python backend
- Django/DRF
- PostgreSQL
- Initial LLM provider
- Initial deployment environment
- No autonomous side-effect actions
- Research must remain human-reviewable
## 12. Future Scope

- additional data providers
- real-time market feeds
- billing
- autonomous actions
- additional model providers
- dedicated vector database if scale requires it