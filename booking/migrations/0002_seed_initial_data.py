from django.db import migrations


def seed_data(apps, schema_editor):
    BusinessHours = apps.get_model("booking", "BusinessHours")
    for weekday in range(7):
        BusinessHours.objects.get_or_create(
            weekday=weekday,
            defaults={"is_closed": False, "open_time": "08:00", "close_time": "18:00"},
        )

    Service = apps.get_model("booking", "Service")
    Service.objects.get_or_create(
        slug="bilvask",
        defaults={
            "name": "Bilvask",
            "description": "Grundig utvendig og innvendig vask av bilen din.",
            "price_kr": 400,
            "duration_minutes": 60,
            "is_active": True,
            "order": 0,
        },
    )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [("booking", "0001_initial")]
    operations = [migrations.RunPython(seed_data, noop)]
