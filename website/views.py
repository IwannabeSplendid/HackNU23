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
import random
from django.db.models import Q

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
        extra = request.POST.get('extra', None)
        
        address = Address(oblast= region, city = city, street_name = street, house_number = house, apartment_number = apartment or None, 
                          floor = floor or None, podezd = order_number or None, corpus = corpus or None, zk_name = zk_name or None, add_info = extra or None)
        address.save()
        order.address =address
        order.date = datetime.now()
        if Client.objects.filter(IIN=trustee).exists():
            order.trustee = trustee
        order.save()
        order.client.address = address
        order.client.save() 
        return redirect('payment', order_id = order.order_id)
    
    return render(request, 'client.html', data)

def payment(request, order_id):
    order = Order.objects.get(order_id = order_id)
    
    cost = 1000
    com_data = []
    for company in Company.objects.all():
        all_couriers = len(Courier.objects.filter(company_id__company_name = company.company_name))
        busy_couriers = len(Courier.objects.filter(company_id = company, status = "B"))
        company_available = (all_couriers - busy_couriers) / all_couriers
        company_cost = cost/company_available
        
        temp = {'company_name': company.company_name, 'company_cost': company_cost, 'company_available': company_available}
        com_data.append(temp)
    
    response = requests.get('https://maps.googleapis.com/maps/api/geocode/json?place_id=ChIJeRpOeF67j4AR9ydy_PIzPuM&key=AIzaSyAd0kKAY8yNMxSL0847Lf7rUexclIDQT10')
    resp_json_payload = response.json()
    address_lat_lon = resp_json_payload['results'][0]['geometry']['location']
    print(address_lat_lon)    
    data = {'dep_name': order.department.dep_name,
            'address': order.address, 
            'companies' : com_data,
            'address_lat': address_lat_lon['lat'],
            'address_lng': address_lat_lon['lng'],
                    }
    
    if request.method == "POST":
        #save
        return 0 
    
    return render(request, 'payment.html', data)

def proceed_payment(request, order_id):
    return render(request, 'payment2.html')

@login_required
def courier_page(request, username):
    courier = Courier.objects.get(user__username = username)
    declined = courier.declined_order.order_id if courier.declined_order else None
    
    orders = list(Order.objects.filter(~Q(order_id=declined)))
    if len(orders) == 0:
        data = {'courier_name': courier.first_name + ' ' + courier.last_name,
            'courier_company': courier.company_id.company_name,
            'courier_image': courier.photo,
            'courier_rating': courier.rating,
            'order' : 0,
            }
    else:
        order= random.choice(orders)
        data = {'courier_name': courier.first_name + ' ' + courier.last_name,
                'courier_company': courier.company_id.company_name,
                'courier_image': courier.photo,
                'courier_rating': courier.rating,
                'order_time': order.date,
                'order_address': order.address,
                'order_id': order.order_id,
                'order_department': order.department.dep_name,
                'order_description': order.description,
                'order_client': capitalizeFirstLetter(order.client.first_name) + ' ' + capitalizeFirstLetter(order.client.last_name),
                'order_dep_address': order.department.address,
                'order' : 1,
                }
    if request.method == "POST":
        if "decline" in request.POST:
            courier.declined_order = order
            courier.save()
            return HttpResponseRedirect(reverse('courier', args=(username,)))
        elif "accept" in request.POST:
            courier.status = "B"
            courier.save()
            order.status = "Waiting for courier"
            order.save()
            return render(request, 'courier_continue.html', data)
        elif "get_code" in request.POST:
            code = random.randrange(1000, 9999)
            phone = get_phone_number(courier.user.IIN)
            send_sms(phone, code)
            
            return render(request, 'courier_continue.html', data)
        
    return render(request, 'courier.html', data)
    

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
            
            if Courier.objects.filter(user__username = username).exists():
                return HttpResponseRedirect(reverse('courier', args = [username]))
            elif Employee.objects.filter(user__username = username).exists():
                return HttpResponseRedirect(reverse('employee_page', args = [username]))
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

