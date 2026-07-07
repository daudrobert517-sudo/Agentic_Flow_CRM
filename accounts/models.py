from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    company_name = models.CharField(max_length=200, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.username