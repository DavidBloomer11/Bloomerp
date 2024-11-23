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
    date = models.DateField()
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE)

