from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .memory_policy import update_user_preference
from .memory_service import save_memory
from .models import Conversation,LongTermMemory
from .serializers import (
    ConversationSerializer,
    ConversationMessageSerializer,
    LongTermMemoryCreateSerializer
)

class ConversationListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        conversations = Conversation.objects.filter(
            user=request.user
        ).order_by("-updated_at")

        serializer = ConversationSerializer(
            conversations,
            many=True,
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ConversationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        conversation = serializer.save(user=request.user)

        return Response(
            ConversationSerializer(conversation).data,
            status=status.HTTP_201_CREATED,
        )


class ConversationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_conversation(self, request, conversation_id):
        return get_object_or_404(
            Conversation.objects.filter(user=request.user),
            id=conversation_id,
        )

    def get(self, request, conversation_id):
        conversation = self.get_conversation(
            request,
            conversation_id,
        )

        messages = conversation.messages.all()

        return Response(
            {
                **ConversationSerializer(conversation).data,
                "messages": ConversationMessageSerializer(
                    messages,
                    many=True,
                ).data,
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request, conversation_id):
        conversation = self.get_conversation(
            request,
            conversation_id,
        )

        conversation.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
    


class LongTermMemoryListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        memories = LongTermMemory.objects.filter(
            user=request.user,
        ).order_by("-created_at")

        data = [
            {
                "id": str(memory.id),
                "memory_type": memory.memory_type,
                "content": memory.content,
                "created_at": memory.created_at,
            }
            for memory in memories
        ]

        return Response(data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = LongTermMemoryCreateSerializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)

        memory = save_memory(
            user=request.user,
            content=serializer.validated_data["content"],
            memory_type="PREFERENCE",
        )

        return Response(
            LongTermMemoryCreateSerializer(memory).data,
            status=status.HTTP_201_CREATED,
        )



class LongTermMemoryDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, memory_id):
        serializer = LongTermMemoryCreateSerializer(
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)

        if "content" not in serializer.validated_data:
            return Response(
                {"content": "This field is required for an update."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        memory = update_user_preference(
            user=request.user,
            memory_id=memory_id,
            new_preference=serializer.validated_data["content"],
        )

        return Response(
            LongTermMemoryCreateSerializer(memory).data,
            status=status.HTTP_200_OK,
        )

    def delete(self, request, memory_id):
        memory = get_object_or_404(
            LongTermMemory.objects.filter(user=request.user),
            id=memory_id,
        )

        memory.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
