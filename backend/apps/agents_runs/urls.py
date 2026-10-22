from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from .views import AgentRunView, ProjectRunView, AgentRunStatuswiseViews, \
                     ApiTokenView,research_page

urlpatterns = [
    path("api/auth/token/", ApiTokenView.as_view(), name="api-token"),
    path("api/projects/", ProjectRunView.as_view(), name="projects"),
    path("api/projects/<uuid:project_id>/", ProjectRunView.as_view(), name="project-detail"),
    path("api/agent-runs/", AgentRunView.as_view(), name="agent-runs"),
    path("api/agent-runs/<uuid:uuid>/", AgentRunView.as_view(), name="agent-run-detail"),
    path("api/agent-runs/status/<str:status_code>/", AgentRunStatuswiseViews.as_view(), name="agent-runs-by-status"),

          path("research-ui/", research_page, name="research_page"),
          path(
        "accounts/login/",
         LoginView.as_view(
        template_name="registration/login.html",
        next_page="/research-ui/",
    ),
        name="login",
    ),
    path(
        "accounts/logout/",
        LogoutView.as_view(next_page="login"),
        name="logout",
    ),

]
