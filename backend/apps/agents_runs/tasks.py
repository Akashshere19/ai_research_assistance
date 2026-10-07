
from celery import shared_task
from django.db import transaction
from apps.agents_runs.models import AgentRun
from apps.agents_runs.serializers import AgentRunUpdateSerializers
from services.agent_run_service import execute_agent_run

@shared_task
def add_numbers(a, b):
    return a + b



@shared_task
def execute_agent_run_task(agent_run_id):
    # agent_run = AgentRun.objects.get(id=agent_run_id)
    agent_run = claim_agent_run(agent_run_id)


    if agent_run is None:
        return {
            "agent_run_id": str(agent_run_id),
            "message": "Task skipped because run is not QUEUED."
        }

    execute_agent_run(agent_run)

    return {
        "agent_run_id": str(agent_run.id),
        "status": agent_run.status,
    }

def claim_agent_run(agent_run_id):
    with transaction.atomic():
            locked_run = AgentRun.objects.select_for_update().get(
                id=agent_run_id
            )

            if locked_run.status != "QUEUED":
                return None

            status_serializer = AgentRunUpdateSerializers(
                locked_run,
                data={"status": "RUNNING"},
                partial=True
            )
            status_serializer.is_valid(raise_exception=True)
            status_serializer.save()

            return locked_run