import datetime

from django import forms

from .availability import get_available_slots
from .models import Booking, EmailVerification, Service


class BookingForm(forms.ModelForm):
    service = forms.ModelChoiceField(
        queryset=Service.objects.filter(is_active=True), widget=forms.HiddenInput()
    )
    date = forms.DateField(widget=forms.HiddenInput())
    start_time = forms.TimeField(widget=forms.HiddenInput())

    class Meta:
        model = Booking
        fields = [
            "service",
            "date",
            "start_time",
            "customer_name",
            "customer_phone",
            "customer_email",
            "notes",
        ]
        widgets = {
            "customer_name": forms.TextInput(
                attrs={"class": "input", "placeholder": "Ola Nordmann", "autocomplete": "name"}
            ),
            "customer_phone": forms.TextInput(
                attrs={"class": "input", "placeholder": "+47 123 45 678", "autocomplete": "tel"}
            ),
            "customer_email": forms.EmailInput(
                attrs={"class": "input", "placeholder": "din@epost.no", "autocomplete": "email"}
            ),
            "notes": forms.Textarea(
                attrs={"class": "input", "rows": 3, "placeholder": "Valgfritt: bilmodell, ønsker, e.l."}
            ),
        }
        labels = {
            "customer_name": "Navn",
            "customer_phone": "Telefon",
            "customer_email": "E-post",
            "notes": "Merknad (valgfritt)",
        }

    def clean(self):
        cleaned = super().clean()
        service = cleaned.get("service")
        date = cleaned.get("date")
        start_time = cleaned.get("start_time")
        if service and date and start_time:
            available = get_available_slots(service, date)
            if start_time not in available:
                raise forms.ValidationError(
                    "Denne tiden er dessverre ikke lenger ledig. Velg en annen tid."
                )
            cleaned["end_time"] = (
                datetime.datetime.combine(date, start_time)
                + datetime.timedelta(minutes=service.duration_minutes)
            ).time()

        email = cleaned.get("customer_email")
        if email:
            verification = (
                EmailVerification.objects.filter(email__iexact=email, verified_at__isnull=False)
                .order_by("-verified_at")
                .first()
            )
            if not verification or verification.is_expired():
                raise forms.ValidationError(
                    "Bekreft e-postadressen din med koden du fikk tilsendt før du fullfører bookingen."
                )
        return cleaned

    def save(self, commit=True):
        booking = super().save(commit=False)
        booking.end_time = self.cleaned_data["end_time"]
        if commit:
            booking.save()
        return booking
