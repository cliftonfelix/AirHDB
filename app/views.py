from email import message
from pstats import Stats
from django.shortcuts import render, redirect
from django.db import connection
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import HttpResponse
import requests

api_key = "AIzaSyCfbRJX3HAzw1mb4ZwHsQCOf4XES8h0eFU"



# Create your views here.
def index(request):
    """Shows the main page"""
    
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM hdb_units")
        units = cursor.fetchall()
        
    result_dict = {'records': units}

    return render(request, 'app/index.html', result_dict)

def login_page(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        try:
            user = User.objects.get(username = username)
        except:
            messages.error(request, 'User does not exist!')
        
        user = authenticate(request, username = username)
        if user is not None:
            login(request, user)
            return redirect('index')

    context = {}
    return render(request, 'app/login.html', context)


def adminu(request):
    status = ''

    if request.POST:
        if request.POST['action'] == 'delete':
            with connection.cursor() as cursor:
                try:
                    cursor.execute("DELETE FROM hdb_units WHERE hdb_id = %s", [request.POST['id']])
                except:
                    status = 'Unit has been booked by a person, you cannot delete it'

    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM hdb_units")
        units = cursor.fetchall()
    
        
    
    result_dict = {'records': units}
    result_dict['status'] = status
    


    return render(request,'app/adminunits.html',result_dict)

def adminb(request):
    

    if request.POST:
        if request.POST['action'] == 'delete':
            with connection.cursor() as cursor:
            
                cursor.execute("DELETE FROM bookings WHERE booking_id = %s", [request.POST['id']])
                


    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM bookings")
        bookings = cursor.fetchall()
        
    
    
    booking_dict = {'bookings':bookings}
    


    return render(request,'app/adminbookings.html',booking_dict)


    
def viewunits(request,id):

    
    
    
    ## Use raw query to get a customer
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM hdb_units WHERE hdb_id = %s", [id])
        unit = cursor.fetchone()
    result_dict = {'unit': unit}

    return render(request,'app/viewunits.html',result_dict)

def viewbookings(request,id):

    
    
    
    ## Use raw query to get a customer
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM bookings WHERE booking_id = %s", [id])
        booking = cursor.fetchone()
    result_dict = {'booking': booking}

    return render(request,'app/viewbookings.html',result_dict)

def editunits(request, id):
    """Shows the main page"""

    # dictionary for initial data with
    # field names as keys
    context ={}

    # fetch the object related to passed id
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM hdb_units WHERE hdb_id = %s", [id])
        obj = cursor.fetchone()

    status = ''
    # save the data from the form

    if request.POST:
        ##TODO: date validation
        with connection.cursor() as cursor:
            try:
                cursor.execute("UPDATE hdb_units SET contact_person_name = %s, contact_person_mobile = %s,can_book = %s WHERE hdb_id = %s"
                    , [request.POST['contact_person'], request.POST['contact_number'],request.POST['can_book'], id ])
                status = 'Customer edited successfully!'
                
            except Exception as e:
                message = str(e)


                if 'violates check constraint "hdb_units_contact_person_mobile_check"' in message:
                    status = 'Unsuccessful , Please enter a valid Singapore Mobile Number'
                elif 'violates check constraint "hdb_units_can_book_check"' in message:
                    status = 'Please input Yes or No for Can Book?'
                else:
                    status = message


            
            cursor.execute("SELECT * FROM hdb_units WHERE hdb_id = %s", [id])
            obj = cursor.fetchone()
            


    context["obj"] = obj
    context["status"] = status
 
    return render(request, "app/editunits.html", context)




def editbookings(request, id):
    """Shows the main page"""

    # dictionary for initial data with
    # field names as keys
    context ={}

    # fetch the object related to passed id
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM bookings WHERE booking_id = %s", [id])
        obj = cursor.fetchone()

    status = ''
    # save the data from the form

    if request.POST:
        ##TODO: date validation
        with connection.cursor() as cursor:
            try:
                cursor.execute("UPDATE bookings SET start_date = %s, end_date = %s WHERE booking_id = %s"
                        , [request.POST['start_date'], request.POST['end_date'], id ])
                status = 'Customer edited successfully!'
                
            except Exception as e:
                message = str(e)

                if 'violates check constraint "bookings_start_date_check"' in message:
                    status = 'There are no bookings to be made earlier than 2022-04-11, please choose another start date'
                elif 'invalid input syntax' in message:
                    status ='Please check your start and end date and follow the format'
                elif 'violates check constraint "bookings_check"' in message:
                    status = 'Please input a valid start and end date, the start date should be before end date'
                elif 'duplicate key value violates unique constraint "bookings_pkey"' in message:
                    status = 'There exists a booking in these dates please choose another start and end date'
                elif 'Booking Dates Not Available' in message:
                    status = 'There exists a booking in these dates please choose another start and end date'
                else:
                    status = message



            
            cursor.execute("SELECT * FROM bookings WHERE booking_id = %s", [id])
            obj = cursor.fetchone()
            


    context["obj"] = obj
    context["status"] = status
 
    return render(request, "app/editbookings.html", context)


def addunits(request):
    """Shows the main page"""
    context = {}
    status = ''
    def get_coordinates(address):
    
        response = requests.get('https://maps.googleapis.com/maps/api/geocode/json?address=' + address, params = {"key": api_key})
        resp_json_payload = response.json()
        return resp_json_payload['results'][0]['geometry']['location']["lat"], resp_json_payload['results'][0]['geometry']['location']["lng"]

    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM towns")
        towns = cursor.fetchall()
        
    
    context['towns'] = towns

    if request.POST:
        ## Check if customerid is already in the table
        with connection.cursor() as cursor:

            cursor.execute("SELECT * FROM hdb_units WHERE hdb_address = %s and hdb_unit_number = %s", [request.POST['hdb_address'],request.POST['hdb_unit_number']])
            customer = cursor.fetchone()
            ## No customer with same id
            if customer == None:
                ##TODO: date validation
                try:
                    cursor.execute("INSERT INTO hdb_units(hdb_address,hdb_unit_number,hdb_type,size,price_per_day,town,multistorey_carpark,contact_person_name,contact_person_mobile,hdb_lat,hdb_long) VALUES (%s, %s, %s, %s, %s, %s, %s,%s, %s,%s, %s)"
                            , [request.POST['hdb_address'].upper(), request.POST['hdb_unit_number'], request.POST['hdb_type'],
                            request.POST['size'] , request.POST['price_per_day'], request.POST['town'], request.POST['multistorey_carpark'],
                            request.POST['contact_person_name'] ,request.POST['contact_person_mobile'] ,get_coordinates(request.POST['hdb_address'])[0],get_coordinates(request.POST['hdb_address'])[1]])
                    return redirect('adminunits')
                except Exception as e:
                    message = str(e)
                    if 'violates check constraint "hdb_units_check"' in message:
                        if request.POST['hdb_type'] == "2-Room/2-Room Flexi":
                            status = 'Please input a size between 35 and 38 or size between 45 and 47'
                        elif request.POST['hdb_type'] == '3-Room':
                            status = 'Please input a size between 60 and 68'
                        elif request.POST['hdb_type'] == '4-Room':
                            status = 'Please input a size between 85 and 93'
                        elif request.POST['hdb_type'] == '5-Room':
                            status = 'Please input a size between 107 and 113'
                        elif request.POST['hdb_type'] == '3-Gen':
                            status = 'Please input a size between 115 and 118'
                    elif 'violates check constraint "hdb_units_contact_person_mobile_check"' in message:
                        status = 'Please input a valid Singapore Number'

                    elif 'violates check constraint "hdb_units_hdb_lat_check"' in message:
                        status = 'Please input a valid Singapore Address'
                    elif 'violates check constraint "hdb_units_hdb_unit_number_check"' in message:
                        status = 'Please input unit number in this format:"#_-_" '
                    elif message == 'list index out of range':
                        status = 'Please input a valid Singapore Address'

                    
                    else:
                        status = message


            else:
                status = 'HDB with ID %s already exists' % (request.POST['hdb_address'])


    context['status'] = status
 
    return render(request, "app/adminunitsadd.html", context)