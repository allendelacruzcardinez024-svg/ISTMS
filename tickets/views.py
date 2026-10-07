from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .forms import TicketForm, TicketUpdateForm, FeedbackForm, TicketFilterForm
from .models import Profile, Category, Ticket, TicketUpdate, Feedback

def role(request):
    return getattr(getattr(request.user, "profile", None), "role", "employee")

def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        if "@" in username:
            try:
                user_obj = User.objects.get(email__iexact=username)
                username = user_obj.username
            except (User.DoesNotExist, User.MultipleObjectsReturned):
                pass
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, "Welcome back to ISTMS.")
            return redirect("dashboard")
        messages.error(request, "Invalid username or password.")
    return render(request, "tickets/index.html")

def logout_view(request):
    logout(request)
    return redirect("login")


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        password2 = request.POST.get("password2", "")
        if not (username and email and password and password2):
            messages.error(request, "Please fill in all fields.")
            return redirect("register")
        if password != password2:
            messages.error(request, "Passwords do not match.")
            return redirect("register")
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("register")
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect("register")
        user = User.objects.create_user(username=username, email=email, password=password)
        Profile.objects.create(user=user)
        login(request, user)
        messages.success(request, "Account created successfully.")
        return redirect("dashboard")
    return render(request, "tickets/register.html")


@login_required
def dashboard(request):
    r = role(request)
    if r == "employee":
        qs = Ticket.objects.filter(submitted_by=request.user)
        stats = {
            "total": qs.count(),
            "pending": qs.filter(status="pending").count(),
            "progress": qs.filter(status="in_progress").count(),
            "resolved": qs.filter(status__in=["resolved", "closed"]).count(),
        }
        recent = qs[:5]
        template = "tickets/dashboard_employee.html"
    elif r == "technician":
        qs = Ticket.objects.all()
        stats = {
            "total": qs.count(),
            "pending": qs.filter(status="pending").count(),
            "progress": qs.filter(status="in_progress").count(),
            "resolved": qs.filter(status="resolved").count(),
            "overdue": qs.filter(status__in=["pending", "assigned", "in_progress"]).count(),
        }
        recent = qs[:6]
        template = "tickets/dashboard_technician.html"
    else:
        qs = Ticket.objects.all()
        stats = {
            "total": qs.count(),
            "pending": qs.filter(status="pending").count(),
            "progress": qs.filter(status="in_progress").count(),
            "resolved": qs.filter(status__in=["resolved", "closed"]).count(),
            "overdue": qs.filter(status__in=["pending", "assigned", "in_progress"]).count(),
        }
        recent = qs[:6]
        category_stats = list(Category.objects.annotate(total=Count("ticket")).values("name", "total"))
        template = "tickets/dashboard_admin.html"
        return render(request, template, {"stats": stats, "recent": recent, "category_stats": category_stats, "role": r})
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
            messages.success(request, f"Ticket {ticket.ticket_number} was submitted successfully.")
            return redirect("my_tickets")
    else:
        form = TicketForm()
    return render(request, "tickets/submit_ticket.html", {"form": form})

@login_required
def my_tickets(request):
    tickets = Ticket.objects.filter(submitted_by=request.user)
    return render(request, "tickets/my_tickets.html", {"tickets": tickets})

@login_required
def all_tickets(request):
    if role(request) == "employee":
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
        if form.cleaned_data.get("status"):
            tickets = tickets.filter(status=form.cleaned_data["status"])
    return render(request, "tickets/ticket_list.html", {"tickets": tickets, "form": form})

@login_required
def ticket_detail(request, pk):
    ticket = get_object_or_404(Ticket.objects.select_related("category", "submitted_by", "assigned_to"), pk=pk)
    r = role(request)
    if r == "employee" and ticket.submitted_by != request.user:
        return redirect("my_tickets")
    technicians = User.objects.filter(profile__role__in=["technician", "admin"]).order_by("first_name", "username")
    return render(request, "tickets/ticket_detail.html", {
        "ticket": ticket,
        "updates": ticket.updates.select_related("author"),
        "update_form": TicketUpdateForm(),
        "feedback_form": FeedbackForm(),
        "technicians": technicians,
        "role": r,
    })

@login_required
def ticket_update(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    if request.method == "POST":
        form = TicketUpdateForm(request.POST)
        if form.is_valid():
            update = form.save(commit=False)
            update.ticket = ticket
            update.author = request.user
            update.save()
            messages.success(request, "Ticket update added.")
    return redirect("ticket_detail", pk=pk)

@login_required
def assign_ticket(request, pk):
    if role(request) not in ["technician", "admin", "manager"]:
        return redirect("ticket_detail", pk=pk)
    ticket = get_object_or_404(Ticket, pk=pk)
    if request.method == "POST":
        user_id = request.POST.get("assigned_to")
        status = request.POST.get("status")
        resolution = request.POST.get("resolution")
        if user_id:
            ticket.assigned_to = get_object_or_404(User, pk=user_id)
        else:
            ticket.assigned_to = None
        if status in dict(Ticket.STATUSES):
            ticket.status = status
            if status in ["resolved", "closed"] and not ticket.resolved_at:
                ticket.resolved_at = timezone.now()
        if resolution is not None:
            ticket.resolution = resolution.strip()
        ticket.save()
        TicketUpdate.objects.create(ticket=ticket, author=request.user, message=f"Ticket assignment/status updated by {request.user.get_full_name() or request.user.username}.")
        messages.success(request, "Ticket assignment/status updated.")
    return redirect("ticket_detail", pk=pk)

@login_required
def ticket_feedback(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    if ticket.submitted_by != request.user:
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
    if role(request) == "employee":
        return redirect("dashboard")
    tickets = Ticket.objects.all()
    by_status = list(tickets.values("status").annotate(total=Count("id")))
    by_category = list(tickets.values("category__name").annotate(total=Count("id")).order_by("-total"))
    by_priority = list(tickets.values("priority").annotate(total=Count("id")))
    return render(request, "tickets/reports.html", {
        "total": tickets.count(),
        "by_status": by_status,
        "by_category": by_category,
        "by_priority": by_priority,
    })

@login_required
def user_management(request):
    if role(request) not in ["admin", "manager"]:
        return redirect("dashboard")
    users = User.objects.select_related("profile").all().order_by("first_name")
    return render(request, "tickets/user_management.html", {"users": users})

@login_required
def profile(request):
    return render(request, "tickets/profile.html", {"profile": getattr(request.user, "profile", None)})

@login_required
def knowledge_base(request):
    articles = [
        ("Password Reset", "Steps for requesting a secure company password reset."),
        ("Wi-Fi Connection", "Basic checks for office Wi-Fi and network connectivity issues."),
        ("Printer Troubleshooting", "Quick checks before submitting a printer support ticket."),
        ("Software Installation", "How to request approved business software."),
    ]
    return render(request, "tickets/knowledge_base.html", {"articles": articles})

@login_required
def settings_page(request):
    return render(request, "tickets/settings.html")