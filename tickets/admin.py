from django.contrib import admin
from .models import Profile, Category, Ticket, TicketUpdate, Feedback, Notification

admin.site.register(Profile)
admin.site.register(Category)
admin.site.register(Ticket)
admin.site.register(TicketUpdate)
admin.site.register(Feedback)
admin.site.register(Notification)
