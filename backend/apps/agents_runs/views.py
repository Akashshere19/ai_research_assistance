import logging

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token

from apps.projects.models import Project
from .models import AgentRun
from .serializers import (
    AgentRunCreateSerializer,
    AgentRunDetailsSerializer,
    ProjectRunDetailsSerializer,
    ProjectSerializer,
)
from .tasks import execute_agent_run_task
from services.agent_run_service import mark_agent_run_failed

logger = logging.getLogger(__name__)


def owned_projects(user):
    return Project.objects.all() if user.is_superuser else Project.objects.filter(owner=user)


def owned_runs(user):
    return AgentRun.objects.select_related("project").filter(
        project__in=owned_projects(user)
    )


class AgentRunView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AgentRunCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        # Commit the row before publishing the task so a fast worker can find it.
        with transaction.atomic():
            agent_run = serializer.save(status="QUEUED")

        try:
            task_result = execute_agent_run_task.delay(str(agent_run.id))
            logger.info("Queued AgentRun %s as Celery task %s", agent_run.id, task_result.id)
        except Exception:
            logger.exception("Failed to enqueue AgentRun %s", agent_run.id)
            mark_agent_run_failed(agent_run, "Unable to queue the background task.")
            agent_run.refresh_from_db()
            return Response(
                AgentRunDetailsSerializer(agent_run).data,
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        agent_run.refresh_from_db()
        response_serializer = AgentRunDetailsSerializer(agent_run)
        return Response(response_serializer.data, status=status.HTTP_202_ACCEPTED)

    def get(self, request, uuid=None):
        if uuid is not None:
            agent_run = get_object_or_404(owned_runs(request.user), id=uuid)
            return Response(AgentRunDetailsSerializer(agent_run).data, status=status.HTTP_200_OK)

        runs = owned_runs(request.user).order_by("-created_at")
        serializer = AgentRunDetailsSerializer(runs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProjectRunView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id=None):
        if project_id is not None:
            project = get_object_or_404(owned_projects(request.user), id=project_id)
            return Response(ProjectRunDetailsSerializer(project).data, status=status.HTTP_200_OK)
        projects = owned_projects(request.user).order_by("-created_at")
        return Response(ProjectSerializer(projects, many=True).data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ProjectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        project = serializer.save(owner=request.user)
        return Response(ProjectSerializer(project).data, status=status.HTTP_201_CREATED)


class AgentRunStatuswiseViews(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, status_code):
        valid_statuses = {choice[0] for choice in AgentRun.STATUS}
        if status_code not in valid_statuses:
            return Response({"status": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)
        runs = owned_runs(request.user).filter(status=status_code).order_by("-created_at")
        return Response(AgentRunDetailsSerializer(runs, many=True).data, status=status.HTTP_200_OK)


class ApiTokenView(ObtainAuthToken):
    """POST username/password to receive a DRF token."""
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        token = Token.objects.get(key=response.data["token"])
        return Response({"token": token.key}, status=status.HTTP_200_OK)
