from django.db import models

# Create your models here.
class Address(models.Model):
    address = models.CharField(max_length=200)

class Transaction(models.Model):
    address = models.ForeignKey(Address, on_delete=models.CASCADE)
    hash_id = models.CharField(max_length=200)
    value = models.BigIntegerField(default=0)
    date = models.DateTimeField()