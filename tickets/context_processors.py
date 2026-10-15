def notification_context(request):
    if not request.user.is_authenticated:
        return {"notifications": [], "unread_notification_count": 0}

    user_notifications = request.user.notifications.select_related("ticket", "ticket__submitted_by")
    return {
        "notifications": user_notifications[:8],
        "unread_notification_count": user_notifications.filter(read_at__isnull=True).count(),
    }