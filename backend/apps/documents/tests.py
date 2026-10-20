from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.projects.models import Project
from apps.documents.models import Document
from apps.agents_runs.models import AgentRun
from services.agent_run_service import execute_agent_run
from apps.documents.retrieval_service import retrieve_relevant_chunks
from apps.documents.models import Document, DocumentChunk


User = get_user_model()


class ResearchDocumentAccessTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="research_owner",
            password="test-pass-12345",
        )
        self.other_user = User.objects.create_user(
            username="other_user",
            password="test-pass-12345",
        )

        self.project = Project.objects.create(
            name="Robotics Research",
            owner=self.owner,
        )
        self.other_project = Project.objects.create(
            name="Other Research",
            owner=self.owner,
        )

        self.run = AgentRun.objects.create(
            project=self.project,
            request="Research robot navigation",
            status="RUNNING",
        )

    @patch("services.agent_run_service.update_agent_heartbeat")
    @patch("services.agent_run_service.run_research_agent")
    def test_only_ready_owner_documents_from_run_project_are_allowed(
        self,
        mock_research_agent,
        mock_heartbeat,
    ):
        ready_document = Document.objects.create(
            project=self.project,
            uploaded_by=self.owner,
            original_filename="robot_specs.pdf",
            file_type="pdf",
            status="READY",
        )

        Document.objects.create(
            project=self.project,
            uploaded_by=self.owner,
            original_filename="pending.pdf",
            file_type="pdf",
            status="PROCESSING",
        )

        Document.objects.create(
            project=self.other_project,
            uploaded_by=self.owner,
            original_filename="other_project.pdf",
            file_type="pdf",
            status="READY",
        )

        Document.objects.create(
            project=self.project,
            uploaded_by=self.other_user,
            original_filename="other_user.pdf",
            file_type="pdf",
            status="READY",
        )

        mock_research_agent.return_value = {
            "report": "Test research report",
            "agent_trace": [],
        }

        execute_agent_run(self.run)

        mock_research_agent.assert_called_once()

        kwargs = mock_research_agent.call_args.kwargs

        self.assertEqual(kwargs["question"], self.run.request)
        self.assertEqual(kwargs["project_id"], str(self.project.id))
        self.assertEqual(
            set(kwargs["allowed_document_ids"]),
            {ready_document.id},
        )

        self.run.refresh_from_db()
        self.assertEqual(self.run.status, "COMPLETED")
        self.assertEqual(self.run.result, "Test research report")


    
    @patch("services.agent_run_service.update_agent_heartbeat")
    @patch("services.agent_run_service.run_research_agent")
    def test_research_agent_failure_is_recorded_and_reraised(
        self,
        mock_research_agent,
        mock_heartbeat,
    ):
        mock_research_agent.side_effect = RuntimeError("Research service unavailable")

        with self.assertRaisesRegex(
            RuntimeError,
            "Research service unavailable",
        ):
            execute_agent_run(self.run)

        self.run.refresh_from_db()

        self.assertNotEqual(self.run.status, "COMPLETED")
        self.assertEqual(
            self.run.error_msg,
            "Research service unavailable",
        )
        self.assertTrue(
            any(
                entry.get("agent") == "workflow"
                and entry.get("status") == "FAILED"
                for entry in self.run.agent_trace
            )
        )



class RAGRetrievalSecurityTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="rag_owner",
            password="test-pass-12345",
        )
        self.other_user = User.objects.create_user(
            username="rag_other",
            password="test-pass-12345",
        )

        self.project = Project.objects.create(
            name="RAG Project",
            owner=self.owner,
        )

        self.allowed_doc = Document.objects.create(
            project=self.project,
            uploaded_by=self.owner,
            original_filename="allowed.pdf",
            file_type="pdf",
            status="READY",
        )

        self.other_doc = Document.objects.create(
            project=self.project,
            uploaded_by=self.other_user,
            original_filename="other.pdf",
            file_type="pdf",
            status="READY",
        )

    def create_chunk(self, document, index, content, embedding):
        return DocumentChunk.objects.create(
            document=document,
            chunk_index=index,
            content=content,
            embedding=embedding,
        )

    @patch("apps.documents.retrieval_service.generate_embedding")
    def test_retrieval_returns_only_allowed_document_chunks(
        self,
        mock_embedding,
    ):
        mock_embedding.return_value = [1.0, 0.0]

        allowed_chunk = self.create_chunk(
            self.allowed_doc, 0, "Allowed robot information", [1.0, 0.0]
        )
        self.create_chunk(
            self.other_doc, 0, "Private robot information", [1.0, 0.0]
        )

        results = retrieve_relevant_chunks(
            question="robot information",
            allowed_document_ids=[self.allowed_doc.id],
            min_similarity=0.35,
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["chunk_id"], str(allowed_chunk.id))
        self.assertEqual(results[0]["filename"], "allowed.pdf")

    @patch("apps.documents.retrieval_service.generate_embedding")
    def test_retrieval_excludes_chunks_from_non_ready_documents(
        self,
        mock_embedding,
    ):
        mock_embedding.return_value = [1.0, 0.0]

        self.allowed_doc.status = "PROCESSING"
        self.allowed_doc.save(update_fields=["status"])

        self.create_chunk(
            self.allowed_doc, 0, "Not ready content", [1.0, 0.0]
        )

        results = retrieve_relevant_chunks(
            question="robot information",
            allowed_document_ids=[self.allowed_doc.id],
        )

        self.assertEqual(results, [])

    @patch("apps.documents.retrieval_service.generate_embedding")
    def test_retrieval_sorts_by_similarity_and_respects_top_k(
        self,
        mock_embedding,
    ):
        mock_embedding.return_value = [1.0, 0.0]

        lower_match = self.create_chunk(
            self.allowed_doc, 0, "Lower similarity", [0.8, 0.6]
        )
        higher_match = self.create_chunk(
            self.allowed_doc, 1, "Higher similarity", [1.0, 0.0]
        )

        results = retrieve_relevant_chunks(
            question="robot information",
            allowed_document_ids=[self.allowed_doc.id],
            top_k=1,
            min_similarity=0.35,
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["chunk_id"], str(higher_match.id))
        self.assertGreater(
            results[0]["similarity"],
            0.35,
        )