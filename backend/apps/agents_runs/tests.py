from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from services.agent_run_service import execute_agent_run
from unittest.mock import patch
from apps.projects.models import Project
from apps.agents_runs.models import AgentRun
from apps.agents_runs.serializers import AgentRunUpdateSerializers
# Create your tests here.



class AgentRunCreateTests(APITestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Robotics Research")
        self.url = "/api/agent-runs/"

    @patch("apps.agents_runs.views.execute_agent_run")
    def test_create_agent_run(self, mock_execute):
        def execute_successfully(agent_run):
            agent_run.status = "COMPLETED"
            agent_run.result = "Mock robotics market research."
            agent_run.save(update_fields=["status", "result"])

        mock_execute.side_effect = execute_successfully

        payload = {
            "project": str(self.project.id),
            "request": "Research the Indian robotics market."
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AgentRun.objects.count(), 1)

        run = AgentRun.objects.get()
        self.assertEqual(run.project, self.project)
        self.assertEqual(run.request, "Research the Indian robotics market.")
        self.assertEqual(run.status, "COMPLETED")
        self.assertEqual(run.result, "Mock robotics market research.")
        self.assertIsNotNone(run.created_at)

    def test_missing_request(self):
        payload = {"project": str(self.project.id)}

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(AgentRun.objects.count(), 0)

    def test_invalid_project(self):
        payload = {
            "project": "00000000-0000-0000-0000-000000000000",
            "request": "Research the Indian robotics market."
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(AgentRun.objects.count(), 0)

    @patch("apps.agents_runs.views.execute_agent_run")
    def test_client_cannot_set_status(self, mock_execute):
        def execute_successfully(agent_run):
            agent_run.status = "COMPLETED"
            agent_run.result = "Mock result."
            agent_run.save(update_fields=["status", "result"])

        mock_execute.side_effect = execute_successfully

        payload = {
            "project": str(self.project.id),
            "request": "Research the Indian robotics market.",
            "status": "COMPLETED"
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        run = AgentRun.objects.get()
        self.assertEqual(run.status, "COMPLETED")
    def test_agent_run_success_lifecycle(self):
                agent_run = AgentRun.objects.create(
                project=self.project,
                request="Research the robotics market.",
                status="QUEUED"
                    )
                with patch(
                    "services.agent_run_service.generate_response",
                    return_value="Mock research result"
                ):
                     execute_agent_run(agent_run)
                agent_run.refresh_from_db()
                self.assertEqual(agent_run.result, "Mock research result")
                self.assertIsNotNone(agent_run.started_at)
                self.assertIsNotNone(agent_run.completed_at)     

    def test_agent_run_failure_lifecycle(self):
            agent_run = AgentRun.objects.create(
                project=self.project,
                request="Research the robotics market.",
                status="QUEUED"
            )

            with patch(
                "services.agent_run_service.generate_response",
                side_effect=Exception("Mock LLM error")
            ):
                execute_agent_run(agent_run)

            agent_run.refresh_from_db()

            self.assertEqual(agent_run.status, "FAILED")
            self.assertIsNotNone(agent_run.started_at)
            self.assertIsNotNone(agent_run.completed_at)
            self.assertTrue(agent_run.error_msg)            

    def test_completed_run_cannot_return_to_running(self):
            # Arrange: create an already completed run
            agent_run = AgentRun.objects.create(
                project=self.project,
                request="Research the robotics market.",
                status="COMPLETED"
            )

            # Act: try to change COMPLETED -> RUNNING
            serializer = AgentRunUpdateSerializers(
                instance=agent_run,
                data={"status": "RUNNING"},
                partial=True
            )

            is_valid = serializer.is_valid()

            # Assert: the transition must be rejected
            self.assertFalse(is_valid)
            self.assertIn("status", serializer.errors)

            # Confirm the database was not changed
            agent_run.refresh_from_db()
            self.assertEqual(agent_run.status, "COMPLETED")        
    def test_update_agent_run_status_to_running(self):
            agent_run = AgentRun.objects.create(
                project=self.project,
                request="Research the robotics market.",
                status="QUEUED"
            )

            url = f"/api/agent-runs/{agent_run.id}/"

            response = self.client.patch(
                url,
                {"status": "RUNNING"},
                format="json"
            )

            self.assertEqual(response.status_code, 200)

            agent_run.refresh_from_db()

            self.assertEqual(agent_run.status, "RUNNING")
            self.assertIsNotNone(agent_run.started_at)        

    def test_update_completed_run_to_running_rejected(self):
            agent_run = AgentRun.objects.create(
                project=self.project,
                request="Research the robotics market.",
                status="COMPLETED"
            )

            url = f"/api/agent-runs/{agent_run.id}/"

            response = self.client.patch(
                url,
                {"status": "RUNNING"},
                format="json"
            )

            self.assertEqual(response.status_code, 400)

            agent_run.refresh_from_db()
            self.assertEqual(agent_run.status, "COMPLETED")        
    def test_update_running_run_to_completed(self):
            agent_run = AgentRun.objects.create(
                project=self.project,
                request="Research the robotics market.",
                status="RUNNING"
            )

            url = f"/api/agent-runs/{agent_run.id}/"

            response = self.client.patch(
                url,
                {"status": "COMPLETED"},
                format="json"
            )

            self.assertEqual(response.status_code, 200)

            agent_run.refresh_from_db()

            self.assertEqual(agent_run.status, "COMPLETED")
            self.assertIsNotNone(agent_run.completed_at)        

    def test_update_running_run_to_failed(self):
            agent_run = AgentRun.objects.create(
                project=self.project,
                request="Research the robotics market.",
                status="RUNNING"
            )

            url = f"/api/agent-runs/{agent_run.id}/"

            response = self.client.patch(
                url,
                {"status": "FAILED"},
                format="json"
            )

            self.assertEqual(response.status_code, 200)

            agent_run.refresh_from_db()

            self.assertEqual(agent_run.status, "FAILED")
            self.assertIsNotNone(agent_run.completed_at)     
    def test_filter_agent_runs_by_status(self):
            AgentRun.objects.create(
                project=self.project,
                request="First request",
                status="QUEUED"
            )
            AgentRun.objects.create(
                project=self.project,
                request="Second request",
                status="RUNNING"
            )
            AgentRun.objects.create(
                project=self.project,
                request="Third request",
                status="COMPLETED"
            )

            response = self.client.get("/api/agent-runs/status/QUEUED/")

            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.data), 1)
            self.assertEqual(response.data[0]["status"], "QUEUED")           

    def test_project_detail_returns_nested_agent_runs(self):
            AgentRun.objects.create(
                project=self.project,
                request="First research request",
                status="QUEUED"
            )

            AgentRun.objects.create(
                project=self.project,
                request="Second research request",
                status="COMPLETED"
            )

            url = f"/api/projects/{self.project.id}/"

            response = self.client.get(url)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(str(response.data["id"]), str(self.project.id))
            self.assertEqual(len(response.data["agent_runs"]), 2)        