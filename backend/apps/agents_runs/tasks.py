import logging
import threading

from celery import shared_task
from celery.exceptions import Retry, SoftTimeLimitExceeded
from groq import APIConnectionError, RateLimitError

from services.agent_heartbeat import update_agent_heartbeat
from services.agent_run_service import (
    claim_agent_run,
    execute_agent_run,
    mark_agent_run_failed,
    requeue_agent_run,
)

logger = logging.getLogger(__name__)


def is_transient_error(exc):
    return isinstance(exc, (APIConnectionError, RateLimitError))


@shared_task(bind=True, max_retries=3, default_retry_delay=10,
             soft_time_limit=120, time_limit=150)
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
                    logger.exception("Heartbeat update failed for AgentRun %s", agent_run.id)

        heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
        heartbeat_thread.start()

        execute_agent_run(agent_run)
        agent_run.refresh_from_db()
        return {"agent_run_id": str(agent_run.id), "status": agent_run.status}

    except SoftTimeLimitExceeded:
        if agent_run is not None:
            agent_run.refresh_from_db()
            if agent_run.status == "RUNNING":
                mark_agent_run_failed(agent_run, "Agent execution exceeded the allowed time.")
        raise

    except Exception as exc:
        if agent_run is None:
            raise

        agent_run.refresh_from_db()
        if agent_run.status in ("COMPLETED", "FAILED"):
            raise

        if is_transient_error(exc) and self.request.retries < self.max_retries:
            if requeue_agent_run(agent_run, str(exc)):
                try:
                    raise self.retry(exc=exc)
                except Retry:
                    raise
                except Exception as retry_error:
                    # Retry publication can fail; do not leave the run QUEUED forever.
                    agent_run.refresh_from_db()
                    if agent_run.status == "QUEUED":
                        mark_agent_run_failed(
                            agent_run,
                            f"Could not schedule retry. Original error: {exc}. "
                            f"Retry scheduling error: {retry_error}",
                        )
                    raise

            agent_run.refresh_from_db()
            if agent_run.status in ("COMPLETED", "FAILED"):
                raise

        mark_agent_run_failed(agent_run, str(exc))
        raise

    finally:
        stop_heartbeat.set()
        if heartbeat_thread is not None:
            heartbeat_thread.join(timeout=2)
