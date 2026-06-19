"""
apps/core/urls.py — Core / dashboard root URLs
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.DashboardIndexView.as_view(), name='dashboard-index'),
]
