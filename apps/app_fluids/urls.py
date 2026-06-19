"""
apps/app_fluids/urls.py
========================
URL routing for the Fluid Mechanics module.
"""
from django.urls import path
from . import views

app_name = 'fluids'

urlpatterns = [
    # HTML page
    path('', views.PipeFlowPageView.as_view(), name='pipe-flow-page'),

    # REST API endpoints
    path('pipe-flow/calculate/', views.PipeFlowCalculateView.as_view(), name='pipe-flow-calculate'),
    path('pipe-flow/schema/', views.PipeFlowSchemaView.as_view(), name='pipe-flow-schema'),
]
