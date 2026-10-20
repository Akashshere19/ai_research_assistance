# Security and API changes

## What changed
- Token authentication is required for API endpoints (DRF TokenAuthentication + IsAuthenticated).
- `POST /api/auth/token/` exchanges a Django username/password for a token.
- Clients can create projects at `POST /api/projects/`; projects are owned by the authenticated user.
- Agent runs can only be created against projects owned by the caller (superusers can administer all projects).
- Agent run result/status/trace/timestamps are read-only in API serialization; public PATCH was removed.
- List/detail/status/project-run endpoints are filtered to projects owned by the authenticated user.
- Django secret, debug, hosts, database and Redis settings are environment-configurable.
- Retry scheduling errors are handled; retryable service exceptions no longer prematurely set `completed_at`.
- Added project owner migration `apps/projects/migrations/0002_project_owner.py`.

## Apply locally
1. Install your existing project dependencies plus `djangorestframework` (already used) and ensure DRF's built-in token app is available.
2. Set `DJANGO_SECRET_KEY` and `GROQ_API_KEY` in your process environment. Copy `.env.example` to `.env`; Django loads `.env` in development. Keep `.env` out of version control.
3. Run `python manage.py migrate`.
4. Create a user: `python manage.py createsuperuser`.
5. Obtain a token:
   `POST /api/auth/token/` with JSON `{"username":"...","password":"..."}`.
6. Send `Authorization: Token <token>` on all API requests.
7. Create a project with `POST /api/projects/` and JSON `{"name":"Research"}`.
8. Create a run with `POST /api/agent-runs/` and JSON `{"project":"<project-uuid>","request":"Research ..."}`.
9. Run the Django web process and Celery worker; start Celery beat if you rely on the recovery schedule.

## Legacy projects
The new owner field is nullable to keep migration safe. Existing projects with `owner=NULL` are not visible to ordinary users. Assign them to the intended user in Django admin or with a deliberate data migration. Superusers can still view them.

## Production notes
- Set `DJANGO_DEBUG=false`, a strong `DJANGO_SECRET_KEY`, and explicit `DJANGO_ALLOWED_HOSTS`.
- Use PostgreSQL for production by setting `DB_ENGINE=postgresql` and the `PG*` variables. Install `psycopg`/`psycopg2` as appropriate for your chosen Django/PostgreSQL setup.
- Serve API over HTTPS. TokenAuthentication tokens are long-lived bearer credentials; protect them and rotate/revoke if exposed.
- The current Project ownership model is user-level. If you require organizations/teams, add organization membership and enforce that policy explicitly.
- This patch was not runtime-tested in this environment because Django and the project dependencies are not installed here. Run the tests and `python manage.py check --deploy` in your actual virtual environment before deployment.
