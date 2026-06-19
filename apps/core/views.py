"""
apps/core/views.py — Core views (dashboard landing page)
"""
from django.views.generic import TemplateView


class DashboardIndexView(TemplateView):
    """Main dashboard landing page listing all scientific modules."""
    template_name = 'dashboard/index.html'
