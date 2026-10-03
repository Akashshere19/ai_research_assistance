from django.urls import path
from .views import AgentRunView,AgentRun,ProjectRunView,AgentRunStatuswiseViews
urlpatterns = [
    path('api/agent-runs/',AgentRunView.as_view(),name="agent-runs"),
    path('api/agent-runs/<uuid:uuid>/', AgentRunView.as_view(), name='agent-run-detail'),
    path('api/agent-runs/status/<str:status_code>/', AgentRunStatuswiseViews.as_view(), name='agent-run-detail'),
    path('api/projects/<uuid:project_id>/', ProjectRunView.as_view(), name='agent-run-project-detail')

]