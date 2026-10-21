from unittest.mock import patch

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.agents_runs.models import AgentRun
from apps.projects.models import Project
from apps.conversations.models import Conversation

User = get_user_model()


class AgentRunApiSecurityTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="akash", password="test-pass-12345")
        self.other_user = User.objects.create_user(username="other", password="test-pass-12345")
        self.project = Project.objects.create(name="Research project", owner=self.user)
        self.other_project = Project.objects.create(name="Private project", owner=self.other_user)
        self.url = "/api/agent-runs/"
        self.client.force_authenticate(user=self.user)

    def test_anonymous_client_cannot_list_runs(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("apps.agents_runs.views.execute_agent_run_task.delay")
    def test_create_run_returns_202_and_queues_task(self, mock_delay):
        mock_delay.return_value.id = "celery-test-id"
        response = self.client.post(
            self.url,
            {"project": str(self.project.id), "request": "Research AI systems."},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        run = AgentRun.objects.get()
        self.assertEqual(run.project, self.project)
        self.assertEqual(run.status, "QUEUED")
        mock_delay.assert_called_once_with(str(run.id))

    @patch("apps.agents_runs.views.execute_agent_run_task.delay", side_effect=RuntimeError("broker down"))
    def test_enqueue_failure_marks_run_failed(self, mock_delay):
        response = self.client.post(
            self.url,
            {"project": str(self.project.id), "request": "Research AI systems."},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        run = AgentRun.objects.get()
        self.assertEqual(run.status, "FAILED")
        self.assertTrue(run.error_msg)
        self.assertIsNotNone(run.completed_at)

    def test_client_cannot_set_server_managed_fields(self):
        response = self.client.post(
            self.url,
            {
                "project": str(self.project.id),
                "request": "Research AI systems.",
                "status": "COMPLETED",
                "result": "Forged result",
                "agent_trace": [{"agent": "forged"}],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        run = AgentRun.objects.get()
        self.assertEqual(run.status, "QUEUED")
        self.assertIsNone(run.result)
        self.assertEqual(run.agent_trace, [])

    def test_cannot_create_run_for_another_users_project(self):
        response = self.client.post(
            self.url,
            {"project": str(self.other_project.id), "request": "Private research."},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(AgentRun.objects.count(), 0)

    def test_cannot_read_another_users_run(self):
        run = AgentRun.objects.create(project=self.other_project, request="Private run")
        response = self.client.get(f"{self.url}{run.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_status_patch_is_not_exposed(self):
        run = AgentRun.objects.create(project=self.project, request="Research", status="QUEUED")
        response = self.client.patch(
            f"{self.url}{run.id}/", {"status": "COMPLETED"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        run.refresh_from_db()
        self.assertEqual(run.status, "QUEUED")

    def test_status_filter_only_returns_owned_runs(self):
        own_run = AgentRun.objects.create(project=self.project, request="Own", status="QUEUED")
        AgentRun.objects.create(project=self.other_project, request="Other", status="QUEUED")
        response = self.client.get("/api/agent-runs/status/QUEUED/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in response.data], [str(own_run.id)])

    def test_create_project_assigns_current_user_as_owner(self):
        response = self.client.post("/api/projects/", {"name": "New project"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        project = Project.objects.get(id=response.data["id"])
        self.assertEqual(project.owner, self.user)
        
    @patch("apps.agents_runs.views.execute_agent_run_task.delay")
    def test_create_run_with_own_conversation(self, mock_delay):
        mock_delay.return_value.id = "celery-test-id"

        conversation = Conversation.objects.create(
            user=self.user,
            title="Robotics Research",
        )

        response = self.client.post(
            self.url,
            {
                "project": str(self.project.id),
                "request": "Research autonomous navigation.",
                "conversation": str(conversation.id),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        run = AgentRun.objects.get()
        self.assertEqual(run.conversation, conversation)
        mock_delay.assert_called_once_with(str(run.id)) 
    
    def test_cannot_create_run_with_another_users_conversation(self):
            other_conversation = Conversation.objects.create(
                user=self.other_user,
                title="Private Research",
            )

            response = self.client.post(
                self.url,
                {
                    "project": str(self.project.id),
                    "request": "Research autonomous navigation.",
                    "conversation": str(other_conversation.id),
                },
                format="json",
            )

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(AgentRun.objects.count(), 0)    
           


class ApiTokenTests(APITestCase):
    def test_token_endpoint_returns_token_for_valid_credentials(self):
        User.objects.create_user(username="token-user", password="test-pass-12345")
        response = self.client.post(
            "/api/auth/token/",
            {"username": "token-user", "password": "test-pass-12345"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
