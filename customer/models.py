from django.db import models
import uuid
from django.contrib.auth import get_user_model

User = get_user_model()


class Customer(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    country = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=20)

    def __str__(self):
        return self.user.fullname

