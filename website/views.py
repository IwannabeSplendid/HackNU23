from django.shortcuts import render
from .models import User, Courier, Employee, Client, Order, Address, Company, Department


# Home page view extends the index.html template
# track, login buttons 
def home(request):
    
    return render(request, 'index.html')



# def index(request):
#     return render(request, 'index.html')

# def index(request):
#     return render(request, 'index.html')

# def index(request):
#     return render(request, 'index.html')

# def index(request):
#     return render(request, 'index.html')