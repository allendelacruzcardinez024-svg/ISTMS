from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from datetime import timedelta
from django.db.models import Avg, Count, DurationField, ExpressionWrapper, F, OuterRef, Q, Subquery, Value
from django.db.models.functions import Concat, TruncDate
from django.views.decorators.http import require_POST
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from .forms import TicketForm, TicketManagementForm, TicketUpdateForm, FeedbackForm, TicketFilterForm, ProfileUpdateForm, ManagedUserForm, RequesterChoiceField
from .models import Profile, Category, Ticket, TicketUpdate, Feedback, Notification

def role(request):
    stored_role = getattr(getattr(request.user, "profile", None), "role", "user")
    return "admin" if stored_role in {"admin", "manager"} or request.user.is_superuser else "user"

def notify_users(ticket, users, message, actor=None):
    recipients = {user.pk: user for user in users if user is not None}
    if actor:
        recipients.pop(actor.pk, None)
    Notification.objects.bulk_create([
        Notification(recipient=user, ticket=ticket, message=message)
        for user in recipients.values()
    ])

def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    selected_role = request.POST.get("account_type", request.GET.get("role", "user"))
    if selected_role not in {"user", "admin"}:
        selected_role = "user"
    if request.method == "POST":
        identifier = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        candidates = []
        seen_user_ids = set()

        def add_candidates(users):
            for candidate in users:
                if candidate.pk not in seen_user_ids:
                    candidates.append(candidate)
                    seen_user_ids.add(candidate.pk)

        add_candidates(User.objects.filter(username=identifier))
        add_candidates(User.objects.filter(
            Q(username__iexact=identifier) | Q(email__iexact=identifier)
        ))
        add_candidates(
            User.objects.annotate(
                login_full_name=Concat("first_name", Value(" "), "last_name")
            ).filter(login_full_name__iexact=identifier)
        )
        display_name_usernames = [
            username
            for username, display_name in RequesterChoiceField.display_names.items()
            if display_name.casefold() == identifier.casefold()
        ]
        if display_name_usernames:
            add_candidates(User.objects.filter(username__in=display_name_usernames))

        user = None
        for candidate in candidates:
            user = authenticate(request, username=candidate.username, password=password)
            if user:
                break
        if user is None and not candidates:
            user = authenticate(request, username=identifier, password=password)
        is_admin_account = bool(user and (getattr(getattr(user, "profile", None), "role", "user") in {"admin", "manager"} or user.is_superuser))
        if user and ((selected_role == "admin" and is_admin_account) or (selected_role == "user" and not is_admin_account)):
            login(request, user)
            request.session.set_expiry(60 * 60 * 24 * 14 if request.POST.get("remember_me") else 0)
            messages.success(request, "Welcome back to ISTMS.")
            return redirect("dashboard")
        if user:
            messages.error(request, "This account does not have access to the selected sign in. Choose the matching account type.")
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, "tickets/index.html", {"selected_role": selected_role})

def logout_view(request):
    logout(request)
    return redirect("login")


def register(request):
    is_admin_action = request.user.is_authenticated and role(request) == "admin"
    if request.user.is_authenticated and not is_admin_action:
        return redirect("dashboard")
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        password2 = request.POST.get("password2", "")
        if not (username and password and password2):
            messages.error(request, "Please enter a username and complete both password fields.")
            return redirect("register")
        if password != password2:
            messages.error(request, "Passwords do not match.")
            return redirect("register")
        if User.objects.filter(username__iexact=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("register")
        user = User.objects.create_user(username=username, email=email, password=password)
        if is_admin_action:
            if request.POST.get("role") == "admin":
                user.profile.role = "admin"
                user.profile.save(update_fields=["role"])
                user.is_staff = True
                user.save(update_fields=["is_staff"])
            messages.success(request, f"Account for {username} created successfully.")
            return redirect("user_management")
        login(request, user)
        messages.success(request, "Account created successfully.")
        return redirect("dashboard")
    return render(request, "tickets/register.html", {"is_admin_action": is_admin_action})


@login_required
def dashboard(request):
    r = role(request)
    if r == "user":
        qs = Ticket.objects.filter(submitted_by=request.user)
        stats = {
            "total": qs.count(),
            "pending": qs.filter(status="pending").count(),
            "progress": qs.filter(status="in_progress").count(),
            "resolved": qs.filter(status__in=["resolved", "closed"]).count(),
        }
        recent = qs[:5]
        template = "tickets/dashboard_employee.html"
    else:
        qs = Ticket.objects.all()
        today = timezone.localdate()
        trend_days = [today - timedelta(days=offset) for offset in range(6, -1, -1)]
        daily_totals = {
            item["day"]: item["total"]
            for item in qs.filter(created_at__date__range=(trend_days[0], today))
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(total=Count("id"))
        }
        trend = [
            {"date": day.isoformat(), "label": day.strftime("%b %d"), "total": daily_totals.get(day, 0)}
            for day in trend_days
        ]
        stats = {
            "total": qs.count(),
            "pending": qs.filter(status="pending").count(),
            "progress": qs.filter(status="in_progress").count(),
            "resolved": qs.filter(status__in=["resolved", "closed"]).count(),
            "overdue": qs.filter(status__in=["pending", "assigned", "in_progress"]).count(),
        }
        recent = qs.select_related("submitted_by", "assigned_to", "category")[:6]
        category_stats = list(Category.objects.annotate(total=Count("ticket")).values("id", "name", "total"))
        template = "tickets/dashboard_admin.html"
        return render(request, template, {
            "stats": stats,
            "recent": recent,
            "category_stats": category_stats,
            "trend": trend,
            "role": r,
        })
    return render(request, template, {"stats": stats, "recent": recent, "role": r})

@login_required
def submit_ticket(request):
    if request.method == "POST":
        form = TicketForm(request.POST, request.FILES)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.submitted_by = request.user
            ticket.save()
            TicketUpdate.objects.create(ticket=ticket, author=request.user, message="Ticket submitted by employee.")
            Notification.objects.create(
                recipient=request.user,
                ticket=ticket,
                message=f"Your ticket {ticket.ticket_number} was submitted and is awaiting IT review.",
            )
            staff = User.objects.filter(
                Q(profile__role__in=["admin", "manager"]) | Q(is_superuser=True)
            )
            notify_users(ticket, staff, "New IT Support Ticket", request.user)
            messages.success(request, f"Ticket {ticket.ticket_number} was submitted successfully.")
            return redirect("my_tickets")
    else:
        form = TicketForm()
    return render(request, "tickets/submit_ticket.html", {"form": form})

@login_required
def my_tickets(request):
    tickets = Ticket.objects.filter(submitted_by=request.user).select_related("category", "submitted_by", "assigned_to")
    status_filter = request.GET.get("status", "all")
    valid_statuses = {value for value, _label in Ticket.STATUSES}
    if status_filter not in valid_statuses | {"all", "completed"}:
        status_filter = "all"
    search_query = request.GET.get("q", "").strip()

    if status_filter == "completed":
        tickets = tickets.filter(status__in=["resolved", "closed"])
    elif status_filter != "all":
        tickets = tickets.filter(status=status_filter)
    if search_query:
        tickets = tickets.filter(Q(ticket_number__icontains=search_query) | Q(title__icontains=search_query))

    return render(request, "tickets/my_tickets.html", {
        "tickets": tickets,
        "status_filter": status_filter,
        "search_query": search_query,
    })

@login_required
def all_tickets(request):
    current_role = role(request)
    if current_role == "user":
        return redirect("my_tickets")
    tickets = Ticket.objects.select_related("submitted_by", "assigned_to", "category").all()
    form = TicketFilterForm(request.GET or None)
    if form.is_valid():
        q = form.cleaned_data.get("q")
        if q:
            tickets = tickets.filter(Q(ticket_number__icontains=q) | Q(title__icontains=q))
        if form.cleaned_data.get("category"):
            tickets = tickets.filter(category=form.cleaned_data["category"])
        if form.cleaned_data.get("priority"):
            tickets = tickets.filter(priority=form.cleaned_data["priority"])
        status = form.cleaned_data.get("status")
        if status == "active":
            tickets = tickets.filter(status__in=["pending", "assigned", "in_progress"])
        elif status == "resolved":
            tickets = tickets.filter(status__in=["resolved", "closed"])
        elif status:
            tickets = tickets.filter(status=status)
        if form.cleaned_data.get("assigned_to"):
            tickets = tickets.filter(assigned_to=form.cleaned_data["assigned_to"])
        if form.cleaned_data.get("assignment") == "unassigned":
            tickets = tickets.filter(assigned_to__isnull=True)
        if form.cleaned_data.get("created_on"):
            tickets = tickets.filter(created_at__date=form.cleaned_data["created_on"])
    return render(request, "tickets/ticket_list.html", {"tickets": tickets, "form": form})

@login_required
def ticket_detail(request, pk):
    ticket = get_object_or_404(Ticket.objects.select_related("category", "submitted_by", "assigned_to"), pk=pk)
    r = role(request)
    if r == "user" and ticket.submitted_by != request.user:
        return redirect("my_tickets")
    technicians = User.objects.filter(profile__role="user", is_active=True).order_by("first_name", "username")
    return render(request, "tickets/ticket_detail.html", {
        "ticket": ticket,
        "updates": ticket.updates.select_related("author"),
        "update_form": TicketUpdateForm(),
        "feedback_form": FeedbackForm(),
        "technicians": technicians,
        "role": r,
    })

@login_required
def edit_ticket(request, pk):
    ticket = get_object_or_404(Ticket.objects.select_related("category", "submitted_by"), pk=pk)
    r = role(request)
    management_fields = r == "admin"
    form_class = TicketManagementForm if management_fields else TicketForm
    if r == "user" and ticket.submitted_by != request.user:
        return redirect("my_tickets")
    if r == "user" and ticket.status not in ["pending", "assigned", "in_progress", "resolved", "closed"]:
        messages.error(request, "You can edit your ticket while it is Pending, Assigned, In Progress, Resolved, or Closed.")
        return redirect("ticket_detail", pk=ticket.pk)

    if request.method == "POST":
        form = form_class(request.POST, request.FILES, instance=ticket)
        if form.is_valid():
            previous_status = ticket.status
            ticket = form.save(commit=False)
            if management_fields:
                if ticket.assigned_to_id and ticket.status == "pending":
                    ticket.status = "assigned"
                elif ticket.assigned_to_id is None and ticket.status == "assigned":
                    ticket.status = "pending"
                if ticket.status in ["resolved", "closed"]:
                    if previous_status not in ["resolved", "closed"] or ticket.resolved_at is None:
                        ticket.resolved_at = timezone.now()
                elif previous_status in ["resolved", "closed"]:
                    ticket.resolved_at = None
                    ticket.resolution = ""
            ticket.save()
            form.save_m2m()
            TicketUpdate.objects.create(
                ticket=ticket,
                author=request.user,
                message=f"Ticket details updated by {request.user.get_full_name() or request.user.username}.",
            )
            if r == "user":
                staff = User.objects.filter(profile__role="admin")
                notify_users(ticket, staff, f"Ticket {ticket.ticket_number} details were updated.", request.user)
            messages.success(request, f"Ticket {ticket.ticket_number} was updated successfully.")
            return redirect("ticket_detail", pk=ticket.pk)
    else:
        form = form_class(instance=ticket)

    return render(request, "tickets/ticket_edit.html", {
        "form": form,
        "ticket": ticket,
        "role": r,
        "management_fields": management_fields,
    })

@login_required
@require_POST
def ticket_update(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    current_role = role(request)
    if current_role == "user" and ticket.submitted_by_id != request.user.pk:
        return redirect("my_tickets")
    form = TicketUpdateForm(request.POST)
    if form.is_valid():
        update = form.save(commit=False)
        update.ticket = ticket
        update.author = request.user
        update.save()
        notify_users(
            ticket,
            [ticket.submitted_by, ticket.assigned_to],
            f"{ticket.ticket_number} received a new update from {request.user.get_full_name() or request.user.username}.",
            request.user,
        )
        messages.success(request, "Ticket update added.")
    return redirect("ticket_detail", pk=pk)

@login_required
@require_POST
def ticket_employee_action(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    if role(request) != "user" or ticket.submitted_by_id != request.user.pk:
        return redirect("my_tickets")

    action = request.POST.get("action")
    if action == "acknowledge":
        if ticket.status not in ["pending", "in_progress"]:
            messages.error(request, "Only Pending or In Progress tickets can be acknowledged.")
            return redirect("ticket_detail", pk=pk)
        update_message = f"Requester acknowledged the {ticket.get_status_display()} status."
        messages.success(request, "Ticket status acknowledged.")
    elif action == "accept":
        if ticket.status != "resolved":
            messages.error(request, "Only a Resolved ticket can be accepted.")
            return redirect("ticket_detail", pk=pk)
        ticket.status = "closed"
        ticket.save(update_fields=["status", "updated_at"])
        update_message = "Requester accepted the resolution and closed the ticket."
        messages.success(request, "Resolution accepted. Ticket closed.")
    elif action == "reopen":
        if ticket.status != "resolved":
            messages.error(request, "Only a Resolved ticket can be reopened.")
            return redirect("ticket_detail", pk=pk)
        reason = request.POST.get("reason", "").strip()
        if not reason:
            messages.error(request, "Add a reason so IT knows why the issue needs more work.")
            return redirect("ticket_detail", pk=pk)
        previous_resolution = ticket.resolution
        ticket.status = "in_progress"
        ticket.resolved_at = None
        ticket.resolution = ""
        ticket.save(update_fields=["status", "resolved_at", "resolution", "updated_at"])
        update_message = f"Requester asked to reopen the ticket. Reason: {reason}"
        if previous_resolution:
            update_message += f" Previous resolution: {previous_resolution}"
        messages.success(request, "Ticket reopened. IT support has been notified.")
    else:
        messages.error(request, "Choose a valid ticket action.")
        return redirect("ticket_detail", pk=pk)

    TicketUpdate.objects.create(ticket=ticket, author=request.user, message=update_message)
    notify_users(
        ticket,
        [ticket.assigned_to],
        f"{ticket.ticket_number}: {update_message}",
        request.user,
    )
    return redirect("ticket_detail", pk=pk)

@login_required
@require_POST
def assign_ticket(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    current_role = role(request)
    if current_role != "admin":
        return redirect("ticket_detail", pk=pk)

    next_status = request.POST.get("status", ticket.status)
    if next_status not in dict(Ticket.STATUSES):
        messages.error(request, "Choose a valid ticket status.")
        return redirect("ticket_detail", pk=pk)

    resolution = request.POST.get("resolution", ticket.resolution).strip()
    if next_status in ["resolved", "closed"] and not resolution:
        messages.error(request, "Add resolution notes before resolving or closing this ticket.")
        return redirect("ticket_detail", pk=pk)

    previous_status = ticket.status
    previous_assignee_id = ticket.assigned_to_id
    if current_role == "admin":
        user_id = request.POST.get("assigned_to", "").strip()
        if user_id:
            assignee = User.objects.filter(pk=user_id, profile__role="user", is_active=True).first()
            if assignee is None:
                messages.error(request, "Choose an active User account for ticket assignment.")
                return redirect("ticket_detail", pk=pk)
            ticket.assigned_to = assignee
        else:
            ticket.assigned_to = None

    if ticket.assigned_to_id and ticket.status == "pending" and next_status == "pending":
        next_status = "assigned"
    elif ticket.assigned_to_id is None and next_status == "assigned":
        next_status = "pending"

    ticket.status = next_status
    ticket.resolution = resolution
    if next_status in ["resolved", "closed"]:
        if previous_status not in ["resolved", "closed"] or ticket.resolved_at is None:
            ticket.resolved_at = timezone.now()
    elif previous_status in ["resolved", "closed"]:
        ticket.resolved_at = None
        ticket.resolution = ""
    ticket.save()

    assignee_name = ticket.assigned_to.get_full_name() or ticket.assigned_to.username if ticket.assigned_to else "unassigned"
    update_message = (
        f"Ticket changed from {dict(Ticket.STATUSES)[previous_status]} to {ticket.get_status_display()} "
        f"and assigned to {assignee_name}."
    )
    if ticket.resolution and ticket.status in ["resolved", "closed"]:
        update_message += f" Resolution: {ticket.resolution}"
    TicketUpdate.objects.create(ticket=ticket, author=request.user, message=update_message)
    notify_users(
        ticket,
        [ticket.submitted_by, ticket.assigned_to],
        f"{ticket.ticket_number} is {ticket.get_status_display().lower()} and assigned to {assignee_name}.",
        request.user,
    )
    if previous_assignee_id != ticket.assigned_to_id or previous_status != ticket.status:
        messages.success(request, "Ticket assignment and status were updated.")
    else:
        messages.success(request, "Ticket resolution notes were updated.")
    return redirect("ticket_detail", pk=pk)

@login_required
def ticket_feedback(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    if ticket.submitted_by != request.user or ticket.status not in ["resolved", "closed"]:
        return redirect("ticket_detail", pk=pk)
    if request.method == "POST":
        form = FeedbackForm(request.POST)
        if form.is_valid():
            Feedback.objects.update_or_create(
                ticket=ticket,
                defaults={
                    "rating": form.cleaned_data["rating"],
                    "comment": form.cleaned_data["comment"],
                },
            )
            messages.success(request, "Thank you! Your feedback has been recorded.")
    return redirect("ticket_detail", pk=pk)

@login_required
def reports(request):
    if role(request) != "admin":
        return redirect("dashboard")
    tickets = Ticket.objects.all()
    active_statuses = ["pending", "assigned", "in_progress"]
    resolved_statuses = ["resolved", "closed"]
    total = tickets.count()
    by_status = list(tickets.values("status").annotate(total=Count("id")))
    by_category = list(tickets.values("category_id", "category__name").annotate(total=Count("id")).order_by("-total"))
    by_priority = list(tickets.values("priority").annotate(total=Count("id")))
    for category in by_category:
        category["share_percent"] = round(category["total"] * 100 / total) if total else 0

    first_staff_update = TicketUpdate.objects.filter(
        ticket_id=OuterRef("pk"),
        author__profile__role="admin",
    ).order_by("created_at").values("created_at")[:1]
    responded_tickets = tickets.annotate(first_response_at=Subquery(first_staff_update)).exclude(
        first_response_at__isnull=True
    ).annotate(
        response_time=ExpressionWrapper(F("first_response_at") - F("created_at"), output_field=DurationField())
    )
    average_response = responded_tickets.aggregate(value=Avg("response_time"))["value"]
    average_resolution = tickets.filter(resolved_at__isnull=False).annotate(
        resolution_time=ExpressionWrapper(F("resolved_at") - F("created_at"), output_field=DurationField())
    ).aggregate(value=Avg("resolution_time"))["value"]
    technicians = User.objects.filter(profile__role="user").exclude(
        Q(username__iexact="technician")
        | Q(first_name__iexact="RYUIN", last_name__iexact="MUNOZ")
    ).annotate(
        active_tickets=Count("assigned_tickets", filter=Q(assigned_tickets__status__in=active_statuses)),
        total_tickets=Count("assigned_tickets"),
    ).order_by("-active_tickets", "username")
    return render(request, "tickets/reports.html", {
        "total": total,
        "active_total": tickets.filter(status__in=active_statuses).count(),
        "unassigned_total": tickets.filter(status__in=active_statuses, assigned_to__isnull=True).count(),
        "resolved_total": tickets.filter(status__in=resolved_statuses).count(),
        "critical_total": tickets.filter(status__in=active_statuses, priority="critical").count(),
        "average_response_hours": round(average_response.total_seconds() / 3600, 1) if average_response is not None else None,
        "average_resolution_hours": round(average_resolution.total_seconds() / 3600, 1) if average_resolution is not None else None,
        "technicians": technicians,
        "by_status": by_status,
        "by_category": by_category,
        "by_priority": by_priority,
    })

@login_required
def user_management(request):
    if role(request) != "admin":
        return redirect("dashboard")
    visible_users = User.objects.exclude(
        Q(username__iexact="technician")
        | Q(
            username__iexact="DUDDY ALBERT BALMEO FONTANILLA",
            email__iexact="duddyalbert017@gmail.com",
        )
    )
    user_ids = list(visible_users.values_list("id", flat=True))
    existing_profile_ids = set(
        Profile.objects.filter(user_id__in=user_ids).values_list("user_id", flat=True)
    )
    for account in visible_users.filter(id__in=[user_id for user_id in user_ids if user_id not in existing_profile_ids]):
        initials = (account.first_name[:1] + account.last_name[:1]).upper() if (account.first_name or account.last_name) else account.username[:2].upper()
        Profile.objects.get_or_create(
            user=account,
            defaults={
                "role": "admin" if account.is_superuser else "user",
                "avatar_initials": initials,
            },
        )
    users = list(
        visible_users.select_related("profile")
    )
    person_priority = {
        "allen john dela cruz cardinez": 0,
        "duddy albert balmeo fontanilla": 1,
        "manager": 1,
        "paul eliniel flores sibul": 2,
        "juan": 2,
        "redford peralta biscarra": 3,
        "employee": 3,
        "lander rabe ragmac": 4,
        "admin": 4,
    }
    technician_priority = {
        "hardware_support": 6,
        "software_support": 7,
        "access_support": 8,
        "network_support": 9,
        "printer_support": 10,
        "hardware support technician": 6,
        "software support specialist": 7,
        "it access support specialist": 8,
        "network support technician": 9,
        "printer support technician": 10,
    }

    def user_sort_key(user):
        username = user.username.casefold()
        full_name = user.get_full_name().casefold()
        priority = person_priority.get(username, person_priority.get(full_name))
        if priority is None:
            priority = technician_priority.get(username, technician_priority.get(full_name))
        if priority is None:
            profile = getattr(user, "profile", None)
            priority = 11 if profile is None or profile.role == "user" else 5
        return priority, full_name, username

    users.sort(key=user_sort_key)
    return render(request, "tickets/user_management.html", {"users": users})

@login_required
def user_edit(request, pk):
    if role(request) != "admin":
        return redirect("dashboard")
    target_user = get_object_or_404(User.objects.select_related("profile"), pk=pk)
    if request.method == "POST":
        form = ManagedUserForm(request.POST, request.FILES, instance=target_user, target_user=target_user)
        if form.is_valid():
            form.save()
            messages.success(request, f"Account for {target_user.get_full_name() or target_user.username} updated.")
            return redirect("user_management")
    else:
        form = ManagedUserForm(instance=target_user, target_user=target_user)
    return render(request, "tickets/user_edit.html", {"form": form, "target_user": target_user})

@login_required
@require_POST
def user_delete(request, pk):
    if role(request) != "admin":
        return redirect("dashboard")

    target_user = get_object_or_404(
        User.objects.exclude(
            Q(username__iexact="technician")
            | Q(
                username__iexact="DUDDY ALBERT BALMEO FONTANILLA",
                email__iexact="duddyalbert017@gmail.com",
            )
        ),
        pk=pk,
    )
    if target_user.pk == request.user.pk:
        messages.error(request, "You cannot delete your own account.")
        return redirect("user_management")

    account_name = target_user.get_full_name() or target_user.username
    target_user.delete()
    messages.success(
        request,
        f"Account for {account_name} and its submitted tickets and history were permanently deleted.",
    )
    return redirect("user_management")

@login_required
def profile(request):
    return render(request, "tickets/profile.html", {"profile": getattr(request.user, "profile", None)})

@login_required
def profile_edit(request):
    profile = getattr(request.user, "profile", None)
    if not profile:
        return redirect("profile")

    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, "Your profile was updated successfully.")
            return redirect("profile")
    else:
        form = ProfileUpdateForm(instance=profile, user=request.user)

    return render(request, "tickets/profile_edit.html", {"form": form, "profile": profile})

@login_required
def notification_open(request, pk):
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    if notification.read_at is None:
        notification.read_at = timezone.now()
        notification.save(update_fields=["read_at"])
    return redirect("ticket_detail", pk=notification.ticket_id)

@login_required
def notifications_feed(request):
    user_notifications = request.user.notifications.select_related(
        "ticket",
        "ticket__submitted_by",
    )[:8]
    notifications = []
    for notification in user_notifications:
        submitter = notification.ticket.submitted_by
        notifications.append({
            "message": notification.message,
            "ticket_title": notification.ticket.title,
            "ticket_number": notification.ticket.ticket_number,
            "submitter": submitter.get_full_name() or submitter.username,
            "created_at": timezone.localtime(notification.created_at).strftime("%b %d, %Y %I:%M %p"),
            "url": reverse("notification_open", args=[notification.pk]),
            "unread": notification.read_at is None,
        })

    return JsonResponse({
        "unread_count": request.user.notifications.filter(read_at__isnull=True).count(),
        "notifications": notifications,
    })

@login_required
@require_POST
def notifications_mark_read(request):
    request.user.notifications.filter(read_at__isnull=True).update(read_at=timezone.now())
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"unread_count": 0})
    next_url = request.POST.get("next", "")
    if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return redirect(next_url)
    return redirect("dashboard")

@login_required
def knowledge_base(request):
    articles = [
        {
            "title": "Password Reset",
            "summary": "Steps for requesting a secure company password reset.",
            "steps": [
                "Verify the employee using the approved identity-check process. Never ask for their current password or MFA code.",
                "Check whether the account is locked or whether the employee can use the official self-service password reset.",
                "If support is needed, use the approved admin reset process and share reset instructions through a verified channel.",
                "Ask the employee to set a new password and confirm they can sign in without sharing the password with you.",
            ],
            "response": "I can help you reset your password. First, I will verify your identity using our approved process. I will never ask you to tell me your password or MFA code.",
        },
        {
            "title": "Wi-Fi Connection",
            "summary": "Basic checks for office Wi-Fi and network connectivity issues.",
            "steps": [
                "Confirm the employee is connecting to the correct company Wi-Fi network and note the exact error message.",
                "Turn Wi-Fi off and on, then reconnect. If appropriate, restart the device and try again.",
                "Check whether other approved devices in the same area can connect to help identify a device or area issue.",
                "If it still fails, record the device name, location, time, and error, then escalate to the network team.",
            ],
            "response": "Let's confirm you're using the company Wi-Fi and reconnect your device. If it still does not work, I'll record the location and error message so our network team can investigate.",
        },
        {
            "title": "Printer Troubleshooting",
            "summary": "Quick checks before submitting a printer support ticket.",
            "steps": [
                "Check that the printer is powered on, online, and free of paper or toner alerts.",
                "Confirm the employee selected the correct printer and check for paused or stuck jobs in the print queue.",
                "Try one test page after clearing a stuck job or reconnecting to the printer.",
                "If the problem remains, note the printer name, location, error code, and whether other users are affected.",
            ],
            "response": "I'll check that the printer is online, confirm the correct printer is selected, and review the print queue. If it still fails, I'll record the printer name and error so we can send it to IT.",
        },
        {
            "title": "Software Installation",
            "summary": "How to request approved business software.",
            "steps": [
                "Ask for the software name, business purpose, department, and the device that needs it.",
                "Check the approved software catalog and confirm whether a license or manager approval is required.",
                "Submit an installation request with the required approvals; do not install unapproved software or bypass security controls.",
                "Tell the employee the request status and arrange installation through the approved IT process.",
            ],
            "response": "Please share the software name and what you need it for. I'll check whether it's approved and whether an approval is needed, then submit the request through our IT process.",
        },
    ]
    return render(request, "tickets/knowledge_base.html", {"articles": articles})

@login_required
def settings_page(request):
    if role(request) != "admin":
        return redirect("dashboard")
    return render(request, "tickets/settings.html")
