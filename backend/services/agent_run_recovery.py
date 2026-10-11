from datetime import timedelta
from django.utils import timezone
from apps.agents_runs.models import AgentRun
from django.db import transaction

def recover_stale_agent_runs():
    timeout_threshold = timezone.now() - timedelta(minutes=10)

    stale_runs = AgentRun.objects.filter(
    status="RUNNING",
     last_heartbeat_at__lt=timeout_threshold,
        ).select_for_update()

    recovered_count = 0

    for agent_run in stale_runs:
        if agent_run.status != "RUNNING":
            continue
        agent_run.status = "FAILED"
        agent_run.error_msg = "Agent execution timed out."
        agent_run.completed_at = timezone.now()

        agent_run.save(
            update_fields=[
                "status",
                "error_msg",
                "completed_at",
            ]
        )

        recovered_count += 1

    return recovered_count