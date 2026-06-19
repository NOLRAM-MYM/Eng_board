"""apps/app_chemistry/urls.py"""
from django.urls import path
from . import views

app_name = 'chemistry'

urlpatterns = [
    path('', views.ChemistryPageView.as_view(), name='chemistry-index'),
    path('element/<str:identifier>/', views.ElementPropertyView.as_view(), name='element-property'),
]
