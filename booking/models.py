import datetime
import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone


class SiteSettings(models.Model):
    """Singleton with the site-wide business info and booking rules."""

    business_name = models.CharField(max_length=120, default="Florø Detailing")
    phone = models.CharField("Telefon", max_length=30, default="+47 483 03 985")
    email = models.EmailField("E-post", blank=True)
    address = models.CharField("Adresse/sted", max_length=200, default="Florø")
    instagram_url = models.URLField("Instagram", blank=True)
    facebook_url = models.URLField("Facebook", blank=True)

    hero_heading = models.CharField(
        max_length=150, default="Din bil fortjener det beste"
    )
    hero_subheading = models.CharField(
        max_length=250,
        default="Profesjonell bilvask og detailing i Florø. Book time på under ett minutt.",
    )
    about_text = models.TextField(
        blank=True,
        default=(
            "Florø Detailing tilbyr grundig og skånsom bilvask og detailing for "
            "folk i Florø-området. Vi behandler hver bil som om det var vår egen."
        ),
    )

    simultaneous_capacity = models.PositiveIntegerField(
        "Antall biler samtidig",
        default=1,
        help_text="Hvor mange biler kan vaskes/behandles på samme tid (antall vaskeplasser).",
    )
    booking_lead_time_hours = models.PositiveIntegerField(
        "Minste varsel før booking (timer)",
        default=2,
        help_text="Kunder kan ikke booke en tid som er nærmere enn dette.",
    )
    booking_horizon_days = models.PositiveIntegerField(
        "Hvor mange dager frem kan det bookes",
        default=30,
    )

    class Meta:
        verbose_name = "Nettsideinnstilling"
        verbose_name_plural = "Nettsideinnstillinger"

    def __str__(self):
        return "Nettsideinnstillinger"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


WEEKDAY_CHOICES = [
    (0, "Mandag"),
    (1, "Tirsdag"),
    (2, "Onsdag"),
    (3, "Torsdag"),
    (4, "Fredag"),
    (5, "Lørdag"),
    (6, "Søndag"),
]


class BusinessHours(models.Model):
    weekday = models.PositiveSmallIntegerField(
        "Ukedag", choices=WEEKDAY_CHOICES, unique=True
    )
    is_closed = models.BooleanField("Stengt denne dagen", default=False)
    open_time = models.TimeField("Åpner", default="08:00")
    close_time = models.TimeField("Stenger", default="18:00")

    class Meta:
        verbose_name = "Åpningstid"
        verbose_name_plural = "Åpningstider"
        ordering = ["weekday"]

    def __str__(self):
        if self.is_closed:
            return f"{self.get_weekday_display()}: Stengt"
        return f"{self.get_weekday_display()}: {self.open_time}–{self.close_time}"

    def clean(self):
        if not self.is_closed and self.open_time >= self.close_time:
            raise ValidationError("Åpningstid må være før stengetid.")


class ClosedDate(models.Model):
    """One-off closures: holidays, vacation, etc. Blocks bookings for that date."""

    date = models.DateField("Dato", unique=True)
    reason = models.CharField("Årsak", max_length=200, blank=True)

    class Meta:
        verbose_name = "Stengt dato"
        verbose_name_plural = "Stengte datoer"
        ordering = ["date"]

    def __str__(self):
        return f"{self.date} ({self.reason})" if self.reason else str(self.date)


class Service(models.Model):
    name = models.CharField("Navn", max_length=100)
    slug = models.SlugField("URL-navn", max_length=110, unique=True)
    description = models.TextField("Beskrivelse", blank=True)
    price_kr = models.PositiveIntegerField("Pris (kr)")
    duration_minutes = models.PositiveIntegerField(
        "Varighet (minutter)",
        default=60,
        help_text="Hvor lang tid tar denne tjenesten? Styrer ledige tider i bookingkalenderen.",
    )
    image = models.ImageField("Bilde", upload_to="services/", blank=True, null=True)
    is_active = models.BooleanField("Aktiv (vises på nettsiden)", default=True)
    order = models.PositiveIntegerField("Rekkefølge", default=0)

    class Meta:
        verbose_name = "Tjeneste"
        verbose_name_plural = "Tjenester"
        ordering = ["order", "name"]

    def __str__(self):
        return f"{self.name} ({self.price_kr} kr)"

    def get_absolute_url(self):
        return reverse("booking:create") + f"?service={self.slug}"


class Booking(models.Model):
    class Status(models.TextChoices):
        CONFIRMED = "confirmed", "Bekreftet"
        CANCELLED = "cancelled", "Kansellert"
        COMPLETED = "completed", "Fullført"

    reference = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    service = models.ForeignKey(
        Service, on_delete=models.PROTECT, related_name="bookings", verbose_name="Tjeneste"
    )
    date = models.DateField("Dato")
    start_time = models.TimeField("Starttid")
    end_time = models.TimeField("Sluttid")

    customer_name = models.CharField("Navn", max_length=120)
    customer_phone = models.CharField("Telefon", max_length=30, blank=True)
    customer_email = models.EmailField("E-post")
    notes = models.TextField("Merknad", blank=True)

    status = models.CharField(
        "Status", max_length=20, choices=Status.choices, default=Status.CONFIRMED
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Booking"
        verbose_name_plural = "Bookinger"
        ordering = ["date", "start_time"]

    def __str__(self):
        return f"{self.customer_name} – {self.service.name} ({self.date} {self.start_time})"

    @property
    def start_datetime(self):
        return timezone.make_aware(datetime.datetime.combine(self.date, self.start_time))

    @property
    def is_past(self):
        return self.start_datetime < timezone.now()

    def clean(self):
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError("Starttid må være før sluttid.")


class EmailVerification(models.Model):
    """
    A one-time code sent to an email address to prove the customer can
    actually receive mail there before their booking is accepted.
    """

    VALID_MINUTES = 30
    MAX_ATTEMPTS = 5

    email = models.EmailField("E-post")
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField("Verifisert", null=True, blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = "E-postverifisering"
        verbose_name_plural = "E-postverifiseringer"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.email} ({'verifisert' if self.verified_at else 'uverifisert'})"

    def is_expired(self):
        return timezone.now() > self.created_at + datetime.timedelta(minutes=self.VALID_MINUTES)

    def is_valid(self):
        return self.verified_at is not None and not self.is_expired()
