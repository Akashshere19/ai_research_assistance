from rest_framework import serializers
from apps.projects.models import Project
from apps.conversations.models import Conversation
from .models import AgentRun
from django.utils import timezone

class AgentRunCreateSerializer(serializers.ModelSerializer):
    """Only client-controlled input; lifecycle fields are always server-managed."""
    project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.none())
    request = serializers.CharField(allow_blank=False, trim_whitespace=True, max_length=20000)
    conversation = serializers.PrimaryKeyRelatedField(
                queryset=Conversation.objects.none(),
                required=False,
                allow_null=True,
            )

    class Meta:
        model = AgentRun
        fields = ["project", "request","conversation"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = self.context.get("request").user if self.context.get("request") else None
        if user is not None and user.is_authenticated:
            projects = Project.objects.all() if user.is_superuser else Project.objects.filter(owner=user)
            self.fields["project"].queryset = projects
            conversations = Conversation.objects.filter(user=user)
            self.fields["conversation"].queryset = conversations


class AgentRunDetailsSerializer(serializers.ModelSerializer):
    project = serializers.UUIDField(source="project_id", read_only=True)

    class Meta:
        model = AgentRun
        fields = [
            "id", "project", "request", "result", "status", "agent_trace",
            "created_at", "started_at", "completed_at", "last_heartbeat_at", "error_msg",
        ]
        read_only_fields = fields



class AgentRunUpdateSerializers(serializers.ModelSerializer):
       """Change status of project query"""
       

       status = serializers.ChoiceField(
                    choices=AgentRun.STATUS,
                    required=True)

       class Meta:
            model = AgentRun
            fields = ['id','status']
       def validate(self,attrs):
            # print("attrs::::",attrs)
            new_status = attrs.get('status')
            if new_status and self.instance:
                 current_status = self.instance.status
                 allowed_transitions = {
                            "CREATED": ["QUEUED", "FAILED"],
                            "QUEUED": ["RUNNING", "FAILED"],
                            "RUNNING": ["COMPLETED", "FAILED"],
                            "COMPLETED": [],
                            "FAILED": [],
                        }
                 if new_status not in allowed_transitions[current_status]:
                                raise serializers.ValidationError({
                            "status": (
                                f"Invalid transition from {current_status} "
                                f"to {new_status}."
                            )
                        })
           
            return attrs
       
       def update(self, instance, validated_data):
            new_status = validated_data["status"]
            current_status = instance.status

            if current_status == "QUEUED" and new_status == "RUNNING":
                instance.started_at = timezone.now()

            elif  new_status in ["COMPLETED", "FAILED"]:
                instance.completed_at = timezone.now()

            instance.status = new_status
            instance.save()
            return instance




class ProjectRunDetailsSerializer(serializers.ModelSerializer):
    agent_runs = AgentRunDetailsSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = ["id", "name", "created_at", "agent_runs"]
        read_only_fields = fields


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["id", "name", "created_at"]
        read_only_fields = ["id", "created_at"]
