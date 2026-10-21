
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from services.agent_nodes import plan_research


class PlanResearchMemoryTests(SimpleTestCase):

    @patch("services.agent_nodes.search_memories")
    @patch("services.agent_nodes.get_user_model")
    @patch("services.agent_nodes.get_final_llm")
    def test_research_continues_when_memory_retrieval_fails(
        self,
        mock_get_llm,
        mock_get_user_model,
        mock_search_memories,
    ):
        mock_user = MagicMock()
        mock_get_user_model.return_value.objects.filter.return_value.first.return_value = (
            mock_user
        )

        mock_search_memories.side_effect = RuntimeError(
            "Embedding service unavailable"
        )

        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = (
            '["Question one?", "Question two?", "Question three?"]'
        )
        mock_get_llm.return_value = mock_llm

        state = {
            "messages": [
                MagicMock(content="Research Python agent frameworks")
            ],
            "user_id": "test-user-id",
            "agent_trace": [],
        }

        result = plan_research(state)

        self.assertEqual(len(result["research_questions"]), 3)
        self.assertTrue(
            any(
                entry["agent"] == "memory_retriever"
                and entry["status"] == "FAILED"
                for entry in result["agent_trace"]
            )
        )

        prompt = mock_llm.invoke.call_args.args[0]
        self.assertIn("No relevant memories found.", prompt)
