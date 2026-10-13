from django.test import TestCase
from apps.agents_runs.models import AgentRun
from services.agent_run_service import claim_agent_run
from apps.projects.models import Project

class ClaimAgentRunTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            name="Test Project"
        )
    def test_second_claim_is_rejected(self):
        # Create a run using your existing Project fixture.
        run = AgentRun.objects.create(
            project=self.project,
            request="Test research request",
            status="QUEUED",
        )

        first_claim = claim_agent_run(run.id)
        second_claim = claim_agent_run(run.id)

        self.assertIsNotNone(first_claim)
        self.assertEqual(first_claim.status, "RUNNING")
        self.assertIsNone(second_claim)