from django.utils import timezone
from apps.agents_runs.models import AgentRun


def update_agent_heartbeat(agent_run_id):
    return AgentRun.objects.filter(
        id=agent_run_id,
        status="RUNNING",
    ).update(
        last_heartbeat_at=timezone.now()
    )