from celery import shared_task
from services.agent_run_recovery import recover_stale_agent_runs


@shared_task
def recover_stale_agent_runs_task():
    return recover_stale_agent_runs()