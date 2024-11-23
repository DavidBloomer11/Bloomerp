from django.db import models

# Create your models here.
class Parent(models.Model):
            name = models.CharField(max_length=255)
            age = models.IntegerField()
            is_active = models.BooleanField(default=True)

class Child(models.Model):
    name = models.CharField(max_length=255)
    age = models.IntegerField()
    is_active = models.BooleanField(default=True)
    parent = models.ForeignKey('app_for_tests.Parent', on_delete=models.CASCADE)
    date = models.DateField()

from django.db import models
from bloomerp.models import BloomerpModel
from bloomerp.models.fields import BloomerpFileField
from django.utils import timezone

class Customer(BloomerpModel):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    address = models.TextField()

class Product(BloomerpModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    image = BloomerpFileField(allowed_extensions=['.jpg', '.jpeg', '.png'])
    price = models.DecimalField(max_digits=10, decimal_places=2)

class Order(BloomerpModel):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    date = models.DateField(default=timezone.now)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    status = models.CharField(max_length=255, choices=STATUS_CHOICES, default='pending')