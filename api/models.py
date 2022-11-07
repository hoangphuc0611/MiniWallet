from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import AbstractBaseUser
from django.db import models
from datetime import datetime
import uuid
unique_id = uuid.uuid4().hex

class Customer(AbstractBaseUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    REQUIRED_FIELDS = ()
    USERNAME_FIELD = 'id'
    def __str__(self):
        return self.id
    
class Wallet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owned_by = models.OneToOneField(Customer, on_delete=models.CASCADE)
    status = models.CharField(max_length=200)
    enabled_at = models.DateTimeField(default=datetime.now, blank=True)
    balance = models.IntegerField(default=0)

    def __str__(self):
        return self.id
class Deposit(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    deposited_by = models.ForeignKey(Customer, on_delete=models.CASCADE)
    status = models.CharField(max_length=200)
    deposited_at = models.DateTimeField(default=datetime.now, blank=True)
    amount = models.IntegerField(default=0)
    reference_id = models.CharField(max_length=200,unique=True)

    def __str__(self):
        return self.id
class Withdrawal(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    withdrawn_by = models.ForeignKey(Customer, on_delete=models.CASCADE)
    status = models.CharField(max_length=200)
    withdrawn_at = models.DateTimeField(default=datetime.now, blank=True)
    amount = models.IntegerField(default=0)
    reference_id = models.CharField(max_length=200)

    def __str__(self):
        return self.id


