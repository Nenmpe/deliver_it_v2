import uuid
from django.contrib.gis.db import models as gis_models
from django.db import models
from users.models import User

class Supplier(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=255, unique=True)
    pan_no = models.CharField(max_length=20, unique=True)
    company_location = gis_models.PointField(geography=True, null=True, blank=True)

    def __str__(self):
        return self.company_name