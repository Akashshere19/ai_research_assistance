from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from .models import Conversation, ConversationMessage
from unittest.mock import patch
from apps.conversations.memory_policy import save_user_preference,update_user_preference
from apps.conversations.models import LongTermMemory

from apps.conversations.memory_service import search_memories



User = get_user_model()


class ConversationAPITests(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username="user1",
            password="test-password-123",
        )
        self.user2 = User.objects.create_user(
            username="user2",
            password="test-password-123",
        )

        self.conversation1 = Conversation.objects.create(
            user=self.user1,
            title="Robotics Research",
        )
        self.conversation2 = Conversation.objects.create(
            user=self.user2,
            title="AI Research",
        )

        self.list_url = "/api/conversations/"
        self.client.force_authenticate(user=self.user1)

    def test_authenticated_user_can_create_conversation(self):
        response = self.client.post(
            self.list_url,
            {"title": "New Research"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "New Research")

        conversation = Conversation.objects.get(
            id=response.data["id"]
        )
        self.assertEqual(conversation.user, self.user1)

    def test_user_sees_only_their_conversations(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        returned_ids = {
            str(item["id"]) for item in response.data
        }

        self.assertEqual(
            returned_ids,
            {str(self.conversation1.id)},
        )

    def test_user_can_retrieve_own_conversation_and_messages(self):
        ConversationMessage.objects.create(
            conversation=self.conversation1,
            role="user",
            content="Research autonomous navigation.",
        )
        ConversationMessage.objects.create(
            conversation=self.conversation1,
            role="assistant",
            content="Here is the research summary.",
        )

        response = self.client.get(
            f"{self.list_url}{self.conversation1.id}/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["messages"]), 2)
        self.assertEqual(
            response.data["messages"][0]["role"],
            "user",
        )

    def test_user_cannot_retrieve_another_users_conversation(self):
        response = self.client.get(
            f"{self.list_url}{self.conversation2.id}/"
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_cannot_delete_another_users_conversation(self):
        response = self.client.delete(
            f"{self.list_url}{self.conversation2.id}/"
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.assertTrue(
            Conversation.objects.filter(
                id=self.conversation2.id
            ).exists()
        )

    def test_unauthenticated_user_cannot_access_conversations(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)    






class MemoryPolicyTests(APITestCase):

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="memory_test_user",
            password="test-password-123",
        )

    @patch(
        "apps.conversations.memory_service.generate_embedding",
        return_value=[0.1] * 384,
    )
    def test_saves_explicit_user_preference(self, mock_embedding):
        memory = save_user_preference(
            user=self.user,
            preference="I prefer Python examples.",
        )

        self.assertEqual(memory.user, self.user)
        self.assertEqual(memory.memory_type, "PREFERENCE")
        self.assertEqual(
            memory.content,
            "I prefer Python examples.",
        )
        self.assertEqual(len(memory.embedding), 384)
        mock_embedding.assert_called_once()

    def test_rejects_empty_preference(self):
        with self.assertRaises(ValueError):
            save_user_preference(
                user=self.user,
                preference="   ",
            )

    def test_rejects_missing_user(self):
        with self.assertRaises(ValueError):
            save_user_preference(
                user=None,
                preference="I prefer Python examples.",
            )

    def test_preference_is_not_saved_when_validation_fails(self):
        with self.assertRaises(ValueError):
            save_user_preference(
                user=self.user,
                preference="",
            )

        self.assertEqual(
            LongTermMemory.objects.filter(user=self.user).count(),
            0,
        )

    
    @patch(
        "apps.conversations.memory_service.generate_embedding",
        return_value=[0.1] * 384,
    )
    def test_duplicate_preference_is_not_saved_twice(self, mock_embedding):
        first = save_user_preference(
            user=self.user,
            preference="I prefer Python examples.",
        )

        second = save_user_preference(
            user=self.user,
            preference=" i prefer python examples. ",
        )

        self.assertEqual(first.id, second.id)
        self.assertEqual(
            LongTermMemory.objects.filter(
                user=self.user,
                memory_type="PREFERENCE",
            ).count(),
            1,
        )
        mock_embedding.assert_called_once()

    
    @patch(
        "apps.documents.embedding_service.generate_embedding",
        return_value=[0.2] * 384,
    )
    def test_updates_existing_preference(self, mock_embedding):
        memory = save_user_preference(
            user=self.user,
            preference="I prefer concise reports.",
        )

        updated = update_user_preference(
            user=self.user,
            memory_id=memory.id,
            new_preference="I prefer detailed reports.",
        )

        self.assertEqual(updated.id, memory.id)
        self.assertEqual(
            updated.content,
            "I prefer detailed reports.",
        )
        mock_embedding.assert_called_once()
    






class LongTermMemoryApiTests(APITestCase):

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="memory_owner",
            password="test-password-123",
        )
        self.other_user = User.objects.create_user(
            username="other_memory_owner",
            password="test-password-123",
        )

        self.memory = LongTermMemory.objects.create(
            user=self.user,
            memory_type="PREFERENCE",
            content="I prefer Python examples.",
            embedding=[0.1] * 384,
        )

        self.url = reverse(
            "memory-detail",
            kwargs={"memory_id": self.memory.id},
        )

    def test_user_can_delete_own_memory(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.delete(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )
        self.assertFalse(
            LongTermMemory.objects.filter(
                id=self.memory.id,
            ).exists()
        )

    def test_user_cannot_delete_another_users_memory(self):
        self.client.force_authenticate(user=self.other_user)

        response = self.client.delete(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertTrue(
            LongTermMemory.objects.filter(
                id=self.memory.id,
            ).exists()
        )

    def test_unauthenticated_user_cannot_delete_memory(self):
        self.client.force_authenticate(user=None)

        response = self.client.delete(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    
    def test_user_can_update_own_preference(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.patch(
            self.url,
            {
                "content": "I prefer detailed research reports.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.memory.refresh_from_db()
        self.assertEqual(
            self.memory.content,
            "I prefer detailed research reports.",
        )

    def test_user_cannot_update_another_users_preference(self):
        self.client.force_authenticate(user=self.other_user)

        response = self.client.patch(
            self.url,
            {
                "content": "Change someone else's preference.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.memory.refresh_from_db()
        self.assertEqual(
            self.memory.content,
            "I prefer Python examples.",
        )

    def test_update_rejects_empty_preference(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.patch(
            self.url,
            {"content": "   "},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
    



class MemorySearchTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="search_user",
            password="test-password-123",
        )
        self.other_user = User.objects.create_user(
            username="other_search_user",
            password="test-password-123",
        )

    @patch(
        "apps.conversations.memory_service.generate_embedding",
        return_value=[1.0, 0.0, 0.0],
    )
    def test_returns_most_similar_memory_first(self, mock_embedding):
        first = LongTermMemory.objects.create(
            user=self.user,
            memory_type="PREFERENCE",
            content="Python examples",
            embedding=[0.8, 0.6, 0.0],
        )
        second = LongTermMemory.objects.create(
            user=self.user,
            memory_type="PREFERENCE",
            content="Python tutorials",
            embedding=[1.0, 0.0, 0.0],
        )

        results = search_memories(
            user=self.user,
            query="Python learning",
            min_similarity=0.0,
        )

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["memory"].id, second.id)
        self.assertEqual(results[1]["memory"].id, first.id)

    @patch(
        "apps.conversations.memory_service.generate_embedding",
        return_value=[1.0, 0.0, 0.0],
    )
    def test_excludes_memories_below_similarity_threshold(
        self, mock_embedding
    ):
        LongTermMemory.objects.create(
            user=self.user,
            memory_type="PREFERENCE",
            content="Unrelated memory",
            embedding=[0.0, 1.0, 0.0],
        )

        results = search_memories(
            user=self.user,
            query="Python research",
            min_similarity=0.5,
        )

        self.assertEqual(results, [])

    @patch(
        "apps.conversations.memory_service.generate_embedding",
        return_value=[1.0, 0.0, 0.0],
    )
    def test_does_not_return_another_users_memories(
        self, mock_embedding
    ):
        other_memory = LongTermMemory.objects.create(
            user=self.other_user,
            memory_type="PREFERENCE",
            content="Private preference",
            embedding=[1.0, 0.0, 0.0],
        )

        results = search_memories(
            user=self.user,
            query="Find my preferences",
            min_similarity=0.0,
        )

        returned_ids = {
            item["memory"].id for item in results
        }

        self.assertNotIn(other_memory.id, returned_ids)

    def test_rejects_empty_query(self):
        with self.assertRaises(ValueError):
            search_memories(
                user=self.user,
                query="   ",
            )
