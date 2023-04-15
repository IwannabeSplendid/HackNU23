from django.db import models
from django.contrib.auth.models import AbstractUser


# User to login/logout 
class User(AbstractUser):
    staff_type = models.CharField(max_length=10, choices=[("C", "Courier"),("E", "Employee")])

class Company(models.Model):
    company_name = models.CharField(max_length=30)
    
class Address(models.Model):
    oblast = models.CharField(max_length=30) # область
    city = models.CharField(max_length=30)
    street_name = models.CharField(max_length=30, blank = True, null = True)
    house_number = models.CharField(max_length=30, blank = True, null = True)
    apartment_number = models.IntegerField()
    podezd = models.CharField(max_length=30, blank = True, null = True) # подъезд
    corpus = models.CharField(max_length=30, blank = True, null = True)
    zk_name = models.CharField(max_length=30, blank = True, null = True) # название ЖК
    add_info = models.TextField(blank = True, null = True)

class Department(models.Model):
    address = models.ForeignKey(Address, on_delete=models.CASCADE)

class Courier(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=30, null = True)
    last_name = models.CharField(max_length=30, null = True)
    IIN = models.IntegerField(unique=True, null = True)
    company_id = models.ForeignKey(Company, on_delete=models.CASCADE)
    status = models.CharField(max_length=30, choices=[("A", "Available"),("B", "Busy handling a package")])
    rating = models.IntegerField() # 1-5

class Employee(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=30, null = True)
    last_name = models.CharField(max_length=30, null = True)
    IIN = models.IntegerField(unique=True, null = True)
    department_id = models.ForeignKey(Department, on_delete=models.CASCADE)

class Client(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    IIN = models.IntegerField(unique=True)
    phone_number = models.CharField(max_length=15, blank = True, null = True)
    address = models.ForeignKey(Address, on_delete=models.CASCADE)

class Order(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    courier = models.ForeignKey(Courier, on_delete=models.SET_NULL, blank = True, null = True)
    description = models.TextField(max_length=50)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    status = models.CharField(max_length=30, choices=[("Not ready", "Not ready"),("Ready to hand", "Ready to hand"), 
                                                      ("Waiting for courier", "Waiting for courier"), ("In progress", "In progress"), ("Delivered", "Delivered")])
    address = models.ForeignKey(Address, on_delete=models.CASCADE, blank = True, null=True)