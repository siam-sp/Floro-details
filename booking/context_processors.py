from .models import BusinessHours, SiteSettings


def site_settings(request):
    return {
        "site_settings": SiteSettings.load(),
        "business_hours": BusinessHours.objects.order_by("weekday"),
    }
