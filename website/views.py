from django.shortcuts import render
from .models import User, Courier, Employee, Client, Order, Address, Company, Department
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
import requests

# Home page view extends the index.html template
# track, login buttons 
def home(request):
    # return to another page with order info
    send_sms('77773378411', 'Hello')
    if request.method == "POST":
        iin = request.POST['iin']
        order_number = request.POST['order_number']
        
        client_info = get_client_info(iin)
        phone = get_phone_number(iin)
        if not Client.objects.filter(IIN=iin).exists():
            client = Client(first_name = client_info['firstName'], last_name = client_info['lastName'], IIN = client_info['iin'], phone_number = phone)
            client.save()
            
        order = Order.objects.get(order_id = order_number)
        print(order.client.IIN)
        if order.client.IIN == iin:
            data = {'order_id': order.order_id, 
                    'order_description': order.description,
                    'order_department': order.department.dep_name,
                    'client_iin': order.client.IIN,
                    'client_first_name': order.client.first_name,
                    'client_last_name': order.client.last_name,
                    'client_phone_number': order.client.phone_number,
                    }
            return render(request, 'order.html', data)
            
        return JsonResponse(client_info)
   
    return render(request, 'home.html')

def construct_order(request, iin):
    if request.method == "POST":
        iin = request.POST['iin']
        order_number = request.POST['order_number']
        client_info = get_client_info(iin)
        phone = get_phone_number(iin)
        if not Client.objects.filter(IIN=iin).exists():
            client = Client(first_name = client_info['firstName'], last_name = client_info['lastName'], IIN = client_info['iin'], phone_number = phone)
            client.save()
        
        order = Order.objects.get(order_id = order_number)
        print(order.client.IIN)
        if order.client.IIN == iin:
            return render(request, 'order.html', {'order': order})
            
        return JsonResponse(client_info)
    
    return render(request, 'order.html')

def get_token():
    url = 'http://hakaton-idp.gov4c.kz/auth/realms/con-web/protocol/openid-connect/token'
    data = {'username': 'test-operator', 'password' : 'DjrsmA9RMXRl', 'client_id' : 'cw-queue-service', 'grant_type' : 'password'}
    
    token = requests.post(url, data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    
    return token.json()['access_token']


def login(request):
    #when submitted (button clicked)
    if request.method == "POST":
        #authenticate user
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username = username, password = password)
        
        #redirect to their pages
        if user is not None: 
            auth_login(request, user)
            return HttpResponseRedirect(reverse('home'))
        else:
            return render(request, 'users/login.html', {
                'message': 'Invalid credentials'
            })
            
    return render(request, 'login.html')
            
def logout(request):
    auth_logout(request)
    return HttpResponseRedirect(reverse('home'))

def send_sms(phone_number, message):
    token = get_token()
    url = 'http://hak-sms123.gov4c.kz/api/smsgateway/send'
    data = {"phone" : phone_number, "smsText" : message}
    
    x = requests.post(url, headers = {'authorization': 'Bearer ' + token}, data = data)
    print(x.content)
    
    

def get_phone_number(iin):
    token = get_token()
    url = 'http://hakaton.gov4c.kz/api/bmg/check/' + iin
    phone = requests.get(url, headers = {'authorization': 'Bearer ' + token}).json()['phone']
    return phone

def get_client_info(iin):
    token = get_token()
    url = 'http://hakaton-fl.gov4c.kz/api/persons/' + iin
    client_info = requests.get(url, headers = {'authorization': 'Bearer ' + token}).json()
    return client_info

# def index(request):
#     return render(request, 'index.html')