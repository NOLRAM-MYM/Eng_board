"""apps/app_physics/urls.py"""
from django.urls import path
from . import views

app_name = 'physics'

urlpatterns = [
    path('', views.PhysicsPageView.as_view(), name='physics-index'),
    path('projectile/calculate/', views.ProjectileCalculateView.as_view(), name='projectile-calculate'),
]
