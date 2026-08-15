import datetime
import logging
import secrets

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .availability import get_all_slots, is_date_bookable
from .emails import send_booking_confirmation_emails, send_verification_email
from .forms import BookingForm
from .models import Booking, EmailVerification, Service, SiteSettings

logger = logging.getLogger(__name__)

WEEKDAY_SHORT = ["Man", "Tir", "Ons", "Tor", "Fre", "Lør", "Søn"]
MONTH_SHORT = [
    "jan", "feb", "mar", "apr", "mai", "jun",
    "jul", "aug", "sep", "okt", "nov", "des",
]

VERIFICATION_RESEND_COOLDOWN_SECONDS = 45


# --- Site pages ---------------------------------------------------------

def home(request):
    services = Service.objects.filter(is_active=True)
    return render(request, "booking/home.html", {"services": services})


def about(request):
    return render(request, "booking/about.html")


# --- Booking flow --------------------------------------------------------

def _upcoming_days(horizon_days):
    today = timezone.localdate()
    days = []
    for offset in range(horizon_days + 1):
        date = today + datetime.timedelta(days=offset)
        days.append(
            {
                "iso": date.isoformat(),
                "weekday": WEEKDAY_SHORT[date.weekday()],
                "day": date.day,
                "month": MONTH_SHORT[date.month - 1],
                "bookable": is_date_bookable(date),
            }
        )
    return days


def booking_create(request):
    services = Service.objects.filter(is_active=True)
    preselected_slug = request.GET.get("service") or request.POST.get("service_slug")
    preselected_service = services.filter(slug=preselected_slug).first() or services.first()
    site = SiteSettings.load()

    if request.method == "POST":
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save()
            send_booking_confirmation_emails(booking)
            return redirect("booking:confirmation", reference=booking.reference)
    else:
        form = BookingForm(initial={"service": preselected_service})

    return render(
        request,
        "booking/booking_create.html",
        {
            "services": services,
            "preselected_service": preselected_service,
            "form": form,
            "days": _upcoming_days(site.booking_horizon_days),
        },
    )


def available_slots_api(request):
    service_slug = request.GET.get("service")
    date_str = request.GET.get("date")

    service = get_object_or_404(Service, slug=service_slug, is_active=True)
    try:
        date = datetime.date.fromisoformat(date_str)
    except (TypeError, ValueError):
        return JsonResponse({"error": "Ugyldig dato"}, status=400)

    slots = get_all_slots(service, date)
    return JsonResponse(
        {"slots": [{"time": t.strftime("%H:%M"), "available": available} for t, available in slots]}
    )


def booking_confirmation(request, reference):
    booking = get_object_or_404(Booking, reference=reference)
    return render(request, "booking/booking_confirmation.html", {"booking": booking})


# --- Email verification ---------------------------------------------------

@require_POST
def send_verification_code(request):
    email = (request.POST.get("email") or "").strip()
    try:
        validate_email(email)
    except DjangoValidationError:
        return JsonResponse({"error": "Ugyldig e-postadresse."}, status=400)

    last = EmailVerification.objects.filter(email__iexact=email).order_by("-created_at").first()
    if last:
        seconds_since = (timezone.now() - last.created_at).total_seconds()
        if seconds_since < VERIFICATION_RESEND_COOLDOWN_SECONDS:
            wait = int(VERIFICATION_RESEND_COOLDOWN_SECONDS - seconds_since)
            return JsonResponse(
                {"error": f"Vent {wait} sekunder før du ber om en ny kode."}, status=429
            )

    code = "".join(secrets.choice("0123456789") for _ in range(6))
    verification = EmailVerification.objects.create(email=email, code=code)
    try:
        send_verification_email(email, code)
    except Exception:
        logger.exception("Failed to send verification email to %s", email)
        verification.delete()
        return JsonResponse(
            {"error": "Kunne ikke sende e-post akkurat nå. Prøv igjen om litt."}, status=502
        )
    return JsonResponse({"ok": True})


@require_POST
def verify_email_code(request):
    email = (request.POST.get("email") or "").strip()
    code = (request.POST.get("code") or "").strip()

    verification = (
        EmailVerification.objects.filter(email__iexact=email, verified_at__isnull=True)
        .order_by("-created_at")
        .first()
    )
    if not verification or verification.is_expired():
        return JsonResponse({"error": "Koden er utløpt. Be om en ny kode."}, status=400)

    if verification.attempts >= EmailVerification.MAX_ATTEMPTS:
        return JsonResponse({"error": "For mange forsøk. Be om en ny kode."}, status=400)

    if not secrets.compare_digest(code, verification.code):
        verification.attempts += 1
        verification.save(update_fields=["attempts"])
        return JsonResponse({"error": "Feil kode. Prøv igjen."}, status=400)

    verification.verified_at = timezone.now()
    verification.save(update_fields=["verified_at"])
    return JsonResponse({"ok": True})
