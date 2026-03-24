from datetime import timedelta

from django.conf import settings
from django.db import models
from django_ckeditor_5.fields import CKEditor5Field
from django.urls import reverse
from django.utils import timezone


class AdvertisementCategory(models.TextChoices):
    TANKS = "tanks", "Танки"
    HEALERS = "healers", "Хилы"
    DAMAGE_DEALERS = "damage_dealers", "ДД"
    TRADERS = "traders", "Торговцы"
    GUILDMASTERS = "guildmasters", "Гилдмастеры"
    QUEST_GIVERS = "quest_givers", "Квестгиверы"
    BLACKSMITHS = "blacksmiths", "Кузнецы"
    LEATHERWORKERS = "leatherworkers", "Кожевники"
    ALCHEMISTS = "alchemists", "Зельевары"
    SPELLMASTERS = "spellmasters", "Мастера заклинаний"


class Advertisement(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="advertisements",
        verbose_name="Автор",
    )
    category = models.CharField(
        max_length=32,
        choices=AdvertisementCategory.choices,
        verbose_name="Категория",
    )
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    content = CKEditor5Field(
        config_name="extends",
        verbose_name="Текст объявления",
        help_text="Используйте визуальный редактор для текста, изображений и встраиваемого медиа.",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Объявление"
        verbose_name_plural = "Объявления"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("board:advertisement_detail", kwargs={"pk": self.pk})


class Response(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Ожидает"
        ACCEPTED = "accepted", "Принят"

    advertisement = models.ForeignKey(
        Advertisement,
        on_delete=models.CASCADE,
        related_name="responses",
        verbose_name="Объявление",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="responses",
        verbose_name="Автор отклика",
    )
    text = models.TextField(verbose_name="Текст отклика")
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Статус",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Отклик"
        verbose_name_plural = "Отклики"
        constraints = [
            models.UniqueConstraint(
                fields=("advertisement", "author"),
                name="unique_response_per_user_and_advertisement",
            )
        ]

    def __str__(self):
        return f"{self.author} -> {self.advertisement}"


class RegistrationConfirmation(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="registration_confirmation",
        verbose_name="Пользователь",
    )
    code = models.CharField(max_length=6, verbose_name="Код")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    class Meta:
        verbose_name = "Подтверждение регистрации"
        verbose_name_plural = "Подтверждения регистрации"

    def __str__(self):
        return f"Код для {self.user.email}"

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=15)
