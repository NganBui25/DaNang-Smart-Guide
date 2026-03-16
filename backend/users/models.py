import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('admin', 'Admin'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    avatar = models.URLField(blank=True, null=True)
    # date_joined (created_at) inherited from AbstractUser

    class Meta:
        db_table = 'users_user'

    def __str__(self):
        return self.username

    @property
    def is_admin(self):
        return self.role == 'admin' or self.is_superuser
