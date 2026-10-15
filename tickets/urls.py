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
    path("tickets/<int:pk>/edit/", views.edit_ticket, name="ticket_edit"),
    path("tickets/<int:pk>/update/", views.ticket_update, name="ticket_update"),
    path("tickets/<int:pk>/employee-action/", views.ticket_employee_action, name="ticket_employee_action"),
    path("tickets/<int:pk>/assign/", views.assign_ticket, name="assign_ticket"),
    path("tickets/<int:pk>/feedback/", views.ticket_feedback, name="ticket_feedback"),
    path("reports/", views.reports, name="reports"),
    path("users/", views.user_management, name="user_management"),
    path("users/<int:pk>/edit/", views.user_edit, name="user_edit"),
    path("users/<int:pk>/delete/", views.user_delete, name="user_delete"),
    path("profile/", views.profile, name="profile"),
    path("profile/edit/", views.profile_edit, name="profile_edit"),
    path("notifications/<int:pk>/", views.notification_open, name="notification_open"),
    path("notifications/feed/", views.notifications_feed, name="notifications_feed"),
    path("notifications/mark-read/", views.notifications_mark_read, name="notifications_mark_read"),
    path("knowledge-base/", views.knowledge_base, name="knowledge_base"),
    path("settings/", views.settings_page, name="settings_page"),
]
