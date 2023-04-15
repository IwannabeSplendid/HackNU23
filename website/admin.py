from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Courier, Employee, Client, Order, Address, Company, Department

admin.site.register(User, UserAdmin)
admin.site.register(Courier)
admin.site.register(Employee)  
admin.site.register(Client)
admin.site.register(Order)
admin.site.register(Address)
admin.site.register(Company)
admin.site.register(Department)