from django.db import migrations, models


def cancel_pending_payment_bookings(apps, schema_editor):
    Booking = apps.get_model("booking", "Booking")
    Booking.objects.filter(status="pending_payment").update(status="cancelled")


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("booking", "0002_seed_initial_data"),
    ]

    operations = [
        migrations.RunPython(cancel_pending_payment_bookings, noop),
        migrations.RemoveField(
            model_name="sitesettings",
            name="require_online_payment",
        ),
        migrations.AlterField(
            model_name="booking",
            name="status",
            field=models.CharField(
                choices=[
                    ("confirmed", "Bekreftet"),
                    ("cancelled", "Kansellert"),
                    ("completed", "Fullført"),
                ],
                default="confirmed",
                max_length=20,
                verbose_name="Status",
            ),
        ),
        migrations.DeleteModel(
            name="Payment",
        ),
    ]
