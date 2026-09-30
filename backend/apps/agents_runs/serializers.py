from .models import *
from ..projects.models import *
from rest_framework import serializers


class AgentRunSerializers(serializers.ModelSerializer):
    serializers.PrimaryKeyRelatedField(queryset=Project.objects.all(),
        required=True)
    request = serializers.CharField(allow_blank = False,required=True)
    class Meta:
        model = AgentRun
        fields = ['project','request']

    # def validate(self,attrs):
    #     if not attrs:
    #         raise serializers.ValidationError("The request payload cannot be empty.")
            
    #     return attrs    