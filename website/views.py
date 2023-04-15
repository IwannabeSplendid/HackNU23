from django.shortcuts import render
from .models import Courier, Employee, Client, Order, Address, Company, Department
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
import requests
import googlemaps
from datetime import datetime

# Home page view extends the index.html template
# track, login buttons 
def home(request):
    # return to another page with order info
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
            return redirect('order', order_id = order_number)
            
        return JsonResponse(client_info)
   
    return render(request, 'home.html')


def construct_order(request, order_id):
    order = Order.objects.get(order_id = order_id)
    data = {'order_id': order.order_id, 
                    'order_description': order.description,
                    'order_department': order.department.dep_name,
                    'client_iin': order.client.IIN,
                    'client_first_name': capitalizeFirstLetter(order.client.first_name),
                    'client_last_name': capitalizeFirstLetter(order.client.last_name),
                    'client_phone_number': '+' + order.client.phone_number,
                    }
    
    if request.method == "POST":
        region = request.POST['region']
        city = request.POST['city']
        street = request.POST['street']
        house = request.POST['house']
        apartment = request.POST['apartment']
        order_number = request.POST['order_number']
        floor = request.POST['floor']
        corpus = request.POST['corpus']
        zk_name = request.POST['zk_name']
        trustee = request.POST['trustee']
    #     class Address(models.Model):
    # oblast = models.CharField(max_length=30) # область
    # city = models.CharField(max_length=30)
    # street_name = models.CharField(max_length=30, blank = True, null = True)
    # house_number = models.CharField(max_length=30, blank = True, null = True)
    # apartment_number = models.IntegerField()
    # podezd = models.CharField(max_length=30, blank = True, null = True) # подъезд
    # corpus = models.CharField(max_length=30, blank = True, null = True)
    # zk_name = models.CharField(max_length=30, blank = True, null = True) # название ЖК
    # add_info = models.TextField(blank = True, null = True)
        client = order.client
        address = Address(oblast= region, city = city, street_name = street, house_number = house, apartment_number = apartment, floor = floor, corpus = corpus, zk_name = zk_name, trustee = trustee)
        client_info = get_client_info(iin)
        phone = get_phone_number(iin)
        if not Client.objects.filter(IIN=iin).exists():
            client = Client(first_name = client_info['firstName'], last_name = client_info['lastName'], IIN = client_info['iin'], phone_number = phone)
            client.save()
        
        order = Order.objects.get(order_id = order_number)
        print(order.client.IIN)
        if order.client.IIN == iin:
            return render(request, 'order.html', {'order': order})
            
        return redirect('payment', order_id = order_number)
    
    return render(request, 'client.html', data)

def payment(request, order_id):
    order = Order.objects.get(order_id = order_id)

    gmaps = googlemaps.Client(key='AIzaSyDNttvAKiXJfCcj3HMoyRTip39IyO0AhNA')

    # Geocoding an address
    geocode_result = gmaps.geocode('1600 Amphitheatre Parkway, Mountain View, CA')

    # Look up an address with reverse geocoding
    reverse_geocode_result = gmaps.reverse_geocode((40.714224, -73.961452))

    # Request directions via public transit
    now = datetime.now()
    directions_result = gmaps.directions("Sydney Town Hall",
                                        "Parramatta, NSW",
                                        mode="transit",
                                        departure_time=now)

    # Validate an address with address validation
    addressvalidation_result =  gmaps.addressvalidation(['1600 Amphitheatre Pk'], 
                                                        regionCode='US',
                                                        locality='Mountain View', 
                                                        enableUspsCass=True)
    data = {'order_id': order.order_id, 
                    'order_description': order.description,
                    'order_department': order.department.dep_name,
                    'client_iin': order.client.IIN,
                    'client_first_name': order.client.first_name,
                    'client_last_name': order.client.last_name,
                    'client_phone_number': order.client.phone_number,
                    }
    
    if request.method == "POST":
        #save
        return 0 
    
    return render(request, 'payement.html')

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
    d = {'phone' : phone_number, 'smsText' : message}
    requests.post(url, json = d, headers = {'Content-Type': 'application/json','Authorization': 'Bearer ' + token})
    

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

def capitalizeFirstLetter(string):
    return string[0]+ string[1:].lower();
