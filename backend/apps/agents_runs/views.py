from django.shortcuts import render
from .serializers import *
import logging
from rest_framework.decorators import APIView
from django.shortcuts import get_object_or_404
from rest_framework import status   
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from services.agent_run_service import execute_agent_run,mark_agent_run_failed
                                          
from .tasks import execute_agent_run_task,claim_agent_run


logger = logging.getLogger(__name__)
# Create your views here.


class AgentRunView(APIView):
    def post(self,request):
            data = request.data

            serializer = AgentRunSerializers(data=data)
            serializer.is_valid(raise_exception=True)
            agent_run = serializer.save()
            try:
                  task_result  = execute_agent_run_task.delay(str(agent_run.id))
                  # ai_response = execute_agent_run(agent_run)
                  # print('agent::',agent_run)
                  # print("Celery task ID:", task_result.id)
                  logger.info("Celery task ID::",task_result.id)
            except Exception as er:
                  logger.exception("Failed to enqueue AgentRun %s", agent_run.id)
                  mark_agent_run_failed(
                        agent_run,
                        "Unable to queue the background task."
                  )
                  response_serializer = AgentRunDetailsSerializers(agent_run)
                  return Response(
                                    response_serializer.data,
                                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                              )
            
            response_serializer = AgentRunDetailsSerializers(agent_run)
            return Response(response_serializer.data, 
                            status=status.HTTP_202_ACCEPTED)

    
    def get(self,request, uuid=None):
            if uuid is not None:
                  agent_run = get_object_or_404(AgentRun,id=uuid)
                  # print('agent model::',agent_search)
                  serializer = AgentRunDetailsSerializers(agent_run)
                  return Response(serializer.data,status=status.HTTP_200_OK)
            else:
                  agents_list = AgentRun.objects.all()
                  serializer = AgentRunDetailsSerializers(agents_list,many=True)
                  # if serializer.is_valid():
                  return Response(serializer.data,status=status.HTTP_200_OK)
            
    def patch(self,request,uuid=None):
          data = request.data
          instance = get_object_or_404(AgentRun,id=uuid)
          serializer = AgentRunUpdateSerializers(instance,data=data,partial=True)  
          serializer.is_valid(raise_exception=True)
          print('serializers::',serializer)
          serializer.save()
          return Response(serializer.data, status=status.HTTP_200_OK)  

            
class ProjectRunView(APIView):
      def get(self,request,project_id=None):
            print('project id:::',project_id)
            if project_id is not None:
                  projects = get_object_or_404(Project,id = project_id)
                  print("projects",projects)
                  serializer = ProjectRunDetailsSerializers(projects)
                  return Response(serializer.data, status=status.HTTP_200_OK)
        
            return Response({"error": "Project id is required"}, status=status.HTTP_400_BAD_REQUEST)

class AgentRunStatuswiseViews(APIView):
      def get(self,request,status_code):
            valid_statuses = [choice[0] for choice in AgentRun.STATUS]
            if status_code not in valid_statuses:
                  return Response(
                        {"status": "Invalid status"},
                        status=status.HTTP_400_BAD_REQUEST
                  )
            
            if status_code is not None:
                  agent_runs = AgentRun.objects.filter(status=status_code)
                  serializer = AgentRunDetailsSerializers(agent_runs,many=True)
                  return Response(serializer.data,status=status.HTTP_200_OK)      