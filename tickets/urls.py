from django.urls import path
from . import views

urlpatterns = [
    path("", views.login_view, name="login"),
    path("register/", views.register, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("submit-ticket/", views.submit_ticket, name="submit_ticket"),
    path("my-tickets/", views.my_tickets, name="my_tickets"),
    path("tickets/", views.all_tickets, name="all_tickets"),
    path("tickets/<int:pk>/", views.ticket_detail, name="ticket_detail"),
    path("tickets/<int:pk>/update/", views.ticket_update, name="ticket_update"),
    path("tickets/<int:pk>/assign/", views.assign_ticket, name="assign_ticket"),
    path("tickets/<int:pk>/feedback/", views.ticket_feedback, name="ticket_feedback"),
    path("reports/", views.reports, name="reports"),
    path("users/", views.user_management, name="user_management"),
    path("profile/", views.profile, name="profile"),
    path("knowledge-base/", views.knowledge_base, name="knowledge_base"),
    path("settings/", views.settings_page, name="settings_page"),
]