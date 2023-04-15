from django.db import models
from django.contrib.auth.models import AbstractUser


# User to login/logout 
class User(AbstractUser):
    staff_type = models.CharField(max_length=10, choices=[("C", "Courier"),("E", "Employee")])

class Company(models.Model):
    company_name = models.CharField(max_length=30)
    
    def __str__(self):
        return self.company_name 
    
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
    dep_name = models.CharField(max_length=30)
    address = models.ForeignKey(Address, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.dep_name

class Courier(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=30, null = True)
    last_name = models.CharField(max_length=30, null = True)
    IIN = models.CharField(max_length = 15, unique=True, null = True)
    company_id = models.ForeignKey(Company, on_delete=models.CASCADE)
    status = models.CharField(max_length=30, choices=[("A", "Available"),("B", "Busy handling a package")])
    rating = models.IntegerField() # 1-5
    
    def __str__(self):
        return self.first_name

class Employee(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=30, null = True)
    last_name = models.CharField(max_length=30, null = True)
    IIN = models.CharField(max_length = 15, unique=True, null = True)
    department_id = models.ForeignKey(Department, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.first_name

class Client(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    IIN = models.CharField(max_length = 15, unique=True)
    phone_number = models.CharField(max_length=15, blank = True, null = True)
    address = models.ForeignKey(Address, on_delete=models.CASCADE, blank = True, null = True)
    
    def __str__(self):
        return self.first_name

class Order(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    order_id = models.CharField(max_length = 15, unique=True)
    courier = models.ForeignKey(Courier, on_delete=models.SET_NULL, blank = True, null = True)
    description = models.TextField(max_length=200)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    status = models.CharField(max_length=30, choices=[("Not ready", "Not ready"),("Ready to hand", "Ready to hand"), 
                                                      ("Waiting for courier", "Waiting for courier"), ("In progress", "In progress"), ("Delivered", "Delivered")])
    address = models.ForeignKey(Address, on_delete=models.CASCADE, blank = True, null=True)
    
    def __str__(self):
        return str(self.order_id)