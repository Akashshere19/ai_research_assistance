from django.shortcuts import render
from .serializers import *
from rest_framework.decorators import APIView
from rest_framework import status   
from rest_framework.response import Response
from rest_framework.serializers import Serializer

# Create your views here.

class AgentRunView(APIView):
    def post(self,request):
            data = request.data

            serializer = AgentRunSerializers(data=data)
            if serializer.is_valid():
                  serializer.save()
                  return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)