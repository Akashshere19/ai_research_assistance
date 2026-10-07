from .llm_service import generate_response
from apps.agents_runs.serializers import *
from django.utils import timezone

def execute_agent_run(agent_run):
        # QUEUED -> RUNNING
        # status_serializer = AgentRunUpdateSerializers(
        #     agent_run,
        #     data={"status": "RUNNING"},
        #     partial=True
        # )
        # status_serializer.is_valid(raise_exception=True)
        # status_serializer.save()

        try:
            ai_response = generate_response(agent_run.request)

        except Exception as e:
            agent_run.error_msg = str(e)
            agent_run.save(update_fields=["error_msg"])

            # RUNNING -> FAILED
            status_serializer = AgentRunUpdateSerializers(
                agent_run,
                data={"status": "FAILED"},
                partial=True
            )
            status_serializer.is_valid(raise_exception=True)
            status_serializer.save()

        else:
            agent_run.result = ai_response
            agent_run.save(update_fields=["result"])

            # RUNNING -> COMPLETED
            status_serializer = AgentRunUpdateSerializers(
                agent_run,
                data={"status": "COMPLETED"},
                partial=True
            )
            status_serializer.is_valid(raise_exception=True)
            status_serializer.save()

        return agent_run


def mark_agent_run_failed(agent_run, error_message):
    agent_run.error_msg = error_message
    agent_run.save(update_fields=["error_msg"])

    status_serializer = AgentRunUpdateSerializers(
        agent_run,
        data={"status": "FAILED"},
        partial=True
    )
    status_serializer.is_valid(raise_exception=True)
    status_serializer.save()

    return agent_run