import json

from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Case, IntegerField, Q, Value, When
from .models import Ticket, TicketUpdate, Feedback, Category, Profile


def validate_profile_image(upload):
    if not upload:
        return
    if upload.size > 5 * 1024 * 1024:
        raise forms.ValidationError("Profile pictures must be 5 MB or smaller.")
    header = upload.read(12)
    upload.seek(0)
    valid = (
        header.startswith(b"\xff\xd8\xff")
        or header.startswith(b"\x89PNG\r\n\x1a\n")
        or header.startswith((b"GIF87a", b"GIF89a"))
        or (header.startswith(b"RIFF") and header[8:12] == b"WEBP")
    )
    if not valid:
        raise forms.ValidationError("Choose a valid JPEG, PNG, GIF, or WebP image.")

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["department", "user_identifier", "profile_picture"]
        widgets = {
            "department": forms.Select(attrs={"class": "form-control"}),
            "user_identifier": forms.TextInput(attrs={"class": "form-control", "placeholder": "User ID"}),
            "profile_picture": forms.ClearableFileInput(attrs={"class": "form-control", "accept": "image/*"}),
        }

    first_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    last_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={"class": "form-control"}))
    new_password = forms.CharField(required=False, widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}), label="New password")
    confirm_password = forms.CharField(required=False, widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}), label="Confirm new password")
    current_password = forms.CharField(required=False, widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "current-password"}), label="Current password")

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields["first_name"].initial = self.user.first_name
            self.fields["last_name"].initial = self.user.last_name
            self.fields["email"].initial = self.user.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user:
            self.user.first_name = self.cleaned_data.get("first_name", "").strip()
            self.user.last_name = self.cleaned_data.get("last_name", "").strip()
            email = self.cleaned_data.get("email", "").strip()
            self.user.email = email
            new_password = self.cleaned_data.get("new_password")
            if new_password:
                self.user.set_password(new_password)
            self.user.save()
        if commit:
            profile.save()
        return profile

    def clean(self):
        cleaned = super().clean()
        new_password = cleaned.get("new_password")
        confirmation = cleaned.get("confirm_password")
        if new_password or confirmation:
            if new_password != confirmation:
                self.add_error("confirm_password", "The new passwords do not match.")
            if not cleaned.get("current_password") or not self.user.check_password(cleaned["current_password"]):
                self.add_error("current_password", "Enter your current password to change it.")
        picture = cleaned.get("profile_picture")
        if picture:
            try:
                validate_profile_image(picture)
            except forms.ValidationError as error:
                self.add_error("profile_picture", error)
        return cleaned


class ManagedUserForm(forms.ModelForm):
    role = forms.ChoiceField(choices=Profile.ROLE_CHOICES, widget=forms.Select(attrs={"class": "form-control"}))
    department = forms.ChoiceField(choices=[("", "—"), *Profile.DEPARTMENT_CHOICES], required=False, widget=forms.Select(attrs={"class": "form-control"}))
    profile_picture = forms.FileField(required=False, widget=forms.ClearableFileInput(attrs={"class": "form-control", "accept": "image/*"}))
    new_password = forms.CharField(required=False, widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}))

    class Meta:
        model = get_user_model()
        fields = ["first_name", "last_name", "email", "is_active"]
        widgets = {"first_name": forms.TextInput(attrs={"class": "form-control"}), "last_name": forms.TextInput(attrs={"class": "form-control"}), "email": forms.EmailInput(attrs={"class": "form-control"}), "is_active": forms.CheckboxInput()}

    def __init__(self, *args, **kwargs):
        self.target_user = kwargs.pop("target_user")
        super().__init__(*args, **kwargs)
        self.fields["role"].initial = "admin" if self.target_user.profile.role in {"admin", "manager"} or self.target_user.is_superuser else "user"
        self.fields["department"].initial = self.target_user.profile.department
        self.fields["profile_picture"].initial = self.target_user.profile.profile_picture

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("new_password")
        if password:
            user.set_password(password)
        if commit:
            user.save()
            profile = user.profile
            profile.role = self.cleaned_data["role"]
            profile.department = self.cleaned_data["department"]
            picture = self.cleaned_data.get("profile_picture")
            if picture:
                profile.profile_picture = picture
            profile.save()
            if self.cleaned_data["role"] == "admin":
                user.is_staff = True
                user.save(update_fields=["is_staff"])
            elif not user.is_superuser:
                user.is_staff = False
                user.save(update_fields=["is_staff"])
        return user

    def clean_profile_picture(self):
        picture = self.cleaned_data.get("profile_picture")
        validate_profile_image(picture)
        return picture

class TicketForm(forms.ModelForm):
    CATEGORY_OPTIONS = ["Hardware", "Software", "Network", "Account Access", "Other"]
    OTHER_CUSTOM_ISSUE = "Other / Type your own issue"
    ISSUE_OPTIONS = {
        "Hardware": [
            "Computer/Laptop not turning on",
            "Computer/Laptop freezing",
            "Computer/Laptop running slow",
            "Overheating",
            "Blue screen",
            "Keyboard not working",
            "Mouse not working",
            "Monitor not working",
            "No display",
            "Screen flickering",
            "Webcam not working",
            "Microphone not working",
            "Speaker not working",
            "USB port not working",
            "USB device not detected",
            "Hard drive/SSD problem",
            "RAM problem",
            "Battery not charging",
            "Battery draining quickly",
            "Power adapter problem",
            "Physical hardware damage",
        ],
        "Software": [
            "Application not opening",
            "Application crashing",
            "Application freezing",
            "Application not responding",
            "Software installation problem",
            "Software update problem",
            "Software error",
            "Windows/Operating System problem",
            "Driver problem",
            "Missing software",
            "Software compatibility problem",
            "Software activation/license problem",
            "Program running slowly",
            "File cannot be opened",
            "Application configuration problem",
        ],
        "Network": [
            "No internet connection",
            "Slow internet",
            "Intermittent internet connection",
            "Wi-Fi not connecting",
            "Wi-Fi disconnecting",
            "LAN/Ethernet not working",
            "Network unavailable",
            "Cannot access website",
            "Cannot access shared folder",
            "Cannot access network drive",
            "DNS problem",
            "IP address problem",
            "VPN not connecting",
            "VPN disconnecting",
            "High network latency",
            "Network timeout",
            "Network authentication problem",
        ],
        "Account Access": [
            "Cannot log in",
            "Forgot password",
            "Password reset",
            "Account locked",
            "Account disabled",
            "User ID problem",
            "Cannot access account",
            "Access denied",
            "Permission denied",
            "Cannot access system",
            "Cannot access application",
            "Cannot access shared files",
            "Account activation problem",
            "Account deactivation problem",
            "Change account information",
        ],
        "Other": [
            OTHER_CUSTOM_ISSUE,
            "Email problem",
            "Email notification problem",
            "Website problem",
            "System error",
            "System unavailable",
            "Service unavailable",
            "Data not saving",
            "Data not updating",
            "Incorrect data",
            "Missing data",
            "Duplicate data",
            "File upload problem",
            "File download problem",
            "File sharing problem",
            "Report generation problem",
            "Notification problem",
            "Feature not working",
            "Broken link",
            "Configuration problem",
            "Synchronization problem",
            "Database problem",
            "Server problem",
            "API error",
            "Integration problem",
            "Security concern",
            "Suspicious activity",
            "Unauthorized activity",
            "Transaction problem",
        ],
    }
    title = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.HiddenInput(),
    )
    issue_type = forms.ChoiceField(required=False, choices=[("", "Select a specific issue")])
    device_system = forms.CharField(
        required=False,
        max_length=120,
        widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "off"}),
        label="Device/System",
    )
    other_issue = forms.CharField(
        required=False,
        max_length=120,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Type the issue you encountered..."}),
        label="Specific Issue",
    )

    class Meta:
        model = Ticket
        fields = ["category", "issue_type", "device_system", "priority", "description", "attachment"]
        widgets = {
            "category": forms.Select(attrs={"class": "form-control"}),
            "priority": forms.Select(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 5, "placeholder": "Describe the problem in detail..."}),
            "attachment": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        category_queryset = Category.objects.filter(name__in=self.CATEGORY_OPTIONS)
        if self.instance.pk and self.instance.category_id:
            category_queryset = Category.objects.filter(
                Q(name__in=self.CATEGORY_OPTIONS) | Q(pk=self.instance.category_id)
            )
        unique_categories = []
        seen_names = set()
        for category in category_queryset:
            if category.name in seen_names:
                continue
            seen_names.add(category.name)
            unique_categories.append(category)
        category_queryset = Category.objects.filter(pk__in=[category.pk for category in unique_categories])
        ordered_ids = []
        for category_name in ["Hardware", "Software", "Network", "Account Access", "Other"]:
            category = category_queryset.filter(name=category_name).first()
            if category:
                ordered_ids.append(category.pk)
        remaining_ids = [category.pk for category in category_queryset.exclude(pk__in=ordered_ids)]
        ordered_ids.extend(remaining_ids)
        self.fields["category"].queryset = Category.objects.filter(pk__in=ordered_ids).order_by(
            Case(
                *[When(pk=pk, then=idx) for idx, pk in enumerate(ordered_ids)],
                output_field=IntegerField(),
            )
        )
        self.fields["category"].empty_label = "Select a category"
        self.fields["category"].initial = ""
        self.fields["category"].widget.attrs["data-issue-map"] = json.dumps({
            str(category.pk): self.ISSUE_OPTIONS.get(category.name, [])
            for category in unique_categories
        })
        category_value = self.data.get(self.add_prefix("category")) if self.is_bound else self.instance.category_id
        selected_category = Category.objects.filter(pk=category_value).first() if category_value else None
        category_name = selected_category.name if selected_category else ""
        choices = self.ISSUE_OPTIONS.get(category_name, [])
        self.fields["issue_type"].choices = [("", "Select a specific issue")] + [(choice, choice) for choice in choices]
        if self.instance.pk and category_name == "Other" and not self.is_bound:
            if self.instance.issue_type in choices:
                self.fields["issue_type"].initial = self.instance.issue_type
            else:
                self.fields["issue_type"].initial = self.OTHER_CUSTOM_ISSUE
                self.fields["other_issue"].initial = self.instance.issue_type
        self.fields["issue_type"].required = bool(category_name)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get("category")
        if category and category.name == "Other":
            selected_issue = cleaned_data.get("issue_type")
            if selected_issue == self.OTHER_CUSTOM_ISSUE:
                issue = (cleaned_data.get("other_issue") or "").strip()
                if issue:
                    cleaned_data["issue_type"] = issue
                else:
                    self.add_error("other_issue", "Enter the issue you encountered.")
            elif selected_issue:
                cleaned_data["other_issue"] = ""
            else:
                self.add_error("issue_type", "Choose a specific issue for this category.")
        elif category and not cleaned_data.get("issue_type"):
            self.add_error("issue_type", "Choose a specific issue for this category.")

        generated_title = (cleaned_data.get("title") or "").strip()
        if not generated_title:
            issue_name = cleaned_data.get("issue_type") or "Support request"
            category_name = category.name if category else "Support request"
            generated_title = f"{category_name}: {issue_name}"[:200]
        cleaned_data["title"] = generated_title
        return cleaned_data

class RequesterChoiceField(forms.ModelChoiceField):
    display_names = {
        "manager": "DUDDY ALBERT BALMEO FONTANILLA",
        "juan": "PAUL ELINIEL FLORES SIBUL",
        "employee": "REDFORD PERALTA BISCARRA",
        "admin": "LANDER RABE RAGMAC",
    }

    def label_from_instance(self, obj):
        return self.display_names.get(obj.username, obj.get_full_name() or obj.username)

class TechnicianChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        if obj.username.casefold() == "technician" or obj.get_full_name().casefold() == "ryuin munoz":
            return "Current assignee"
        return obj.get_full_name() or obj.username

class TicketManagementForm(TicketForm):
    submitted_by = RequesterChoiceField(queryset=get_user_model().objects.none())
    assigned_to = TechnicianChoiceField(queryset=get_user_model().objects.none())

    ticket_date = forms.DateTimeField(
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(
            format="%Y-%m-%dT%H:%M",
            attrs={"class": "form-control", "type": "datetime-local"},
        ),
    )

    class Meta(TicketForm.Meta):
        fields = [
            "title", "submitted_by", "category", "issue_type", "priority", "status",
            "assigned_to", "description", "attachment", "resolution",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        User = get_user_model()
        requester_order = [
            "ALLEN JOHN DELA CRUZ CARDINEZ",
            "manager",
            "juan",
            "employee",
            "admin",
        ]
        self.fields["submitted_by"].queryset = User.objects.exclude(
            username__in=[
                "technician",
                "hardware_support",
                "software_support",
                "printer_support",
                "network_support",
                "access_support",
            ]
        ).exclude(
            username__iexact="DUDDY ALBERT BALMEO FONTANILLA",
            email__iexact="duddyalbert017@gmail.com",
        ).exclude(
            first_name__iexact="RYUIN",
            last_name__iexact="MUNOZ",
        ).order_by(
            Case(
                *[
                    When(username=username, then=Value(index))
                    for index, username in enumerate(requester_order)
                ],
                default=Value(len(requester_order)),
                output_field=IntegerField(),
            ),
            "first_name",
            "username",
        )
        self.fields["submitted_by"].label = "Requester"
        self.fields["ticket_date"].initial = self.instance.created_at
        self.fields["ticket_date"].label = "Date"
        technician_queryset = User.objects.filter(profile__role="user", is_active=True)
        technician_order = [
            "hardware_support",
            "software_support",
            "access_support",
            "network_support",
            "printer_support",
        ]
        self.fields["assigned_to"].queryset = technician_queryset.order_by(
            Case(
                *[
                    When(username=username, then=Value(index))
                    for index, username in enumerate(technician_order)
                ],
                default=Value(len(technician_order)),
                output_field=IntegerField(),
            ),
            "first_name",
            "username",
        )
        self.fields["assigned_to"].label = "Assigned To"
        self.fields["resolution"].widget = forms.Textarea(
            attrs={"class": "form-control", "rows": 3}
        )
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

    def save(self, commit=True):
        ticket = super().save(commit=False)
        ticket.created_at = self.cleaned_data["ticket_date"]
        if commit:
            ticket.save()
            self.save_m2m()
        return ticket

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("status") in ["resolved", "closed"] and not cleaned_data.get("resolution", "").strip():
            self.add_error("resolution", "Add resolution notes before resolving or closing this ticket.")
        return cleaned_data

class TicketUpdateForm(forms.ModelForm):
    class Meta:
        model = TicketUpdate
        fields = ["message"]
        widgets = {"message": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Add an update, action taken, or note..."})}

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ["rating", "comment"]
        widgets = {
            "rating": forms.Select(
                choices=[(i, "★" * i + "☆" * (5 - i)) for i in range(1, 6)],
                attrs={"class": "form-control"},
            ),
            "comment": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Tell us about your support experience..."})
        }

class TicketFilterForm(forms.Form):
    q = forms.CharField(required=False, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Search ticket number or title..."}))
    category = forms.ModelChoiceField(required=False, queryset=Category.objects.all(), empty_label="All Categories", widget=forms.Select(attrs={"class": "form-control"}))
    priority = forms.ChoiceField(required=False, choices=[("", "All Priorities")] + Ticket.PRIORITIES, widget=forms.Select(attrs={"class": "form-control"}))
    status = forms.ChoiceField(required=False, choices=[("", "All Statuses"), ("active", "Open / Active")] + Ticket.STATUSES, widget=forms.Select(attrs={"class": "form-control"}))
    assigned_to = forms.ModelChoiceField(required=False, queryset=get_user_model().objects.filter(profile__role="user", is_active=True).order_by("first_name", "username"), empty_label="All Users", widget=forms.Select(attrs={"class": "form-control"}))
    assignment = forms.ChoiceField(required=False, choices=[("", "All Assignments"), ("unassigned", "Unassigned")], widget=forms.Select(attrs={"class": "form-control"}))
    created_on = forms.DateField(required=False, widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}))
