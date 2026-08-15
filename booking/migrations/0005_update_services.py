from django.db import migrations


def update_services(apps, schema_editor):
    Service = apps.get_model("booking", "Service")

    # Don't delete Bilvask: existing bookings reference it (on_delete=PROTECT).
    # Deactivating removes it from the site without touching booking history.
    Service.objects.filter(slug="bilvask").update(is_active=False)

    Service.objects.update_or_create(
        slug="lett-vask-innvendig",
        defaults={
            "name": "Lett vask innvendig",
            "description": "Støvsuging og overflatevask av interiøret.",
            "price_kr": 500,
            "duration_minutes": 60,
            "is_active": True,
            "order": 1,
        },
    )
    Service.objects.update_or_create(
        slug="grundigvask-innvendig-med-shine",
        defaults={
            "name": "Grundigvask innvendig med shine",
            "description": (
                "Grundig støvsuging, vask av dashbord og paneler, og full innvendig shine."
            ),
            "price_kr": 750,
            "duration_minutes": 120,
            "is_active": True,
            "order": 2,
        },
    )
    Service.objects.update_or_create(
        slug="rens-av-seter",
        defaults={
            "name": "Rens av seter",
            "description": (
                "Dyprens av ett bilsete (75 kr/stk). Har du flere seter som skal renses, "
                "book tjenesten flere ganger eller noter antall i merknadsfeltet."
            ),
            "price_kr": 75,
            "duration_minutes": 20,
            "is_active": True,
            "order": 3,
        },
    )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [("booking", "0004_emailverification")]
    operations = [migrations.RunPython(update_services, noop)]
