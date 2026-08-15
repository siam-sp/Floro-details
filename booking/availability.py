import datetime

from django.utils import timezone

from .models import Booking, BusinessHours, ClosedDate, SiteSettings


def is_date_bookable(date):
    """Whether `date` is within the booking horizon and not a closed day/date."""
    settings_obj = SiteSettings.load()
    latest_allowed_date = timezone.localdate() + datetime.timedelta(
        days=settings_obj.booking_horizon_days
    )
    if date > latest_allowed_date or date < timezone.localdate():
        return False
    if ClosedDate.objects.filter(date=date).exists():
        return False
    try:
        hours = BusinessHours.objects.get(weekday=date.weekday())
    except BusinessHours.DoesNotExist:
        return False
    return not hours.is_closed


def get_all_slots(service, date):
    """
    Return a sorted list of (datetime.time, is_available) for every slot in
    the business day on `date`, or [] if the day isn't bookable at all.
    """
    settings_obj = SiteSettings.load()

    if not is_date_bookable(date):
        return []

    hours = BusinessHours.objects.get(weekday=date.weekday())
    earliest_allowed = timezone.now() + datetime.timedelta(
        hours=settings_obj.booking_lead_time_hours
    )
    duration = datetime.timedelta(minutes=service.duration_minutes)

    day_bookings = list(
        Booking.objects.filter(status=Booking.Status.CONFIRMED, date=date).values_list(
            "start_time", "end_time"
        )
    )

    slots = []
    current_dt = datetime.datetime.combine(date, hours.open_time)
    close_dt = datetime.datetime.combine(date, hours.close_time)

    while current_dt + duration <= close_dt:
        slot_start = current_dt.time()
        slot_end = (current_dt + duration).time()

        slot_start_aware = timezone.make_aware(current_dt)
        if slot_start_aware >= earliest_allowed:
            overlapping = sum(
                1
                for existing_start, existing_end in day_bookings
                if existing_start < slot_end and existing_end > slot_start
            )
            slots.append((slot_start, overlapping < settings_obj.simultaneous_capacity))

        current_dt += duration

    return slots


def get_available_slots(service, date):
    """Return a sorted list of available datetime.time start times for `service` on `date`."""
    return [t for t, available in get_all_slots(service, date) if available]
