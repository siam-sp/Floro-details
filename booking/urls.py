from django.urls import path

from . import views

app_name = "booking"

urlpatterns = [
    path("", views.home, name="home"),
    path("om-oss/", views.about, name="about"),
    path("book/", views.booking_create, name="create"),
    path("book/ledige-tider/", views.available_slots_api, name="available_slots"),
    path("book/bekreftelse/<uuid:reference>/", views.booking_confirmation, name="confirmation"),
    path("book/send-kode/", views.send_verification_code, name="send_verification_code"),
    path("book/verifiser-kode/", views.verify_email_code, name="verify_email_code"),
]
