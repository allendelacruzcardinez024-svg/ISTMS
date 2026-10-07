from django import forms
from .models import Ticket, TicketUpdate, Feedback, Category

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ["category", "priority", "title", "description", "device_system", "location", "attachment"]
        widgets = {
            "category": forms.Select(attrs={"class": "form-control"}),
            "priority": forms.Select(attrs={"class": "form-control"}),
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Brief title of the issue"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 5, "placeholder": "Describe the problem in detail..."}),
            "device_system": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Dell Latitude / Email / Wi-Fi"}),
            "location": forms.TextInput(attrs={"class": "form-control", "placeholder": "Office / Room / Area"}),
            "attachment": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }

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
            "rating": forms.Select(choices=[(i, f"{i} / 5") for i in range(1, 6)], attrs={"class": "form-control"}),
            "comment": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Tell us about your support experience..."})
        }

class TicketFilterForm(forms.Form):
    q = forms.CharField(required=False, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Search ticket number or title..."}))
    category = forms.ModelChoiceField(required=False, queryset=Category.objects.all(), empty_label="All Categories", widget=forms.Select(attrs={"class": "form-control"}))
    priority = forms.ChoiceField(required=False, choices=[("", "All Priorities")] + Ticket.PRIORITIES, widget=forms.Select(attrs={"class": "form-control"}))
    status = forms.ChoiceField(required=False, choices=[("", "All Statuses")] + Ticket.STATUSES, widget=forms.Select(attrs={"class": "form-control"}))
