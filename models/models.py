from django.db import models as dj_models


class Task(dj_models.Model):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    ]

    telegram_user_id = dj_models.BigIntegerField()
    telegram_username = dj_models.CharField(max_length=255, blank=True, default="")
    name = dj_models.CharField(max_length=255)
    phone_number = dj_models.CharField(max_length=30)
    category = dj_models.CharField(max_length=100)
    address = dj_models.CharField(max_length=255, blank=True, default="")
    description = dj_models.TextField()
    status = dj_models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = dj_models.DateTimeField(auto_now_add=True)
    updated_at = dj_models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} ({self.category}) - {self.status}"


class BotSession(dj_models.Model):
    user_id = dj_models.BigIntegerField(unique=True)
    step = dj_models.CharField(max_length=50, default="name")
    data = dj_models.JSONField(default=dict)
    updated_at = dj_models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Session<{self.user_id}:{self.step}>"


class PaidMember(dj_models.Model):
    user_id = dj_models.BigIntegerField(unique=True)
    username = dj_models.CharField(max_length=255, blank=True, default="")
    full_name = dj_models.CharField(max_length=255, blank=True, default="")
    is_active = dj_models.BooleanField(default=True)
    created_at = dj_models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.user_id} ({'active' if self.is_active else 'inactive'})"
