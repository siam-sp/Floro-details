from django.conf import settings
from django.core.mail import send_mail

from .models import SiteSettings


def send_verification_email(email, code):
    site = SiteSettings.load()
    message = (
        f"Bekreftelseskoden din er: {code}\n\n"
        f"Skriv koden inn på nettsiden for å bekrefte e-postadressen din og fullføre "
        f"bookingen hos {site.business_name}. Koden er gyldig i 30 minutter."
    )
    send_mail(
        subject=f"Bekreftelseskode: {code} – {site.business_name}",
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )


def send_booking_confirmation_emails(booking):
    site = SiteSettings.load()
    date_str = booking.date.strftime("%d.%m.%Y")
    time_str = booking.start_time.strftime("%H:%M")

    customer_message = (
        f"Hei {booking.customer_name},\n\n"
        f"Timen din hos {site.business_name} er bekreftet:\n\n"
        f"Tjeneste: {booking.service.name}\n"
        f"Dato: {date_str}\n"
        f"Tid: {time_str}\n"
        f"Sted: {site.address}\n\n"
        f"Har du spørsmål? Ring oss på {site.phone}.\n\n"
        f"Vi sees!\n{site.business_name}"
    )
    send_mail(
        subject=f"Bekreftet booking – {site.business_name}",
        message=customer_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[booking.customer_email],
        fail_silently=True,
    )

    if settings.BUSINESS_NOTIFICATION_EMAIL:
        owner_message = (
            f"Ny booking bekreftet:\n\n"
            f"Kunde: {booking.customer_name}\n"
            f"Telefon: {booking.customer_phone}\n"
            f"E-post: {booking.customer_email}\n"
            f"Tjeneste: {booking.service.name}\n"
            f"Dato: {date_str} kl. {time_str}\n"
            f"Merknad: {booking.notes or '-'}\n"
        )
        send_mail(
            subject=f"Ny booking: {booking.customer_name} ({date_str} {time_str})",
            message=owner_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.BUSINESS_NOTIFICATION_EMAIL],
            fail_silently=True,
        )
