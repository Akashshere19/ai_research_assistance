from .models import *
from ..projects.models import *
from rest_framework import serializers
from django.utils import timezone



# print("timezone :::",timezone.localtime(timezone.now()))
class AgentRunSerializers(serializers.ModelSerializer):
    project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all(),
        required=True)
    request = serializers.CharField(allow_blank = False,required=True)
    class Meta:
        model = AgentRun
        fields = ['project','request']

class AgentRunDetailsSerializers(serializers.ModelSerializer):
    """Return details of project query in GET method"""
    class Meta:
        model = AgentRun
        read_only_fields = [
                'id',
                'status',
                'created_at',
                'started_at',
                'completed_at',
                'error_msg',
        ] 
        exclude = ["project"] 

# class AgentRunReturnStatusSerializers(serializers.ModelSerializer):
       


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


class ProjectRunDetailsSerializers(serializers.ModelSerializer):
              """return all agents runs list under  project's uuid"""
              agent_runs = AgentRunDetailsSerializers(many=True, read_only=True)
              class Meta:
                    model = Project 
                    fields = ['id', 'name', 'agent_runs']