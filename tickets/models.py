import uuid
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

class Profile(models.Model):
    DEPARTMENT_CHOICES = [
        ("Information Technology", "Information Technology"),
        ("IT Support Services", "IT Support Services"),
        ("Network and Infrastructure", "Network and Infrastructure"),
        ("Human Resources", "Human Resources"),
        ("Operations", "Operations"),
    ]
    ROLE_CHOICES = [
        ("user", "User"),
        ("admin", "Admin"),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="user")
    department = models.CharField(max_length=100, blank=True, choices=DEPARTMENT_CHOICES)
    user_identifier = models.CharField(max_length=50, blank=True, verbose_name="User ID")
    avatar_initials = models.CharField(max_length=5, blank=True)
    profile_picture = models.FileField(upload_to="profile_pictures/", blank=True)

    def get_role_display(self):
        return "Admin" if self.role in {"admin", "manager"} or self.user.is_superuser else "User"

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.role}"

@receiver(post_save, sender=User)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    initials = (instance.first_name[:1] + instance.last_name[:1]).upper() if (instance.first_name or instance.last_name) else instance.username[:2].upper()
    Profile.objects.get_or_create(
        user=instance,
        defaults={
            "role": "admin" if instance.is_superuser else "user",
            "avatar_initials": initials,
        },
    )

class Category(models.Model):
    name = models.CharField(max_length=80)
    description = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.name


ISSUE_TYPES_BY_CATEGORY = {
    "Hardware": [
        "Computer won't turn on",
        "Monitor displays a black screen",
        "Keyboard keys are not working",
        "Mouse is unresponsive",
        "Laptop battery is not charging",
        "Computer overheats",
        "Broken computer components",
        "USB port is not working",
        "RAM or storage upgrade request",
        "Laptop screen is damaged",
    ],
    "Software": [
        "Application crashes unexpectedly",
        "Software installation request",
        "Operating system error",
        "Application freezes",
        "Microsoft Office is not working",
        "Software update failure",
        "Browser is not responding",
        "Company application error",
        "Missing or corrupted files",
        "Software license activation issue",
    ],
    "Network": [
        "Office Wi-Fi not connecting",
        "Slow internet connection",
        "No internet access",
        "LAN connection failure",
        "VPN connection problem",
        "Network cable disconnected",
        "IP address conflict",
        "DNS resolution error",
        "Shared network folder inaccessible",
        "Network printer connection failure",
    ],
    "Account Access": [
        "Forgot password",
        "Account locked",
        "Unable to log in",
        "Password reset request",
        "Email account access problem",
        "Microsoft 365 sign-in error",
        "New employee account request",
        "Account permission request",
        "Multi-factor authentication issue",
        "Employee account deactivation request",
    ],
    "Other": [
        "IT equipment setup request",
        "New workstation configuration",
        "Data backup request",
        "File recovery request",
        "Email configuration assistance",
        "IT security concern",
        "Suspicious email or phishing report",
        "IT equipment relocation",
        "Computer maintenance request",
        "Technical assistance or consultation",
    ],
}


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
    issue_type = models.CharField(max_length=120, blank=True)
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

class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="notifications")
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

class Feedback(models.Model):
    ticket = models.OneToOneField(Ticket, on_delete=models.CASCADE, related_name="feedback")
    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
