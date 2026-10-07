import uuid
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

class Profile(models.Model):
    ROLE_CHOICES = [
        ("employee", "Employee"),
        ("technician", "IT Technician"),
        ("admin", "Administrator"),
        ("manager", "Manager"),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="employee")
    department = models.CharField(max_length=100, blank=True)
    employee_id = models.CharField(max_length=50, blank=True)
    avatar_initials = models.CharField(max_length=5, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.role}"

@receiver(post_save, sender=User)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    if created:
        initials = (instance.first_name[:1] + instance.last_name[:1]).upper() if (instance.first_name or instance.last_name) else instance.username[:2].upper()
        Profile.objects.get_or_create(
            user=instance,
            defaults={
                "role": "admin" if instance.is_superuser else "employee",
                "avatar_initials": initials,
            },
        )

class Category(models.Model):
    name = models.CharField(max_length=80)
    description = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.name

class Ticket(models.Model):
    PRIORITIES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    ]
    STATUSES = [
        ("pending", "Pending"),
        ("assigned", "Assigned"),
        ("in_progress", "In Progress"),
        ("resolved", "Resolved"),
        ("closed", "Closed"),
    ]
    ticket_number = models.CharField(max_length=30, unique=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    priority = models.CharField(max_length=20, choices=PRIORITIES, default="medium")
    status = models.CharField(max_length=20, choices=STATUSES, default="pending")
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="submitted_tickets")
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_tickets")
    device_system = models.CharField(max_length=120, blank=True)
    location = models.CharField(max_length=150, blank=True)
    attachment = models.FileField(upload_to="ticket_files/", blank=True, null=True)
    resolution = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            year = self.created_at.strftime('%Y') if self.created_at else timezone.now().strftime('%Y')
            self.ticket_number = f"TKT-{year}-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.ticket_number

class TicketUpdate(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="updates")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

class Feedback(models.Model):
    ticket = models.OneToOneField(Ticket, on_delete=models.CASCADE, related_name="feedback")
    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
