from django.urls import path
from .views import IngestView, ExtractView, AskView, AuditView, HealthCheckView

urlpatterns = [
    path('ingest/', IngestView.as_view(), name='ingest'),
    path('extract/<int:doc_id>/', ExtractView.as_view(), name='extract'),
    path('ask/', AskView.as_view(), name='ask'),
    path('audit/<int:doc_id>/', AuditView.as_view(), name='audit'),
    path('healthz/', HealthCheckView.as_view(), name='healthz'), 
]