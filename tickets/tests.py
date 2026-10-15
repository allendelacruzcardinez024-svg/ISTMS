from django import forms
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import ManagedUserForm, ProfileUpdateForm, TicketForm, TicketManagementForm
from .models import Category, Feedback, Notification, Profile, Ticket, TicketUpdate


class AccountAuthenticationTests(TestCase):
    def test_new_account_can_sign_in_after_signing_out(self):
        registration_response = self.client.post(
            reverse("register"),
            {
                "username": "new-employee",
                "email": "new-employee@example.com",
                "password": "secure-password-123",
                "password2": "secure-password-123",
            },
        )

        user = get_user_model().objects.get(username="new-employee")
        self.assertRedirects(registration_response, reverse("dashboard"))
        self.assertTrue(user.check_password("secure-password-123"))
        self.assertTrue(hasattr(user, "profile"))
        self.assertEqual(self.client.get(reverse("logout")).status_code, 302)

        login_response = self.client.post(
            reverse("login"),
            {"username": "NEW-EMPLOYEE", "password": "secure-password-123"},
        )

        self.assertRedirects(login_response, reverse("dashboard"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_login_accepts_the_display_name_used_by_the_system(self):
        user = get_user_model().objects.create_user(
            username="manager",
            first_name="DUDDY",
            last_name="ALBERT",
            password="password123",
        )

        response = self.client.post(
            reverse("login"),
            {
                "username": "DUDDY ALBERT BALMEO FONTANILLA",
                "password": "password123",
            },
        )

        self.assertRedirects(response, reverse("dashboard"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_requested_accounts_can_register_and_sign_in_with_demo_password(self):
        usernames = [
            "DUDDY ALBERT BALMEO FONTANILLA",
            "PAUL ELINIEL FLORES SIBUL",
            "REDFORD PERALTA BISCARRA",
            "LANDER RABE RAGMAC",
        ]

        for username in usernames:
            with self.subTest(username=username):
                registration_response = self.client.post(
                    reverse("register"),
                    {
                        "username": username,
                        "password": "demo 123",
                        "password2": "demo 123",
                    },
                )
                self.assertRedirects(registration_response, reverse("dashboard"))
                user = get_user_model().objects.get(username=username)
                self.assertEqual(user.email, "")

                self.client.get(reverse("logout"))
                login_response = self.client.post(
                    reverse("login"),
                    {"username": username, "password": "demo 123"},
                )

                self.assertRedirects(login_response, reverse("dashboard"))
                self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)
                self.client.get(reverse("logout"))

    def test_duplicate_email_login_selects_account_with_matching_password(self):
        users = get_user_model()
        users.objects.create_user(
            username="existing-manager",
            email="shared@example.com",
            password="old-password",
        )

        registration_response = self.client.post(
            reverse("register"),
            {
                "username": "new-manager-name",
                "email": "shared@example.com",
                "password": "demo 123",
                "password2": "demo 123",
            },
        )
        new_user = users.objects.get(username="new-manager-name")
        self.assertRedirects(registration_response, reverse("dashboard"))
        self.client.get(reverse("logout"))

        login_response = self.client.post(
            reverse("login"),
            {"username": "shared@example.com", "password": "demo 123"},
        )

        self.assertRedirects(login_response, reverse("dashboard"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), new_user.pk)


class UserManagementTests(TestCase):
    def test_department_choices_match_approved_departments(self):
        form = ProfileUpdateForm()
        department_values = [value for value, _label in form.fields["department"].choices if value]

        self.assertEqual(department_values, [
            "Information Technology",
            "IT Support Services",
            "Network and Infrastructure",
            "Human Resources",
            "Operations",
        ])

    def test_admin_can_update_user_department_from_edit_account(self):
        users = get_user_model()
        admin = users.objects.create_user(username="admin", password="password123")
        admin.profile.role = "admin"
        admin.profile.save(update_fields=["role"])
        target_user = users.objects.create_user(
            username="employee",
            first_name="Taylor",
            email="employee@example.com",
            password="password123",
        )
        target_user.profile.department = "Operations"
        target_user.profile.save(update_fields=["department"])
        self.client.force_login(admin)

        edit_response = self.client.get(reverse("user_edit", args=[target_user.pk]))
        save_response = self.client.post(
            reverse("user_edit", args=[target_user.pk]),
            {
                "first_name": "Taylor",
                "last_name": "Employee",
                "email": "employee@example.com",
                "role": "user",
                "department": "Human Resources",
                "is_active": "on",
            },
        )

        target_user.profile.refresh_from_db()
        self.assertContains(edit_response, "Department")
        self.assertEqual(edit_response.context["form"].fields["department"].initial, "Operations")
        self.assertRedirects(save_response, reverse("user_management"))
        self.assertEqual(target_user.profile.department, "Human Resources")

        clear_department_response = self.client.post(
            reverse("user_edit", args=[target_user.pk]),
            {
                "first_name": "Taylor",
                "last_name": "Employee",
                "email": "employee@example.com",
                "role": "user",
                "department": "",
                "is_active": "on",
            },
        )

        target_user.profile.refresh_from_db()
        self.assertRedirects(clear_department_response, reverse("user_management"))
        self.assertEqual(target_user.profile.department, "")

    def test_user_management_repairs_accounts_without_profiles(self):
        users = get_user_model()
        admin = users.objects.create_user(username="admin", password="password123")
        admin.profile.role = "admin"
        admin.profile.save(update_fields=["role"])
        orphaned_account = users.objects.create_user(
            username="orphaned-account",
            password="password123",
        )
        Profile.objects.filter(user=orphaned_account).delete()
        self.client.force_login(admin)

        response = self.client.get(reverse("user_management"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Profile.objects.filter(user=orphaned_account).exists())
        self.assertContains(response, "orphaned-account")

    def test_admin_can_delete_user_and_their_submitted_tickets(self):
        users = get_user_model()
        admin = users.objects.create_user(username="admin", password="password123")
        admin.profile.role = "admin"
        admin.profile.save(update_fields=["role"])
        target_user = users.objects.create_user(username="employee", password="password123")
        category = Category.objects.create(name="Hardware")
        ticket = Ticket.objects.create(
            title="Damaged keyboard",
            description="Several keys do not respond.",
            category=category,
            submitted_by=target_user,
        )
        self.client.force_login(admin)

        response = self.client.post(reverse("user_delete", args=[target_user.pk]))

        self.assertRedirects(response, reverse("user_management"))
        self.assertFalse(users.objects.filter(pk=target_user.pk).exists())
        self.assertFalse(Ticket.objects.filter(pk=ticket.pk).exists())

    def test_user_delete_rejects_get_and_prevents_self_deletion(self):
        users = get_user_model()
        admin = users.objects.create_user(username="admin", password="password123")
        admin.profile.role = "admin"
        admin.profile.save(update_fields=["role"])
        self.client.force_login(admin)

        get_response = self.client.get(reverse("user_delete", args=[admin.pk]))
        post_response = self.client.post(reverse("user_delete", args=[admin.pk]))

        self.assertEqual(get_response.status_code, 405)
        self.assertRedirects(post_response, reverse("user_management"))
        self.assertTrue(users.objects.filter(pk=admin.pk).exists())

    def test_non_admin_cannot_delete_users(self):
        users = get_user_model()
        requester = users.objects.create_user(username="employee", password="password123")
        target_user = users.objects.create_user(username="another-employee", password="password123")
        self.client.force_login(requester)

        response = self.client.post(reverse("user_delete", args=[target_user.pk]))

        self.assertRedirects(response, reverse("dashboard"))
        self.assertTrue(users.objects.filter(pk=target_user.pk).exists())

    def test_legacy_technician_and_duplicate_duddy_are_hidden_without_deleting_accounts(self):
        users = get_user_model()
        admin = users.objects.create_user(username="admin", password="password123")
        admin.profile.role = "admin"
        admin.profile.save()
        duddy = users.objects.create_user(
            username="DUDDY ALBERT BALMEO FONTANILLA",
            email="duddyalbert017@gmail.com",
            password="password123",
        )
        technician = users.objects.create_user(
            username="technician",
            email="ryuinmunoz12@gmail.com",
            password="password123",
        )
        technician.profile.role = "technician"
        technician.profile.save()
        manager = users.objects.create_user(
            username="manager",
            email="duddyalbert017@gmail.com",
            password="password123",
        )
        manager.profile.role = "manager"
        manager.profile.save()
        self.client.force_login(admin)

        response = self.client.get(reverse("user_management"))

        visible_usernames = [user.username for user in response.context["users"]]
        self.assertNotIn(duddy.username, visible_usernames)
        self.assertNotIn(technician.username, visible_usernames)
        self.assertIn(manager.username, visible_usernames)
        self.assertEqual(users.objects.get(pk=duddy.pk).email, "duddyalbert017@gmail.com")
        self.assertEqual(users.objects.get(pk=technician.pk).email, "ryuinmunoz12@gmail.com")

    def test_people_and_specialists_follow_requested_order_without_email_changes(self):
        users = get_user_model()
        expected_usernames = [
            "ALLEN JOHN DELA CRUZ CARDINEZ",
            "manager",
            "juan",
            "employee",
            "admin",
            "hardware_support",
            "software_support",
            "access_support",
            "network_support",
            "printer_support",
        ]
        emails = {username: f"{index}@example.com" for index, username in enumerate(expected_usernames)}

        for username in reversed(expected_usernames):
            user = users.objects.create_user(
                username=username,
                email=emails[username],
                password="password123",
            )
            if username in {"admin", "hardware_support", "software_support", "access_support", "network_support", "printer_support"}:
                user.profile.role = "admin" if username == "admin" else "technician"
                user.profile.save()

        self.client.force_login(users.objects.get(username="admin"))
        response = self.client.get(reverse("user_management"))

        self.assertEqual(
            list(response.context["users"].values_list("username", flat=True))
            if hasattr(response.context["users"], "values_list")
            else [user.username for user in response.context["users"]],
            expected_usernames,
        )
        self.assertEqual(
            dict(users.objects.filter(username__in=expected_usernames).values_list("username", "email")),
            emails,
        )


class TicketIssueTypeFormTests(TestCase):
    def setUp(self):
        self.hardware = Category.objects.create(name="Hardware")
        self.network = Category.objects.create(name="Network")

    def test_specific_issue_options_follow_category_and_printer_is_not_an_option(self):
        printer = Category.objects.create(name="Printer")
        form = TicketForm({"category": self.hardware.pk})
        issue_options = [value for value, _label in form.fields["issue_type"].choices if value]

        self.assertTrue(form.fields["issue_type"].required)
        self.assertEqual(form.fields["issue_type"].widget.input_type, "select")
        self.assertEqual(len(issue_options), 21)
        self.assertIn("Computer/Laptop not turning on", issue_options)
        self.assertNotIn("Wi-Fi not connecting", issue_options)
        self.assertEqual(
            form.fields["other_issue"].widget.attrs["placeholder"],
            "Type the issue you encountered...",
        )
        self.assertNotIn(printer, form.fields["category"].queryset)

        network_form = TicketForm({"category": self.network.pk})
        network_options = [value for value, _label in network_form.fields["issue_type"].choices if value]
        self.assertIn("Wi-Fi not connecting", network_options)
        self.assertNotIn("Computer/Laptop not turning on", network_options)

    def test_device_system_input_disables_browser_autocomplete(self):
        form = TicketForm()

        self.assertEqual(form.fields["device_system"].widget.attrs["autocomplete"], "off")

    def test_form_accepts_a_custom_issue_for_other(self):
        other = Category.objects.create(name="Other")
        form = TicketForm({
            "category": other.pk,
            "issue_type": TicketForm.OTHER_CUSTOM_ISSUE,
            "other_issue": "My custom support request",
            "priority": "medium",
            "title": "Other issue",
            "description": "Please investigate this custom concern.",
        })

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["issue_type"], "My custom support request")

    def test_other_category_includes_requested_choices_and_custom_option(self):
        other = Category.objects.create(name="Other")
        form = TicketForm({"category": other.pk})
        options = [value for value, _label in form.fields["issue_type"].choices if value]

        self.assertIn("Email problem", options)
        self.assertIn("Transaction problem", options)
        self.assertEqual(options[0], TicketForm.OTHER_CUSTOM_ISSUE)
        self.assertNotIn("Other technical issue", options)
        self.assertIsInstance(form.fields["other_issue"].widget, forms.Textarea)
        self.assertFalse(form.fields["other_issue"].required)

        missing_custom_text = TicketForm({
            "category": other.pk,
            "issue_type": TicketForm.OTHER_CUSTOM_ISSUE,
            "priority": "medium",
            "title": "Other issue",
            "description": "Please investigate this custom concern.",
        })
        self.assertFalse(missing_custom_text.is_valid())
        self.assertIn("other_issue", missing_custom_text.errors)

    def test_form_requires_a_specific_issue(self):
        form = TicketForm({
            "category": self.network.pk,
            "issue_type": "",
            "priority": "medium",
            "title": "Network issue",
            "description": "The computer cannot access the office network.",
        })

        self.assertFalse(form.is_valid())
        self.assertIn("issue_type", form.errors)


class TicketEditTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="employee",
            email="employee@example.com",
            password="password123",
        )
        self.user.profile.role = "employee"
        self.user.profile.save()
        self.category = Category.objects.create(name="Hardware")
        self.ticket = Ticket.objects.create(
            title="Keyboard not responding",
            description="Issue with keyboard input.",
            category=self.category,
            priority="medium",
            status="pending",
            submitted_by=self.user,
        )

    def test_employee_can_open_ticket_edit_page(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("ticket_edit", args=[self.ticket.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Edit Ticket")

    def test_employee_name_is_shown_in_ticket_lists(self):
        self.user.first_name = "Jamie"
        self.user.last_name = "Employee"
        self.user.save()
        self.client.force_login(self.user)

        self.assertContains(self.client.get(reverse("my_tickets")), "Jamie Employee")
        self.assertContains(self.client.get(reverse("dashboard")), "Jamie Employee")

    def test_employee_can_update_ticket(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("ticket_edit", args=[self.ticket.pk]),
            {
                "category": self.category.pk,
                "issue_type": "Computer/Laptop not turning on",
                "priority": "high",
                "title": "Keyboard still not responding",
                "description": "The wireless keyboard stopped working after startup.",
                "device_system": "Dell Latitude 5420",
                "location": "HQ Floor 2",
            },
        )
        self.ticket.refresh_from_db()
        self.assertRedirects(response, reverse("ticket_detail", args=[self.ticket.pk]))
        self.assertEqual(self.ticket.title, "Keyboard still not responding")
        self.assertEqual(self.ticket.priority, "high")

    def test_admin_can_update_ticket_management_fields(self):
        self.user.profile.role = "admin"
        self.user.profile.save()
        requester = get_user_model().objects.create_user(username="new-requester", password="password123")
        technician = get_user_model().objects.create_user(username="ticket-tech", password="password123")
        technician.profile.role = "technician"
        technician.profile.save()
        category = Category.objects.create(name="Software")
        self.client.force_login(self.user)

        edit_url = reverse("ticket_edit", args=[self.ticket.pk])
        page = self.client.get(edit_url)
        response = self.client.post(
            edit_url,
            {
                "title": "Updated ticket title",
                "submitted_by": requester.pk,
                "category": category.pk,
                "issue_type": "Software installation request",
                "priority": "critical",
                "status": "assigned",
                "assigned_to": technician.pk,
                "ticket_date": "2026-10-08T10:30",
                "description": "Updated description.",
                "device_system": "Office laptop",
                "location": "HQ",
                "attachment": "",
                "resolution": "",
            },
        )

        self.assertContains(page, 'name="submitted_by"')
        self.assertContains(page, 'name="status"')
        self.assertContains(page, 'name="assigned_to"')
        self.assertContains(page, 'name="ticket_date"')
        self.assertRedirects(response, reverse("ticket_detail", args=[self.ticket.pk]))
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.title, "Updated ticket title")
        self.assertEqual(self.ticket.submitted_by, requester)
        self.assertEqual(self.ticket.category, category)
        self.assertEqual(self.ticket.priority, "critical")
        self.assertEqual(self.ticket.status, "assigned")
        self.assertEqual(self.ticket.assigned_to, technician)
        self.assertEqual(timezone.localtime(self.ticket.created_at).strftime("%Y-%m-%dT%H:%M"), "2026-10-08T10:30")

    def test_requester_dropdown_displays_requested_full_names(self):
        User = get_user_model()
        User.objects.create_user(username="manager")
        User.objects.create_user(username="admin")
        User.objects.create_user(username="juan")
        User.objects.create_user(
            username="ALLEN JOHN DELA CRUZ CARDINEZ",
            first_name="ALLEN JOHN DELA CRUZ",
            last_name="CARDINEZ",
        )
        User.objects.create_user(
            username="DUDDY ALBERT BALMEO FONTANILLA",
            email="duddyalbert017@gmail.com",
            first_name="duddy",
            last_name="albert",
        )
        technician = User.objects.create_user(
            username="technician",
            first_name="Ryuin",
            last_name="Munoz",
        )
        technician.profile.role = "technician"
        technician.profile.save()
        call_command("seed_demo", specialists_only=True, verbosity=0)

        form = TicketManagementForm(instance=self.ticket)
        labels = [label for _, label in form.fields["submitted_by"].choices]

        self.assertEqual(labels[1:], [
            "ALLEN JOHN DELA CRUZ CARDINEZ",
            "DUDDY ALBERT BALMEO FONTANILLA",
            "PAUL ELINIEL FLORES SIBUL",
            "REDFORD PERALTA BISCARRA",
            "LANDER RABE RAGMAC",
        ])
        self.assertIn("DUDDY ALBERT BALMEO FONTANILLA", labels)
        self.assertIn("PAUL ELINIEL FLORES SIBUL", labels)
        self.assertIn("REDFORD PERALTA BISCARRA", labels)
        self.assertIn("LANDER RABE RAGMAC", labels)
        self.assertNotIn("Ryuin Munoz", labels)
        for specialist in [
            "Hardware Support Technician",
            "Software Support Specialist",
            "Printer Support Technician",
            "Network Support Technician",
            "IT Access Support Specialist",
        ]:
            self.assertNotIn(specialist, labels)
        for username in ["manager", "admin", "juan", "employee", "technician"]:
            self.assertNotIn(username, labels)

    def test_specialist_technicians_are_available_for_assignment(self):
        call_command("seed_demo", specialists_only=True, verbosity=0)
        form = TicketManagementForm(instance=self.ticket)
        labels = [label for _, label in form.fields["assigned_to"].choices]

        self.assertEqual(labels[1:], [
            "Hardware Support Technician",
            "Software Support Specialist",
            "IT Access Support Specialist",
            "Network Support Technician",
            "Printer Support Technician",
        ])
        self.assertNotIn("RYUIN MUNOZ", labels)

    def test_existing_ryuin_assignment_is_preserved_without_showing_name(self):
        technician = get_user_model().objects.create_user(
            username="technician",
            first_name="RYUIN",
            last_name="MUNOZ",
        )
        technician.profile.role = "technician"
        technician.profile.save()
        self.ticket.assigned_to = technician
        self.ticket.status = "assigned"
        self.ticket.save()

        form = TicketManagementForm(instance=self.ticket)
        labels = [label for _, label in form.fields["assigned_to"].choices]

        self.assertEqual(form["assigned_to"].value(), technician.pk)
        self.assertIn("Current assignee", labels)
        self.assertNotIn("RYUIN MUNOZ", labels)

    def test_employee_can_edit_after_ticket_is_assigned(self):
        technician = get_user_model().objects.create_user(username="assigned-tech", password="password123")
        technician.profile.role = "technician"
        technician.profile.save()
        self.ticket.assigned_to = technician
        self.ticket.status = "assigned"
        self.ticket.save()
        self.client.force_login(self.user)

        edit_url = reverse("ticket_edit", args=[self.ticket.pk])
        view_url = reverse("ticket_detail", args=[self.ticket.pk])
        response = self.client.get(edit_url)
        detail_response = self.client.get(reverse("ticket_detail", args=[self.ticket.pk]))
        list_response = self.client.get(reverse("my_tickets"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(detail_response, edit_url)
        row = list_response.content.decode().split("</tr>")[1]
        self.assertLess(row.index(view_url), row.index(edit_url))
        response = self.client.post(
            edit_url,
            {
                "category": self.category.pk,
                "issue_type": "Computer/Laptop not turning on",
                "priority": "high",
                "title": "Updated after assignment",
                "description": "Added details after the ticket was assigned.",
                "device_system": "Dell Latitude 5420",
                "location": "HQ Floor 2",
            },
        )

        self.assertRedirects(response, reverse("ticket_detail", args=[self.ticket.pk]))
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.title, "Updated after assignment")
        self.assertEqual(self.ticket.status, "assigned")
        self.assertEqual(self.ticket.assigned_to, technician)

    def test_employee_can_edit_own_in_progress_and_resolved_tickets(self):
        technician = get_user_model().objects.create_user(username="assigned-tech", password="password123")
        technician.profile.role = "technician"
        technician.profile.save()
        self.ticket.assigned_to = technician
        self.client.force_login(self.user)

        for status in ["in_progress", "resolved"]:
            self.ticket.status = status
            self.ticket.save()
            response = self.client.post(
                reverse("ticket_edit", args=[self.ticket.pk]),
                {
                    "category": self.category.pk,
                    "issue_type": "Computer/Laptop not turning on",
                    "priority": "high",
                    "title": f"Updated while {status}",
                    "description": "Added more detail about the issue.",
                    "device_system": "Dell Latitude 5420",
                    "location": "HQ Floor 2",
                },
            )
            self.assertRedirects(response, reverse("ticket_detail", args=[self.ticket.pk]))
            self.ticket.refresh_from_db()
            self.assertEqual(self.ticket.status, status)
            self.assertEqual(self.ticket.assigned_to, technician)
            self.assertEqual(self.ticket.priority, "high")

    def test_closed_ticket_shows_view_before_edit_and_remains_closed_after_edit(self):
        technician = get_user_model().objects.create_user(username="closed-tech", password="password123")
        technician.profile.role = "technician"
        technician.profile.save()
        self.ticket.assigned_to = technician
        self.ticket.status = "closed"
        self.ticket.resolution = "The keyboard was replaced."
        self.ticket.resolved_at = timezone.now()
        self.ticket.save()
        self.client.force_login(self.user)

        list_response = self.client.get(reverse("my_tickets"))
        view_link = reverse("ticket_detail", args=[self.ticket.pk])
        edit_link = reverse("ticket_edit", args=[self.ticket.pk])
        row = list_response.content.decode().split("</tr>")[1]
        edit_response = self.client.post(
            edit_link,
            {
                "category": self.category.pk,
                "issue_type": "Keyboard not working",
                "priority": "high",
                "title": "Keyboard replacement still disconnects",
                "description": "The replacement keyboard has intermittent connection loss.",
                "device_system": "Dell Latitude 5420",
                "location": "HQ Floor 2",
            },
        )

        self.assertLess(row.index(view_link), row.index(edit_link))
        self.assertRedirects(edit_response, reverse("ticket_detail", args=[self.ticket.pk]))
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, "closed")
        self.assertEqual(self.ticket.assigned_to, technician)
        self.assertEqual(self.ticket.resolution, "The keyboard was replaced.")

    def test_employee_can_acknowledge_pending_or_in_progress_status(self):
        self.client.force_login(self.user)

        for status in ["pending", "in_progress"]:
            self.ticket.status = status
            self.ticket.save()
            response = self.client.post(
                reverse("ticket_employee_action", args=[self.ticket.pk]),
                {"action": "acknowledge"},
            )
            self.ticket.refresh_from_db()
            self.assertRedirects(response, reverse("ticket_detail", args=[self.ticket.pk]))
            self.assertEqual(self.ticket.status, status)
            self.assertIn("acknowledged", self.ticket.updates.latest("created_at").message)

    def test_employee_can_accept_resolved_ticket(self):
        self.ticket.status = "resolved"
        self.ticket.resolution = "Replaced the faulty keyboard."
        self.ticket.save()
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("ticket_employee_action", args=[self.ticket.pk]),
            {"action": "accept"},
        )

        self.ticket.refresh_from_db()
        self.assertRedirects(response, reverse("ticket_detail", args=[self.ticket.pk]))
        self.assertEqual(self.ticket.status, "closed")
        self.assertIn("accepted the resolution", self.ticket.updates.latest("created_at").message)

    def test_employee_cannot_submit_feedback_before_resolution(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("ticket_feedback", args=[self.ticket.pk]),
            {"rating": 5, "comment": "Helpful support."},
        )

        self.assertRedirects(response, reverse("ticket_detail", args=[self.ticket.pk]))
        self.assertFalse(Feedback.objects.filter(ticket=self.ticket).exists())

    def test_employee_can_submit_feedback_after_resolution(self):
        self.ticket.status = "resolved"
        self.ticket.resolution = "Replaced the faulty keyboard."
        self.ticket.save()
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("ticket_feedback", args=[self.ticket.pk]),
            {"rating": 5, "comment": "Helpful support."},
        )

        self.assertRedirects(response, reverse("ticket_detail", args=[self.ticket.pk]))
        self.assertEqual(Feedback.objects.get(ticket=self.ticket).rating, 5)

    def test_employee_can_request_reopen_with_reason(self):
        self.ticket.status = "resolved"
        self.ticket.resolution = "Replaced the faulty keyboard."
        self.ticket.save()
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("ticket_employee_action", args=[self.ticket.pk]),
            {"action": "reopen", "reason": "The replacement keyboard still disconnects."},
        )

        self.ticket.refresh_from_db()
        self.assertRedirects(response, reverse("ticket_detail", args=[self.ticket.pk]))
        self.assertEqual(self.ticket.status, "in_progress")
        self.assertEqual(self.ticket.resolution, "")
        self.assertIsNone(self.ticket.resolved_at)
        self.assertIn("The replacement keyboard still disconnects.", self.ticket.updates.latest("created_at").message)

    def test_employee_cannot_act_on_another_employees_ticket(self):
        another_employee = get_user_model().objects.create_user(username="another-employee", password="password123")
        self.ticket.status = "resolved"
        self.ticket.save()
        self.client.force_login(another_employee)

        response = self.client.post(
            reverse("ticket_employee_action", args=[self.ticket.pk]),
            {"action": "accept"},
        )

        self.assertRedirects(response, reverse("my_tickets"))
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, "resolved")

    def test_knowledge_base_has_clickable_topics_and_hidden_slide_examples(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("knowledge_base"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "article-trigger", count=4)
        self.assertContains(response, "Password Reset")
        self.assertContains(response, "Wi-Fi Connection")
        self.assertContains(response, "Printer Troubleshooting")
        self.assertContains(response, "Software Installation")
        self.assertContains(response, "guideDialog")
        self.assertContains(response, "Suggested response")
        self.assertContains(response, "Example steps")
        self.assertContains(response, "hidden")

    def test_profile_edit_updates_name_shown_in_header(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("profile_edit"),
            {
                "first_name": "Allen John",
                "last_name": "Dela Cruz Cardinez",
                "email": "allen@example.com",
                "department": "IT Support Services",
                "user_identifier": "EMP-1001",
            },
        )

        self.assertRedirects(response, reverse("profile"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.get_full_name(), "Allen John Dela Cruz Cardinez")
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.user_identifier, "EMP-1001")
        profile_response = self.client.get(reverse("profile"))
        self.assertContains(profile_response, "Allen John Dela Cruz Cardinez")
        self.assertContains(profile_response, "EMP-1001")
        self.assertContains(profile_response, "User ID")
        self.assertContains(profile_response, "User")
        self.assertContains(profile_response, 'href="/profile/edit/"')

    def test_submitting_ticket_creates_submitter_notification(self):
        other_category = Category.objects.create(name="Other")
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("submit_ticket"),
            {
                "category": other_category.pk,
                "issue_type": TicketForm.OTHER_CUSTOM_ISSUE,
                "other_issue": "A custom issue that is not on a predefined list",
                "priority": "medium",
                "title": "Custom support issue",
                "description": "Please investigate this typed issue.",
                "device_system": "Laptop",
                "location": "Office",
            },
        )

        self.assertRedirects(response, reverse("my_tickets"))
        notification = Notification.objects.get(recipient=self.user)
        self.assertIn("awaiting IT review", notification.message)
        self.assertEqual(
            Ticket.objects.get(submitted_by=self.user, title="Custom support issue").issue_type,
            "A custom issue that is not on a predefined list",
        )
        self.assertContains(self.client.get(reverse("my_tickets")), "A custom issue that is not on a predefined list")

    def test_submitting_ticket_notifies_admin_level_accounts(self):
        users = get_user_model()
        admin = users.objects.create_user(username="admin", password="password123")
        admin.profile.role = "admin"
        admin.profile.save(update_fields=["role"])
        manager = users.objects.create_user(username="manager", password="password123")
        manager.profile.role = "manager"
        manager.profile.save(update_fields=["role"])
        superuser = users.objects.create_superuser(
            username="superadmin",
            email="superadmin@example.com",
            password="password123",
        )
        superuser.profile.role = "user"
        superuser.profile.save(update_fields=["role"])
        network_category = Category.objects.create(name="Network")
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("submit_ticket"),
            {
                "category": network_category.pk,
                "issue_type": "Wi-Fi not connecting",
                "priority": "medium",
                "title": "Cannot connect to office Wi-Fi",
                "description": "The device cannot join the company network.",
                "device_system": "Laptop",
                "location": "Office",
            },
        )

        ticket = Ticket.objects.get(submitted_by=self.user, title="Cannot connect to office Wi-Fi")
        notified_usernames = set(
            Notification.objects.filter(ticket=ticket).values_list("recipient__username", flat=True)
        )
        self.assertRedirects(response, reverse("my_tickets"))
        self.assertTrue({"employee", "admin", "manager", "superadmin"}.issubset(notified_usernames))

        self.client.force_login(admin)
        admin_ticket_response = self.client.get(reverse("all_tickets"))
        self.assertContains(admin_ticket_response, "Wi-Fi not connecting")
        feed_response = self.client.get(reverse("notifications_feed"))
        feed_data = feed_response.json()
        admin_notification = Notification.objects.get(recipient=admin, ticket=ticket)
        self.assertEqual(feed_response.status_code, 200)
        self.assertEqual(feed_data["unread_count"], 1)
        self.assertEqual(feed_data["notifications"][0]["message"], "New IT Support Ticket")
        self.assertEqual(feed_data["notifications"][0]["ticket_title"], ticket.title)
        self.assertEqual(feed_data["notifications"][0]["ticket_number"], ticket.ticket_number)
        self.assertEqual(feed_data["notifications"][0]["submitter"], self.user.username)
        self.assertEqual(feed_data["notifications"][0]["url"], reverse("notification_open", args=[admin_notification.pk]))

        open_response = self.client.get(feed_data["notifications"][0]["url"])
        self.assertRedirects(open_response, reverse("ticket_detail", args=[ticket.pk]))
        admin_notification.refresh_from_db()
        self.assertIsNotNone(admin_notification.read_at)

        self.client.force_login(manager)
        mark_read_response = self.client.post(
            reverse("notifications_mark_read"),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(mark_read_response.json(), {"unread_count": 0})

        other_user = users.objects.create_user(username="other-user", password="password123")
        self.client.force_login(other_user)
        self.assertEqual(self.client.get(reverse("notifications_feed")).json()["unread_count"], 0)

    def test_ticket_update_creates_notification_and_mark_read_works(self):
        technician = get_user_model().objects.create_user(
            username="technician",
            email="tech@example.com",
            password="password123",
        )
        technician.profile.role = "technician"
        technician.profile.save()
        self.ticket.assigned_to = technician
        self.ticket.save()

        self.client.force_login(technician)
        self.client.post(
            reverse("ticket_update", args=[self.ticket.pk]),
            {"message": "Checking network connectivity."},
        )

        notification = Notification.objects.get(recipient=self.user, ticket=self.ticket)
        self.client.force_login(self.user)
        page = self.client.get(reverse("profile"))
        self.assertContains(page, notification.message)
        self.assertEqual(page.context["unread_notification_count"], 1)

        response = self.client.post(
            reverse("notifications_mark_read"),
            {"next": reverse("profile")},
        )
        self.assertRedirects(response, reverse("profile"))
        notification.refresh_from_db()
        self.assertIsNotNone(notification.read_at)


class TicketActionTests(TestCase):
    def setUp(self):
        users = get_user_model()
        self.employee = users.objects.create_user(username="requester", password="password123")
        self.manager = users.objects.create_user(username="manager", password="password123")
        self.manager.profile.role = "manager"
        self.manager.profile.save()
        self.technician = users.objects.create_user(username="technician", password="password123")
        self.technician.profile.role = "technician"
        self.technician.profile.save()
        self.other_technician = users.objects.create_user(username="other-tech", password="password123")
        self.other_technician.profile.role = "technician"
        self.other_technician.profile.save()
        self.category = Category.objects.create(name="Hardware")
        self.ticket = Ticket.objects.create(
            title="Laptop will not start",
            description="The laptop does not start.",
            category=self.category,
            submitted_by=self.employee,
        )

    def test_assignment_rejects_non_technician_users(self):
        self.client.force_login(self.manager)

        response = self.client.post(
            reverse("assign_ticket", args=[self.ticket.pk]),
            {"assigned_to": self.employee.pk, "status": "assigned", "resolution": ""},
        )

        self.assertRedirects(response, reverse("ticket_detail", args=[self.ticket.pk]))
        self.ticket.refresh_from_db()
        self.assertIsNone(self.ticket.assigned_to)
        self.assertEqual(self.ticket.status, "pending")
        self.assertFalse(TicketUpdate.objects.filter(ticket=self.ticket).exists())

    def test_ticket_cannot_be_resolved_without_resolution_notes(self):
        self.client.force_login(self.manager)

        self.client.post(
            reverse("assign_ticket", args=[self.ticket.pk]),
            {"assigned_to": "", "status": "resolved", "resolution": "   "},
        )

        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, "pending")
        self.assertIsNone(self.ticket.resolved_at)
        self.assertFalse(TicketUpdate.objects.filter(ticket=self.ticket).exists())

    def test_manager_assignment_and_resolution_are_recorded(self):
        self.client.force_login(self.manager)
        action_url = reverse("assign_ticket", args=[self.ticket.pk])

        self.client.post(action_url, {"assigned_to": self.technician.pk, "status": "pending", "resolution": ""})
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.assigned_to, self.technician)
        self.assertEqual(self.ticket.status, "assigned")

        self.client.post(
            action_url,
            {"assigned_to": self.technician.pk, "status": "resolved", "resolution": "Replaced the failed battery."},
        )
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, "resolved")
        self.assertIsNotNone(self.ticket.resolved_at)
        self.assertEqual(self.ticket.resolution, "Replaced the failed battery.")
        self.assertIn("Resolution: Replaced the failed battery.", self.ticket.updates.latest("created_at").message)

    def test_technician_can_update_owned_ticket_without_reassigning(self):
        self.ticket.assigned_to = self.technician
        self.ticket.status = "assigned"
        self.ticket.save()
        self.client.force_login(self.technician)

        self.client.post(
            reverse("assign_ticket", args=[self.ticket.pk]),
            {"assigned_to": self.other_technician.pk, "status": "in_progress", "resolution": ""},
        )

        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.assigned_to, self.technician)
        self.assertEqual(self.ticket.status, "in_progress")

    def test_technician_dashboard_only_counts_assigned_tickets(self):
        Ticket.objects.create(
            title="Other technician issue",
            description="A separate issue.",
            category=self.category,
            assigned_to=self.other_technician,
            submitted_by=self.employee,
        )
        self.ticket.assigned_to = self.technician
        self.ticket.save()
        self.client.force_login(self.technician)

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.context["stats"]["total"], 1)
        self.assertEqual(list(response.context["recent"]), [self.ticket])


class MyTicketFilterTests(TestCase):
    def setUp(self):
        self.employee = get_user_model().objects.create_user(username="my-employee", password="password123")
        self.category = Category.objects.create(name="Network")
        self.tickets = {}
        for status in ["pending", "assigned", "in_progress", "resolved", "closed"]:
            self.tickets[status] = Ticket.objects.create(
                title=f"{status.replace('_', ' ').title()} sample",
                description="Sample employee ticket.",
                category=self.category,
                status=status,
                submitted_by=self.employee,
            )
        self.client.force_login(self.employee)

    def test_status_selection_returns_only_matching_employee_tickets(self):
        for status in ["pending", "assigned", "in_progress"]:
            with self.subTest(status=status):
                response = self.client.get(reverse("my_tickets"), {"status": status})
                self.assertEqual(list(response.context["tickets"]), [self.tickets[status]])
                self.assertEqual(response.context["status_filter"], status)

    def test_resolved_and_closed_selection_returns_only_completed_tickets(self):
        response = self.client.get(reverse("my_tickets"), {"status": "completed"})

        self.assertEqual(set(response.context["tickets"]), {self.tickets["resolved"], self.tickets["closed"]})

    def test_all_statuses_and_search_are_combined(self):
        all_response = self.client.get(reverse("my_tickets"), {"status": "all"})
        search_response = self.client.get(reverse("my_tickets"), {"status": "in_progress", "q": "In Progress sample"})
        empty_response = self.client.get(reverse("my_tickets"), {"status": "pending", "q": "not found"})

        self.assertEqual(all_response.context["tickets"].count(), 5)
        self.assertEqual(list(search_response.context["tickets"]), [self.tickets["in_progress"]])
        self.assertEqual(empty_response.context["tickets"].count(), 0)
        self.assertContains(all_response, 'name="status"')


class ReportsTests(TestCase):
    def setUp(self):
        users = get_user_model()
        self.manager = users.objects.create_user(username="manager", password="password123")
        self.manager.profile.role = "manager"
        self.manager.profile.save()
        self.employee = users.objects.create_user(username="employee", password="password123")
        self.technician = users.objects.create_user(username="technician", password="password123")
        self.technician.profile.role = "technician"
        self.technician.profile.save()
        self.category = Category.objects.create(name="Network")
        self.active_ticket = Ticket.objects.create(
            title="Wi-Fi unavailable",
            description="Cannot connect to Wi-Fi.",
            category=self.category,
            status="in_progress",
            assigned_to=self.technician,
            submitted_by=self.employee,
        )
        self.unassigned_ticket = Ticket.objects.create(
            title="VPN access needed",
            description="VPN access is unavailable.",
            category=self.category,
            status="pending",
            submitted_by=self.employee,
        )
        Ticket.objects.create(
            title="Email restored",
            description="Email access has been restored.",
            category=self.category,
            status="resolved",
            submitted_by=self.employee,
        )
        Ticket.objects.create(
            title="Printer restored",
            description="Printer access has been restored.",
            category=self.category,
            status="closed",
            submitted_by=self.employee,
        )
        self.client.force_login(self.manager)

    def test_reports_show_correct_counts_and_actionable_links(self):
        response = self.client.get(reverse("reports"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total"], 4)
        self.assertEqual(response.context["active_total"], 2)
        self.assertEqual(response.context["unassigned_total"], 1)
        self.assertEqual(response.context["resolved_total"], 2)
        self.assertContains(response, f"?category={self.category.pk}")
        self.assertContains(response, f"?assigned_to={self.technician.pk}")
        self.assertContains(response, "priorityChart")
        self.assertContains(response, "statusChart")

    def test_reports_hide_only_ryuin_from_technician_workload(self):
        ryuin = get_user_model().objects.create_user(
            username="ryuin",
            first_name="RYUIN",
            last_name="MUNOZ",
        )
        ryuin.profile.role = "technician"
        ryuin.profile.save()

        response = self.client.get(reverse("reports"))
        workload = response.context["technicians"]

        self.assertContains(response, self.technician.username)
        self.assertNotContains(response, "RYUIN MUNOZ")
        self.assertNotIn(ryuin, workload)

    def test_report_drilldown_filters_active_tickets_and_assignee(self):
        response = self.client.get(reverse("all_tickets"), {"status": "active", "assigned_to": self.technician.pk})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["tickets"]), [self.active_ticket])
        self.assertEqual(list(response.context["form"].fields["assigned_to"].queryset), [self.technician])
        self.assertContains(response, 'id="ticketFilters"')

    def test_ticket_filters_return_only_the_selected_category_and_priority(self):
        hardware = Category.objects.create(name="Hardware")
        unrelated_ticket = Ticket.objects.create(
            title="Laptop repair",
            description="Laptop needs repair.",
            category=hardware,
            priority="critical",
            submitted_by=self.employee,
        )

        category_response = self.client.get(reverse("all_tickets"), {"category": self.category.pk})
        priority_response = self.client.get(reverse("all_tickets"), {"priority": "critical"})
        technician_response = self.client.get(reverse("all_tickets"), {"assigned_to": self.technician.pk})

        self.assertEqual(set(category_response.context["tickets"].values_list("pk", flat=True)), {
            self.active_ticket.pk,
            self.unassigned_ticket.pk,
            *Ticket.objects.filter(submitted_by=self.employee, status__in=["resolved", "closed"]).values_list("pk", flat=True),
        })
        self.assertEqual(list(priority_response.context["tickets"]), [unrelated_ticket])
        self.assertEqual(list(technician_response.context["tickets"]), [self.active_ticket])

    def test_unassigned_and_resolved_drilldowns_match_report_tiles(self):
        unassigned = self.client.get(reverse("all_tickets"), {"status": "active", "assignment": "unassigned"})
        resolved = self.client.get(reverse("all_tickets"), {"status": "resolved"})

        self.assertEqual(list(unassigned.context["tickets"]), [self.unassigned_ticket])
        self.assertEqual(set(resolved.context["tickets"].values_list("status", flat=True)), {"resolved", "closed"})

    def test_admin_dashboard_uses_real_trend_and_clickable_ticket_filters(self):
        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(sum(day["total"] for day in response.context["trend"]), 4)
        self.assertEqual(response.context["trend"][-1]["date"], timezone.localdate().isoformat())
        self.assertContains(response, "?status=pending")
        self.assertContains(response, "?status=in_progress")
        self.assertContains(response, "categoryData")
        self.assertContains(response, "trendData")
        self.assertContains(response, reverse("ticket_detail", args=[self.active_ticket.pk]))

    def test_ticket_queue_filters_by_chart_trend_date(self):
        today = timezone.localdate()
        response = self.client.get(reverse("all_tickets"), {"created_on": today.isoformat()})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.context["tickets"].values_list("pk", flat=True)), {
            self.active_ticket.pk,
            self.unassigned_ticket.pk,
            *Ticket.objects.filter(submitted_by=self.employee, status__in=["resolved", "closed"]).values_list("pk", flat=True),
        })
