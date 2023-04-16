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

        if order.client.IIN == iin:
            return redirect('order', order_id = order_number)
            
        return JsonResponse(client_info)
   
    return render(request, 'home.html')


def construct_order(request, order_id):
    order = Order.objects.get(order_id = order_id)
    if order.status == "In progress":
        if request.method == "POST":
            return redirect('code_final', order_id = order_id)
        return render(request, 'client_generate.html')
    else:
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
            trustee = request.POST.get('trustee', None)
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

def code_final(request, order_id):
    order = Order.objects.get(order_id = order_id)
    code = random.randrange(1000, 9999)
    phone = get_phone_number(order.courier.IIN)
    send_sms(phone, code)
    data = {
        'code' : code,
    }
    order.client.code = code
    order.client.save()
    return render(request, 'client_generate.html', data)

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
    
    address_map = order.address.house_number + ', ' + order.address.street_name + ', ' + order.address.city+ ', ' + 'Kazakhstan'
    response = requests.get(f'https://maps.googleapis.com/maps/api/geocode/json?address={address_map}&key=AIzaSyAd0kKAY8yNMxSL0847Lf7rUexclIDQT10')
    resp_json_payload = response.json()
    address_lat_lon = resp_json_payload['results'][0]['geometry']['location'] 
    
    dep_address = order.department.address.house_number + ', ' + order.department.address.street_name + ', ' +order.department.address.city+ ', ' + 'Kazakhstan'
    response = requests.get(f'https://maps.googleapis.com/maps/api/geocode/json?address={dep_address}&key=AIzaSyAd0kKAY8yNMxSL0847Lf7rUexclIDQT10')
    resp_json_payload = response.json()
    address_dep_lat_lon = resp_json_payload['results'][0]['geometry']['location'] 
    data = {'dep_name': order.department.dep_name,
            'address': order.address, 
            'companies' : com_data,
            'address_lat': address_lat_lon['lat'],
            'address_lng': address_lat_lon['lng'],
            'address_dep_lat': address_dep_lat_lon['lat'],
            'address_dep_lng': address_dep_lat_lon['lng'],
            'address_dep': dep_address,
            'address_map': address_map,
                    }
    
    
    if request.method == "POST":
        print(request.POST)
        if 'pay' in request.POST:
            order.status = "Waiting for courier"
            comp = Company.objects.get(company_name = "Yandex.Taxi")
            order.company_courier = comp
            order.save()
            return redirect('proceed_payment', order_id = order.order_id)
    
    return render(request, 'payment.html', data)

def proceed_payment(request, order_id):
    if request.method == "POST":
        order = Order.objects.get(order_id = order_id)
        order.status = "Waiting for courier"
        order.save()
        return redirect('home')
    return render(request, 'payment2.html')

@login_required
def courier_page(request, username):
    courier = Courier.objects.get(user__username = username)
    declined = courier.declined_order.order_id if courier.declined_order else None
    five_range = [0,1,2,3,4]
    orders = list(Order.objects.filter(~Q(order_id=declined, status = "Delivered") ))
    if len(orders) == 0:
        data = {'courier_name': courier.first_name + ' ' + courier.last_name,
            'courier_company': courier.company_id.company_name,
            'courier_image': courier.photo,
            'courier_rating': courier.rating,
            'order' : 0,
            'range' :five_range,
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
                'range' :five_range,
                'trustee': order.trustee,
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
            code = random.randrange(1000, 9999)
            phone = get_phone_number(courier.IIN)
            send_sms(phone, code)
            courier.code = code
            return render(request, 'courier_continue.html', data)
        elif "stop" in request.POST:
            return render(request, 'courier3.html', data)
        elif "confirm" in request.POST:
            print(f"{request.POST['code']}, {order.client.code}")
            if str(order.client.code) == str(request.POST['code']):
                order.status = 'Delivered'
                order.save()
                return render(request, 'courier.html', data)
            else:
                return render(request, 'courier.html', {'error': 'Wrong code'})
        
    return render(request, 'courier.html', data)

    
@login_required
def employee_page(request, username):
    employee = Employee.objects.get(user__username = username)
    orders = Order.objects.filter(department__dep_name = employee.department_id.dep_name, status = "Not ready").order_by('date')
    
    order_info = []
    orders_by_order_id = []
    for order in orders:
        temp = {'order_num': order.order_id, 'client_name': capitalizeFirstLetter(order.client.first_name) + ' ' + capitalizeFirstLetter(order.client.last_name), 
                'description': order.description, 'date': order.date}
        orders_by_order_id.append(order.order_id)
        order_info.append(temp)
    data ={
        'orders' : order_info,
        'em_name' : employee.first_name + ' ' +employee.last_name,
        'em_dep' : employee.department_id.dep_name,
        'dep_address' : employee.department_id.address,
        'user' : username,
    }
    
    if request.method == "POST":
        if "Give" in request.POST:
            sms = f"Сіздің #{order.order_id} құжатыңыз дайын. http://127.0.0.1:8000/order/order.order_id адреса доставки/ сілтемесін басу арқылы құжатты жеткізуді пайдалана аласыз. Құжатты жеткізу курьерлік қызметтің жеткізу мерзімдеріне сәйкес жүзеге асырылады. Ваш документ #{order.order_id} готов. Можете воспользоваться доставкой документа следуя по ссылке http://127.0.0.1:8000/order/order.order_id адреса доставки/ Доставка осуществляется в соответствии со сроками доставки курьерской службы"
            phone = get_phone_number(order.client.IIN)
            send_sms(phone, sms)
            return render(request, 'tson_cont.html' )
        
        
    return render(request, 'tson.html', data)

@login_required
def employee_page_cont(request, username, order_id):
    employee = Employee.objects.get(user__username = username)
    orders = Order.objects.get(order_id = order_id)
    data ={
        'order_client' : capitalizeFirstLetter(orders.client.first_name) + ' ' + capitalizeFirstLetter(orders.client.last_name),
        'trustee' : orders.trustee,
        'order_desc' : orders.description,
        'order_date' : orders.date,
        'user' : username,
        'order_courier' : orders.courier,
        'order_comp' : orders.courier.company_id.company_name,
        'order_id' : orders.order_id,
        'em_name' : employee.first_name + ' ' +employee.last_name,
        'em_dep' : employee.department_id.dep_name,
        'dep_address' : employee.department_id.address,
    }
    if request.POST:
        code = request.POST['code']
        right_code = orders.courier.code
        if code == right_code:
            orders.status = "In progress"
            orders.save()
            return render(request, 'tson.html', data)
    
        
    return render(request, 'tson_cont.html', data )


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
            return render(request, 'login.html', {
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

