from django.db import migrations


def update_business_hours(apps, schema_editor):
    BusinessHours = apps.get_model("booking", "BusinessHours")

    # Monday(0) - Friday(4): 08:00-16:00
    BusinessHours.objects.filter(weekday__in=[0, 1, 2, 3, 4]).update(
        is_closed=False, open_time="08:00", close_time="16:00"
    )
    # Saturday(5) - Sunday(6): closed
    BusinessHours.objects.filter(weekday__in=[5, 6]).update(is_closed=True)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [("booking", "0005_update_services")]
    operations = [migrations.RunPython(update_business_hours, noop)]
