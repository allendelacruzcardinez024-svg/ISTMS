from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from tickets.models import Profile, Category, Ticket, TicketUpdate

class Command(BaseCommand):
    help = "Create demo users, categories, and sample tickets."

    def handle(self, *args, **kwargs):
        categories = [
            ("Hardware", "Laptop, desktop, peripherals and physical equipment"),
            ("Software", "Business applications and installation"),
            ("Network", "Internet, Wi-Fi, LAN and connectivity"),
            ("Account Access", "Password, email and access concerns"),
            ("Printer", "Printing, scanning and printer connectivity"),
            ("Other", "Other technology-related services"),
        ]
        for name, desc in categories:
            Category.objects.get_or_create(name=name, defaults={"description": desc})

        demo = [
            ("employee", "Juan", "Dela Cruz", "employee", "employee", "Operations", "EMP-001"),
            ("technician", "Rafael", "Santos", "technician", "technician", "IT Support", "TECH-001"),
            ("admin", "Maria", "Santos", "admin", "admin", "IT", "ADM-001"),
            ("manager", "John", "Lim", "manager", "manager", "Operations", "MGR-001"),
        ]
        users = {}
        for key, first, last, username, role, dept, empid in demo:
            u, created = User.objects.get_or_create(username=username, defaults={
                "first_name": first, "last_name": last, "email": f"{username}@nexora.local"
            })
            u.set_password("password123")
            u.first_name, u.last_name, u.email = first, last, f"{username}@nexora.local"
            if role == "admin":
                u.is_staff = True
                u.is_superuser = True
            u.save()
            Profile.objects.update_or_create(
                user=u,
                defaults={
                    "role": role,
                    "department": dept,
                    "employee_id": empid,
                    "avatar_initials": (first[0] + last[0]).upper(),
                },
            )
            users[key] = u
            users[username] = u

        if Ticket.objects.count() == 0:
            data = [
                ("Cannot access email", "Account Access", "high", "in_progress", "employee", "technician", "Dell Latitude / Outlook"),
                ("Printer not working", "Printer", "medium", "assigned", "employee", "technician", "HP LaserJet"),
                ("Laptop running slow", "Hardware", "low", "pending", "employee", None, "Dell Latitude"),
                ("Software installation", "Software", "medium", "resolved", "employee", "technician", "Adobe Acrobat"),
                ("Network connection issue", "Network", "high", "closed", "employee", "technician", "Office Wi-Fi"),
            ]
            for title, cat, pri, stat, requester, tech, device in data:
                t = Ticket.objects.create(
                    title=title,
                    description=f"Demo support request: {title}. Please investigate and provide an update.",
                    category=Category.objects.get(name=cat),
                    priority=pri,
                    status=stat,
                    submitted_by=users[requester],
                    assigned_to=users.get(tech),
                    device_system=device,
                    location="Nexora Office",
                )
                TicketUpdate.objects.create(
                    ticket=t,
                    author=users.get(tech) or users[requester],
                    message="Ticket created and entered into the centralized support workflow.",
                )
        self.stdout.write(self.style.SUCCESS("ISTMS demo data is ready. Login password: password123"))
