from datetime import timedelta
from django.utils import timezone
from apps.agents_runs.models import AgentRun
from django.db.models import Q
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

def recover_stale_agent_runs():
    timeout_threshold = timezone.now() - timedelta(minutes=10)
    recovered_count = 0

    with transaction.atomic():
        stale_runs = AgentRun.objects.filter(
            status="RUNNING"
        ).filter(
            Q(last_heartbeat_at__lt=timeout_threshold)
            | Q(
                last_heartbeat_at__isnull=True,
                started_at__lt=timeout_threshold,
            )
        ).select_for_update()

        for agent_run in stale_runs:
            # Recheck after acquiring the row lock.
            if agent_run.status != "RUNNING":
                continue

            agent_run.status = "FAILED"
            agent_run.error_msg = "Agent execution timed out."
            logger.warning(
                    "Recovered stale AgentRun %s: marked FAILED after heartbeat timeout",
                    agent_run.id,
                )
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
