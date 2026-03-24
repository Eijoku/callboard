from django.contrib import admin

from .models import Advertisement, RegistrationConfirmation, Response


@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "author", "created_at")
    list_filter = ("category", "created_at")
    search_fields = ("title", "content", "author__username", "author__email")


@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = ("advertisement", "author", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("text", "author__username", "author__email", "advertisement__title")


@admin.register(RegistrationConfirmation)
class RegistrationConfirmationAdmin(admin.ModelAdmin):
    list_display = ("user", "code", "created_at")
    search_fields = ("user__username", "user__email", "code")
