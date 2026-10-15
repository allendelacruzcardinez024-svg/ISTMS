from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from tickets.models import Profile, Category, Ticket, TicketUpdate

class Command(BaseCommand):
    help = "Create demo users, categories, and sample tickets."

    def add_arguments(self, parser):
        parser.add_argument(
            "--specialists-only",
            action="store_true",
            help="Create or update only the specialist technician accounts.",
        )

    def handle(self, *args, **kwargs):
        categories = [
            ("Hardware", "Laptop, desktop, peripherals and physical equipment"),
            ("Software", "Business applications and installation"),
            ("Network", "Internet, Wi-Fi, LAN and connectivity"),
            ("Account Access", "Password, email and access concerns"),
            ("Other", "Other technology-related services"),
        ]
        for name, desc in categories:
            Category.objects.get_or_create(name=name, defaults={"description": desc})

        specialists = [
            ("hardware_support", "Hardware Support", "Technician", "hardware_support", "technician", "IT Support Services", "TECH-002"),
            ("software_support", "Software Support", "Specialist", "software_support", "technician", "IT Support Services", "TECH-003"),
            ("network_support", "Network Support", "Technician", "network_support", "technician", "Network and Infrastructure", "TECH-004"),
            ("access_support", "IT Access Support", "Specialist", "access_support", "technician", "IT Support Services", "TECH-005"),
            ("printer_support", "Printer Support", "Technician", "printer_support", "technician", "IT Support Services", "TECH-006"),
        ]
        demo = [
            ("juan", "PAUL", "ELINIEL", "juan", "employee", "Network and Infrastructure", "EMP-002"),
            ("employee", "REDFORD", "BISCARRA", "employee", "employee", "Human Resources", "EMP-001"),
            ("technician", "IT Support", "Technician", "technician", "technician", "IT Support Services", "TECH-001"),
            ("employee_lander", "LANDER", "RAGMAC", "admin", "employee", "Operations", "EMP-003"),
            ("manager", "DUDDY", "ALBERT", "manager", "manager", "IT Support Services", "MGR-001"),
        ]
        if kwargs["specialists_only"]:
            demo = specialists
        else:
            demo.extend(specialists)
        users = {}
        for key, first, last, username, role, dept, user_id in demo:
            u, created = User.objects.get_or_create(username=username, defaults={
                "first_name": first, "last_name": last, "email": f"{username}@nexora.local"
            })
            u.set_password("password123")
            u.first_name, u.last_name, u.email = first, last, f"{username}@nexora.local"
            u.is_staff = role == "admin"
            u.is_superuser = role == "admin"
            u.save()
            Profile.objects.update_or_create(
                user=u,
                defaults={
                    "role": role,
                    "department": dept,
                    "user_identifier": user_id,
                    "avatar_initials": (first[0] + last[0]).upper(),
                },
            )
            users[key] = u
            users[username] = u

        if not kwargs["specialists_only"] and Ticket.objects.count() == 0:
            data = [
                ("Cannot access email", "Account Access", "high", "in_progress", "employee", "technician", "Dell Latitude / Outlook"),
                ("Printer not working", "Hardware", "medium", "assigned", "employee", "technician", "HP LaserJet"),
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
        if kwargs["specialists_only"]:
            self.stdout.write(self.style.SUCCESS("Specialist technician accounts are ready. Login password: password123"))
        else:
            self.stdout.write(self.style.SUCCESS("ISTMS demo data is ready. Login password: password123"))
