from .llm_service import generate_response
from services.research_agent_service import run_research_agent
from django.db import transaction
from services.agent_heartbeat import update_agent_heartbeat
from apps.agents_runs.serializers import *
from django.utils import timezone


def execute_agent_run(agent_run):
    update_agent_heartbeat(agent_run.id)

    try:
        
        
        ai_response = run_research_agent(agent_run.request)

        with transaction.atomic():
            locked_run = AgentRun.objects.select_for_update().get(
                id=agent_run.id
            )

            if locked_run.status in ("COMPLETED", "FAILED"):
                return locked_run

            locked_run.result = ai_response["report"]

            agent_trace = list(ai_response.get("agent_trace", []))
            agent_trace = [
                entry for entry in agent_trace
                if not (
                    entry.get("agent") == "workflow"
                    and entry.get("status") == "SUCCESS"
                )
            ]

            agent_trace.append({
                "agent": "workflow",
                "status": "SUCCESS",
                "details": "Research workflow completed successfully",
            })

            locked_run.agent_trace = agent_trace
            locked_run.status = "COMPLETED"
            locked_run.completed_at = timezone.now()
            locked_run.save(
                update_fields=[
                    "result",
                    "agent_trace",
                    "status",
                    "completed_at",
                ]
            )

        return locked_run

    except Exception as exc:
        try:
            agent_run.refresh_from_db()

            if agent_run.status not in ("COMPLETED", "FAILED"):
                agent_trace = agent_run.agent_trace or []
                agent_trace.append({
                    "agent": "workflow",
                    "status": "FAILED",
                    "details": str(exc),
                })

                agent_run.error_msg = str(exc)
                agent_run.agent_trace = agent_trace
                # The Celery task owns retry/failure state transitions. Do not
                # mark completion here: transient failures may be retried.
                agent_run.save(update_fields=["error_msg", "agent_trace"])

        except Exception:
            # Preserve the original exception.
            pass

        raise
    






def mark_agent_run_failed(agent_run, error_message):
    with transaction.atomic():
        locked_run = AgentRun.objects.select_for_update().get(
            id=agent_run.id
        )

        # Never overwrite a terminal state.
        if locked_run.status in ("COMPLETED", "FAILED"):
            return locked_run

        locked_run.error_msg = error_message
        locked_run.status = "FAILED"
        locked_run.completed_at = timezone.now()
        locked_run.save(
            update_fields=[
                "error_msg",
                "status",
                "completed_at",
            ]
        )

        return locked_run



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
            locked_run.started_at = timezone.now()
            locked_run.last_heartbeat_at = timezone.now()
            locked_run.error_msg = ""

            locked_run.save(
                update_fields=["started_at", "last_heartbeat_at", "error_msg"]
            )

            return locked_run





def requeue_agent_run(agent_run, error_message):
    with transaction.atomic():
        locked_run = AgentRun.objects.select_for_update().get(
            id=agent_run.id
        )

        if locked_run.status != "RUNNING":
            return False

        locked_run.error_msg = error_message
        locked_run.status = "QUEUED"
        locked_run.started_at = None
        locked_run.last_heartbeat_at = None

        locked_run.save(
            update_fields=[
                "error_msg",
                "status",
                "started_at",
                "last_heartbeat_at",
            ]
        )

        return True
