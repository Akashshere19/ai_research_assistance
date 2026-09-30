from django.urls import path
from .views import AgentRunView
urlpatterns = [
    path('api/agent-runs/',AgentRunView.as_view(),name="agent run")
]