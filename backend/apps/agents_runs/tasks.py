import threading
import logging
from services.agent_heartbeat import update_agent_heartbeat
from celery import shared_task
from services.agent_run_service import (
    claim_agent_run,
    execute_agent_run,
    mark_agent_run_failed,
    requeue_agent_run
)
from groq import APIConnectionError, RateLimitError

from celery.exceptions import SoftTimeLimitExceeded
logger = logging.getLogger(__name__)

@shared_task
def add_numbers(a, b):
    return a + b

def is_transient_error(exc):
    return isinstance(
        exc,
        (APIConnectionError, RateLimitError),
    )



@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=10,
    soft_time_limit=120,
    time_limit=150,
)
def execute_agent_run_task(self, agent_run_id):
    agent_run = None
    stop_heartbeat = threading.Event()
    heartbeat_thread = None

    try:
        agent_run = claim_agent_run(agent_run_id)

        if agent_run is None:
            return {
                "agent_run_id": str(agent_run_id),
                "message": "Task skipped because run is not QUEUED.",
            }

        def heartbeat_loop():
            while not stop_heartbeat.wait(30):
                try:
                    update_agent_heartbeat(agent_run.id)
                except Exception:
                    logger.exception(
                        "Heartbeat update failed for AgentRun %s",
                        agent_run.id,
                    )

        heartbeat_thread = threading.Thread(
            target=heartbeat_loop,
            daemon=True,
        )
        heartbeat_thread.start()

        execute_agent_run(agent_run)

        return {
            "agent_run_id": str(agent_run.id),
            "status": agent_run.status,
        }

    except SoftTimeLimitExceeded:
        if agent_run is not None and agent_run.status == "RUNNING":
            mark_agent_run_failed(
                agent_run,
                "Agent execution exceeded the allowed time.",
            )
        raise

    
    except Exception as exc:
        if agent_run is None:
            raise

        # Never retry or overwrite a terminal run.
        agent_run.refresh_from_db()

        if agent_run.status in ("COMPLETED", "FAILED"):
            raise

        # Retry only recognized transient errors.
        if (
            is_transient_error(exc)
            and self.request.retries < self.max_retries
        ):
            requeued = requeue_agent_run(agent_run, str(exc))

            if requeued:
                raise self.retry(exc=exc)

        # Permanent error or retry limit reached.
        mark_agent_run_failed(agent_run, str(exc))
        raise


    finally:
        stop_heartbeat.set()

        if heartbeat_thread is not None:
            heartbeat_thread.join(timeout=2)
