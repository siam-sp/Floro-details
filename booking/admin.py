from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Booking, BusinessHours, ClosedDate, EmailVerification, Service, SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Kontaktinfo", {"fields": ("business_name", "phone", "email", "address", "instagram_url", "facebook_url")}),
        ("Forside-tekst", {"fields": ("hero_heading", "hero_subheading", "about_text")}),
        (
            "Booking-regler",
            {
                "fields": (
                    "simultaneous_capacity",
                    "booking_lead_time_hours",
                    "booking_horizon_days",
                )
            },
        ),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(BusinessHours)
class BusinessHoursAdmin(admin.ModelAdmin):
    list_display = ("get_weekday_display", "is_closed", "open_time", "close_time")
    list_editable = ("is_closed", "open_time", "close_time")
    ordering = ("weekday",)

    def has_add_permission(self, request):
        return BusinessHours.objects.count() < 7

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ClosedDate)
class ClosedDateAdmin(admin.ModelAdmin):
    list_display = ("date", "reason")
    ordering = ("date",)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "price_kr", "duration_minutes", "is_active", "order")
    list_editable = ("price_kr", "duration_minutes", "is_active", "order")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("order", "name")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "start_time",
        "customer_name",
        "service",
        "status",
        "customer_phone",
        "created_at",
        "confirmation_link",
    )
    list_filter = ("status", "service", "date")
    search_fields = ("customer_name", "customer_phone", "customer_email", "reference")
    date_hierarchy = "date"
    readonly_fields = ("reference", "created_at", "updated_at")
    ordering = ("-date", "-start_time")

    @admin.display(description="Bekreftelsesside")
    def confirmation_link(self, obj):
        url = reverse("booking:confirmation", args=[obj.reference])
        return format_html('<a href="{}" target="_blank">Åpne ↗</a>', url)


@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ("email", "created_at", "verified_at", "attempts")
    list_filter = ("verified_at",)
    search_fields = ("email",)
    readonly_fields = ("email", "code", "created_at", "verified_at", "attempts")
    ordering = ("-created_at",)

    def has_add_permission(self, request):
        return False
