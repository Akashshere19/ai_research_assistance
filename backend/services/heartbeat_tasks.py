from celery import shared_task
from services.agent_heartbeat import update_agent_heartbeat


@shared_task
def update_agent_heartbeat_task(agent_run_id):
    return update_agent_heartbeat(agent_run_id)