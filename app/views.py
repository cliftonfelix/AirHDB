from email import message
from pstats import Stats
from django.db import connection
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from datetime import datetime
from datetime import timedelta
import requests

api_key = "AIzaSyCfbRJX3HAzw1mb4ZwHsQCOf4XES8h0eFU"

def login_page(request):
    if request.user.is_authenticated:
        email = request.user.username

        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE email_address = %s", [email])
            row = cursor.fetchone()

            if row[3] == 'Yes':
                return redirect('adminunits')

            elif row[3] == 'No':
                return redirect('listings')

    context = {"current_email": "", "current_password": ""}

    if request.method == 'POST':
        email = request.POST.get('email').lower()
        password = request.POST.get('password')
        context["current_email"] = email
        context["current_password"] = password

        try:
            user = User.objects.get(username = email)
        except:
            messages.error(request, 'Invalid email address!')
            return render(request, 'app/login.html', context)

        user = authenticate(request, username = email, password = password)
        if user is not None:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE email_address = %s", [email])
                row = cursor.fetchone()
                login(request, user)

            if row[3] == 'Yes':
                return redirect('adminunits')

            elif row[3] == 'No':
                return redirect('listings')

        else:
            messages.error(request, 'Wrong password entered!')
            return render(request, 'app/login.html', context)

    return render(request, 'app/login.html', context)

def logout_page(request):
    logout(request)
    return redirect('login')

def register_page(request):
    context = {'name': '', 'number': '', 'email': '', 'password': '', 'confirm_password': ''}
    if request.method == 'POST':
        
        name = request.POST.get('name')
        number = request.POST.get('number')
        email = request.POST.get('email').lower()
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        context['name'] = name
        context['number'] = number
        context['email'] = email
        context['password'] = password
        context['confirm_password'] = confirm_password

        if password != confirm_password:
            messages.error(request, 'Passwords do not match!')
            return render(request, 'app/register.html', context)

        with connection.cursor() as cursor:
            try:
                cursor.execute("INSERT INTO users VALUES (%s, %s, %s)", [name, email, number])
            except Exception as e:
                string = str(e)
                message = ""
                if 'duplicate key value violates unique constraint "users_pkey"' in string:
                    message = 'The email has already been used by another user!'
                elif 'new row for relation "users" violates check constraint "users_email_address_check"' in string:
                    message = 'Please enter a valid email address!'
                elif 'new row for relation "users" violates check constraint "users_mobile_number_check"' in string:
                    message = 'Please enter a valid Singapore number!'
                elif 'out of range for type integer' in string:
                    message = 'Please enter a valid Singapore number!'
                messages.error(request, message)
                return render(request, 'app/register.html', context)

            user = User.objects.create_user(email, password = password)
            user.save()
            messages.success(request, 'Account has been successfully registered!')
            return redirect('login')
    return render(request, 'app/register.html', context)
    
@login_required(login_url = 'login')
def listings(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT DISTINCT town, 'No' FROM towns ORDER BY town")
        towns = cursor.fetchall()

        cursor.execute("SELECT DISTINCT region, 'No' FROM towns ORDER BY region")
        regions = cursor.fetchall()

        cursor.execute("SELECT DISTINCT mrt_name, 'No' FROM mrt_stations ORDER BY mrt_name")
        mrt_stations = cursor.fetchall()

        cursor.execute("SELECT DISTINCT hdb_type, 'No' FROM hdb_types_info ORDER BY hdb_type")
        hdb_types = cursor.fetchall()

    result_dict = {'towns': towns, 'regions': regions, 'mrt_stations': mrt_stations, 'hdb_types': hdb_types}
    result_dict['start_date'] = ''
    result_dict['end_date'] = ''
    result_dict['num_guests'] = ''
    result_dict['min_price_per_day'] = ''
    result_dict['max_price_per_day'] = ''
    result_dict['min_size'] = ''
    result_dict['max_size'] = ''
    result_dict['num_bedrooms'] = [('1', 'No'), ('2', 'No'), ('3', 'No'), ('4', 'No')]
    result_dict['num_bathrooms'] = [('1', 'No'), ('2', 'No'), ('3', 'No')]
    result_dict['nearest_mrt_dist'] = [("< 100 m", 'No'), ("100 - 250 m", 'No'), ("250 m - 1 km", 'No'), ("1 - 2 km", 'No'), ("> 2 km", 'No')]
    result_dict['search_by_address'] = ''

    if request.method == "POST":
        result = ""
        sqlquery = "SELECT * FROM hdb_listings hl1"

        #START AND END DATE FILTER
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        if start_date and not end_date:
            end_date = (datetime.strptime(start_date, '%Y-%m-%d') + timedelta(days = 1)).strftime("%Y-%m-%d")

        elif not start_date and end_date:
            start_date = (datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days = 1)).strftime("%Y-%m-%d")
            
        if start_date and end_date: #TODO: if only start_date filled in then show end_date to be start + 1 and vice versa
            result_dict['start_date'] = start_date
            result_dict['end_date'] = end_date
            result += """({0}
                          WHERE NOT EXISTS (SELECT *
                          FROM bookings b1
                          WHERE hl1.hdb_id = b1.hdb_id AND
                                (('{1}' :: DATE BETWEEN b1.start_date AND b1.end_date - 1 OR
                                '{2}' :: DATE - 1 BETWEEN b1.start_date AND b1.end_date - 1) OR
                                (b1.start_date BETWEEN '{1}' :: DATE AND '{2}' :: DATE - 1 OR
                                b1.end_date - 1 BETWEEN '{1}' :: DATE AND '{2}' :: DATE - 1))))""".format(sqlquery, start_date, end_date)

            
        #NUMBER OF GUESTS FILTER
        num_guests = request.POST.get('num_guests')
        if num_guests:
            result_dict['num_guests'] = num_guests
            temp = """{0} 
                       WHERE hl1.max_occupants >= {1}""".format(sqlquery, num_guests)
            if result:
                result += " INTERSECT "
            result += "({})".format(temp)

        #MIN AND MAX PRICE FILTER
        min_price_per_day = request.POST.get('min_price_per_day')
        max_price_per_day = request.POST.get('max_price_per_day')
        temp = ""

        if min_price_per_day:
            result_dict['min_price_per_day'] = min_price_per_day
            temp = "{} WHERE hl1.price_per_day >= {}".format(sqlquery, min_price_per_day)

        if max_price_per_day:
            result_dict['max_price_per_day'] = max_price_per_day
            if not temp:
                temp = "{} WHERE hl1.price_per_day <= {}".format(sqlquery, max_price_per_day)
            else:
                temp += " INTERSECT {} WHERE hl1.price_per_day <= {}".format(sqlquery, max_price_per_day)

        if temp:
            if result:
                result += " INTERSECT "
            result += "({})".format(temp)
            
        #REGION FILTER
        regions = request.POST.getlist('regions')

        if regions:
            temp = ""
            for region in regions:
                regions_temp = result_dict["regions"]
                for i in range(len(regions_temp)):
                    if regions_temp[i][0] == region:
                        result_dict["regions"][i] = (region, 'Yes')
                        
                if temp:
                    temp += " UNION "
                temp += """{0} 
			   WHERE hl1.region = '{1}'""".format(sqlquery, region)

            if temp:
                if result:
                    result += " INTERSECT "
                result += "({})".format(temp)
				
	#TOWN FILTER
        towns = request.POST.getlist('towns')

        if towns:
            temp = ""
            for town in towns:
                towns_temp = result_dict["towns"]
                for i in range(len(towns_temp)):
                    if towns_temp[i][0] == town:
                        result_dict["towns"][i] = (town, 'Yes')
                        
                if temp:
                    temp += " UNION "
                temp += """{0} 
			   WHERE hl1.town = '{1}'""".format(sqlquery, town)

            if temp:
                if result:
                    result += " INTERSECT "
                result += "({})".format(temp)
				
	#HDB TYPE FILTER
        hdb_types = request.POST.getlist('hdb_types')

        if hdb_types:
            temp = ""
            for hdb_type in hdb_types:
                hdb_types_temp = result_dict["hdb_types"]
                for i in range(len(hdb_types_temp)):
                    if hdb_types_temp[i][0] == hdb_type:
                        result_dict["hdb_types"][i] = (hdb_type, 'Yes')
                
                if temp:
                    temp += " UNION "
                temp += """{0} 
			   WHERE hl1.hdb_type = '{1}'""".format(sqlquery, hdb_type)

            if temp:
                if result:
                    result += " INTERSECT "
                result += "({})".format(temp)
				
	#SIZE FILTER
        min_size = request.POST.get('min_size')
        max_size = request.POST.get('max_size')
        temp = ""

        if min_size:
            result_dict['min_size'] = min_size
            temp = "{} WHERE hl1.size >= {}".format(sqlquery, min_size)

        if max_size:
            result_dict['max_size'] = max_size
            if not temp:
                temp = "{} WHERE hl1.size <= {}".format(sqlquery, max_size)
            else:
                temp += " INTERSECT {} WHERE hl1.size <= {}".format(sqlquery, max_size)

        if temp:
            if result:
                result += " INTERSECT "
            result += "({})".format(temp)
			
	#NUM BEDROOMS FILTER
        num_bedrooms = request.POST.getlist('num_bedrooms')
        if num_bedrooms:
            temp = ""
            for bedroom in num_bedrooms:
                num_bedrooms_temp = result_dict["num_bedrooms"]
                for i in range(len(num_bedrooms_temp)):
                    if num_bedrooms_temp[i][0] == bedroom:
                        result_dict["num_bedrooms"][i] = (bedroom, 'Yes')
                
                if temp:
                    temp += " UNION "
                temp += """{0} 
			   WHERE hl1.number_of_bedrooms = {1}""".format(sqlquery, bedroom)

            if temp:
                if result:
                    result += " INTERSECT "
                result += "({})".format(temp)
			
	#NUM BATHROOMS FILTER
        num_bathrooms = request.POST.getlist('num_bathrooms')
        if num_bathrooms:
            temp = ""
            for bathroom in num_bathrooms:
                num_bathrooms_temp = result_dict["num_bathrooms"]
                for i in range(len(num_bathrooms_temp)):
                    if num_bathrooms_temp[i][0] == bathroom:
                        result_dict["num_bathrooms"][i] = (bathroom, 'Yes')
                
                if temp:
                    temp += " UNION "
                temp += """{0} 
			   WHERE hl1.number_of_bathrooms = {1}""".format(sqlquery, bathroom)

            if temp:
                if result:
                    result += " INTERSECT "
                result += "({})".format(temp)
			
	#NEAREST MRT FILTER
        nearest_mrts = request.POST.getlist('nearest_mrts')

        if nearest_mrts:
            temp = ""
            for nearest_mrt in nearest_mrts:
                nearest_mrts_temp = result_dict["mrt_stations"]
                for i in range(len(nearest_mrts_temp)):
                    if nearest_mrts_temp[i][0] == nearest_mrt:
                        result_dict["mrt_stations"][i] = (nearest_mrt, 'Yes')
                        
                if temp:
                    temp += " UNION "
                temp += """{0} 
			   WHERE hl1.nearest_mrt = '{1}'""".format(sqlquery, nearest_mrt)

            if temp:
                if result:
                    result += " INTERSECT "
                result += "({})".format(temp)
				
	#NEAREST MRT DISTANCE FILTER
        nearest_mrt_dists = request.POST.getlist('nearest_mrt_dists')
        if nearest_mrt_dists:
            temp = ""
            if "< 100 m" in nearest_mrt_dists:
                result_dict['nearest_mrt_dist'][0] = ("< 100 m", "Yes")
                temp += """{0} 
			   WHERE hl1.nearest_mrt_distance < 0.1""".format(sqlquery)

            if "100 - 250 m" in nearest_mrt_dists:
                result_dict['nearest_mrt_dist'][1] = ("100 - 250 m", "Yes")
                if temp:
                    temp += " UNION "
                temp += """{0} 
			   WHERE hl1.nearest_mrt_distance BETWEEN 0.1 AND 0.25""".format(sqlquery)
				
            if "250 m - 1 km" in nearest_mrt_dists:
                result_dict['nearest_mrt_dist'][2] = ("250 m - 1 km", "Yes")
                if temp:
                    temp += " UNION "
                temp += """{0} 
                           WHERE hl1.nearest_mrt_distance BETWEEN 0.25 AND 1""".format(sqlquery)

            if "1 - 2 km" in nearest_mrt_dists:
                result_dict['nearest_mrt_dist'][3] = ("1 - 2 km", "Yes")
                if temp:
                    temp += " UNION "
                temp += """{0} 
                           WHERE hl1.nearest_mrt_distance BETWEEN 1 AND 2""".format(sqlquery)

            if "> 2 km" in nearest_mrt_dists:
                result_dict['nearest_mrt_dist'][4] = ("> 2 km", "Yes")
                if temp:
                    temp += " UNION "
                temp += """{0} 
			   WHERE hl1.nearest_mrt_distance > 2""".format(sqlquery)

            if temp:
                if result:
                    result += " INTERSECT "
                result += "({})".format(temp)

        search_by_address = request.POST.get('search_by_address')
        result_dict["search_by_address"] = search_by_address
        address_exists = False
        address_correct = False

        def get_coordinates(address):
            response = requests.get('https://maps.googleapis.com/maps/api/geocode/json?address=' + address, params = {"key": api_key})
            resp_json_payload = response.json()
            return resp_json_payload['results'][0]['geometry']['location']["lat"], resp_json_payload['results'][0]['geometry']['location']["lng"]

        if search_by_address:
            try:
                address_lat, address_long = get_coordinates(search_by_address)
                address_exists = True

                if address_lat <= 1.472 and address_lat >= 1.158 and address_long <= 104.1 and address_long >= 103.6:
                    address_correct = True
                else:
                    messages.error(request, "The address is not a Singapore address. Please input a Singapore address and reapply the filter")
                    
            except:
                messages.error(request, "The address is not recognized by Google Maps. Please input a valid address and reapply the filter")

        if not address_exists or not address_correct:
            with connection.cursor() as cursor:
                if result:
                    result = "SELECT *, '-' FROM ({}) temp ORDER BY temp.hdb_id".format(result)
                    cursor.execute(result)
                    
                else:
                    cursor.execute("SELECT *, '-' FROM hdb_listings")
                    
                listings = cursor.fetchall()
                
        else:
            with connection.cursor() as cursor:
                if result:
                    result = """SELECT *, ROUND(get_distance(temp.hdb_lat, temp.hdb_long, {}, {}), 2) dist FROM ({}) temp ORDER BY dist""".format(address_lat, address_long, result)
                    cursor.execute(result)
                    
                else:
                    cursor.execute("SELECT *, ROUND(get_distance(hdb_listings.hdb_lat, hdb_listings.hdb_long, {}, {}), 2) dist FROM hdb_listings ORDER BY dist".format(address_lat, address_long))
                    
                listings = cursor.fetchall()

        result_dict['listings'] = listings

        return render(request, 'app/listings.html', result_dict)

    with connection.cursor() as cursor:
        cursor.execute("SELECT *, '-' FROM hdb_listings")
        listings = cursor.fetchall()

    result_dict['listings'] = listings

    return render(request, 'app/listings.html', result_dict)

@login_required(login_url = 'login')
def adminu(request):
    status = ''

    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM hdb_units hu1 ORDER BY hu1.hdb_id")
        units = cursor.fetchall()

    result_dict = {'records': units}
    result_dict['status'] = status
    
    return render(request,'app/adminunits.html',result_dict)

@login_required(login_url = 'login')
def adminb(request):
    if request.POST:
        if request.POST['action'] == 'delete':
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM bookings WHERE booking_id = %s", [request.POST['id']])
 
    with connection.cursor() as cursor:
        cursor.execute("SELECT b.booking_id, b.hdb_id, h.hdb_address, h.hdb_unit_number, b.booked_by, b.start_date, b.end_date, b.credit_card_type, b.credit_card_number, b.total_price\
		       FROM bookings b, hdb_units h WHERE b.hdb_id = h.hdb_id ORDER BY b.booking_id")
        bookings = cursor.fetchall()

    booking_dict = {'bookings':bookings}

    return render(request,'app/adminbookings.html',booking_dict)

@login_required(login_url = 'login')
def adminm(request):
    status = ''

    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM mrt_stations mrt1 ORDER BY mrt1.mrt_name")
        stations = cursor.fetchall()

    result_dict = {'stations': stations}
    result_dict['status'] = status

    return render(request,'app/adminmrts.html',result_dict)

@login_required(login_url = 'login')
def addmrt(request):
    """Shows the main page"""
    context = {}
    status = ''

    context['mrt_name'] = ''
    context['lat'] = ''
    context['long'] = ''
    
    if request.POST:
        context['mrt_name'] = request.POST.get('mrt_name').capitalize()
        context['lat'] = request.POST['latitude']
        context['long'] = request.POST.get('longitude')

        ## Check if customerid is already in the table
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM mrt_stations WHERE mrt_name = %s or (mrt_lat = %s and mrt_long =%s)", [request.POST['mrt_name'].capitalize(),request.POST['latitude'],request.POST['longitude']])
            mrt = cursor.fetchone()
            ## No customer with same id
            if mrt == None:
                ##TODO: date validation
                try:
                    cursor.execute("INSERT INTO mrt_stations(mrt_name,mrt_lat,mrt_long) VALUES (%s, %s, %s)"
                            , [request.POST['mrt_name'].capitalize(), request.POST['latitude'], request.POST['longitude']])
                            
                    messages.success(request, '%s station has been successfully added!'% (request.POST['mrt_name'].capitalize()))
                    return redirect('adminmrts')
                   
                except Exception as e:
                    message = str(e)
                    if '"mrt_stations" violates check constraint "mrt_stations_mrt_lat_check"' in message:
                        status ='%s Station latitude out of range for Singapore'%(request.POST['mrt_name'].capitalize())
                    elif '"mrt_stations" violates check constraint "mrt_stations_mrt_long_check"' in message:
                        status ='%s Station longitude out of range for Singapore'%(request.POST['mrt_name'].capitalize())

                    else:
                        status = message
            else:
                status = '%s already exists' % (request.POST['mrt_name'].capitalize())

    context['status'] = status
 
    return render(request, "app/adminaddmrt.html", context)

@login_required(login_url = 'login')
def viewunits(request,id):
    ## Use raw query to get a customer
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM hdb_units WHERE hdb_id = %s", [id])
        unit = cursor.fetchone()
	
    result_dict = {'unit': unit}

    return render(request,'app/viewunits.html',result_dict)

@login_required(login_url = 'login')
def viewbookings(request,id):
    ## Use raw query to get a customer
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM bookings WHERE booking_id = %s", [id])
        booking = cursor.fetchone()
    result_dict = {'booking': booking}

    return render(request,'app/viewbookings.html',result_dict)

@login_required(login_url = 'login')
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

@login_required(login_url = 'login')
def editbookings(request, id):
    """Shows the main page"""

    # dictionary for initial data with
    # field names as keys
    context ={}
    context['startdate'] = ''
    context['enddate'] = ''

    # fetch the object related to passed id
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM bookings WHERE booking_id = %s", [id])
        obj = cursor.fetchone()

    status = ''
    # save the data from the form

    if request.POST:
        ##TODO: date validation
        with connection.cursor() as cursor:
            context['startdate'] = request.POST.get('start_date')
            context['enddate'] = request.POST.get('end_date')

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

@login_required(login_url = 'login')
def adminaddunits(request):
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
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM hdb_types_info")
        types = cursor.fetchall()
        
    context['hdb_types'] = types
    context['towns'] = towns
    context['towns_default'] = ''
    context['type'] = ''
    context['address'] = ''
    context['unit'] =''
    context['size'] =''
    context['price'] = ''
    context['name'] = ''
    context['number'] = ''
    context['ans'] = ''

    if request.POST:
        context['towns_default'] = request.POST.get('town')
        context['address'] = request.POST['hdb_address'].upper()
        context['unit'] = request.POST.get('hdb_unit_number')
        context['size'] = request.POST.get('size')
        context['price'] = request.POST.get('price_per_day')
        context['name'] = request.POST.get('contact_person_name')
        context['number'] = request.POST.get('contact_person_mobile')
        context['type'] = request.POST.get('hdb_type')
        context['ans'] = request.POST.get('multistorey_carpark')

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
                    
                    messages.success(request, '%s %s has been successfully added!'% (request.POST['hdb_address'].upper(),request.POST['hdb_unit_number']))
                    return redirect('adminunits')
                   
                except Exception as e:
                    message = str(e)
                    if 'violates check constraint "hdb_units_check"' in message:
                        if request.POST['hdb_type'] == "2-Room/2-Room Flexi":
                            status = 'The size of a 2-Room/2-Room Flexi should be between 35 and 38 or size between 45 and 47'
                        elif request.POST['hdb_type'] == '3-Room':
                            status = 'The size of a 3-Room should be between 60 and 68'
                        elif request.POST['hdb_type'] == '4-Room':
                            status = 'The size of a 4-Room should be between 85 and 93'
                        elif request.POST['hdb_type'] == '5-Room':
                            status = 'The size of a 5-Room should be between 107 and 113'
                        elif request.POST['hdb_type'] == '3-Gen':
                            status = 'The size of a 3-Gen should be between 115 and 118'
                    elif 'violates check constraint "hdb_units_contact_person_mobile_check"' in message:
                        status = 'Please input a valid Singapore Number'

                    elif 'violates check constraint "hdb_units_hdb_lat_check"' in message:
                        status = 'Please input a valid Singapore Address'
                    elif 'violates check constraint "hdb_units_hdb_unit_number_check"' in message:
                        status = 'Please input unit number in this format:"#_-_" '
                    elif message == 'list index out of range':
                        status = 'Please input a valid Singapore Address'
                    elif 'violates unique constraint "hdb_units_hdb_address_hdb_unit_number_key"' in message:
                        status = '%s %s already exists' % (request.POST['hdb_address'].upper(),request.POST['hdb_unit_number'])

                    
                    else:
                        status = message

            else:
                status = '%s %s already exists' % (request.POST['hdb_address'].upper(),request.POST['hdb_unit_number'])

    context['status'] = status
 
    return render(request, "app/adminunitsadd.html", context)

@login_required(login_url = 'login')
def useraddunits(request):
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
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM hdb_types_info")
        types = cursor.fetchall()
        
    context['hdb_types'] = types
    context['towns'] = towns
    context['towns_default'] = ''
    context['type'] = ''
    context['address'] = ''
    context['unit'] =''
    context['size'] =''
    context['price'] = ''
    context['name'] = ''
    context['number'] = ''
    context['ans'] = ''

    if request.POST:
        context['towns_default'] = request.POST.get('town')
        context['address'] = request.POST['hdb_address'].upper()
        context['unit'] = request.POST.get('hdb_unit_number')
        context['size'] = request.POST.get('size')
        context['price'] = request.POST.get('price_per_day')
        context['name'] = request.POST.get('contact_person_name')
        context['number'] = request.POST.get('contact_person_mobile')
        context['type'] = request.POST.get('hdb_type')
        context['ans'] = request.POST.get('multistorey_carpark')

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
                    
                    messages.success(request, '%s %s has been successfully added!'% (request.POST['hdb_address'].upper(),request.POST['hdb_unit_number']))
                    return redirect('listings')
                   
                except Exception as e:
                    message = str(e)
                    if 'violates check constraint "hdb_units_check"' in message:
                        if request.POST['hdb_type'] == "2-Room/2-Room Flexi":
                            status = 'The size of a 2-Room/2-Room Flexi should be between 35 and 38 or size between 45 and 47'
                        elif request.POST['hdb_type'] == '3-Room':
                            status = 'The size of a 3-Room should be between 60 and 68'
                        elif request.POST['hdb_type'] == '4-Room':
                            status = 'The size of a 4-Room should be between 85 and 93'
                        elif request.POST['hdb_type'] == '5-Room':
                            status = 'The size of a 5-Room should be between 107 and 113'
                        elif request.POST['hdb_type'] == '3-Gen':
                            status = 'The size of a 3-Gen should be between 115 and 118'
                    elif 'violates check constraint "hdb_units_contact_person_mobile_check"' in message:
                        status = 'Please input a valid Singapore Number'

                    elif 'violates check constraint "hdb_units_hdb_lat_check"' in message:
                        status = 'Please input a valid Singapore Address'
                    elif 'violates check constraint "hdb_units_hdb_unit_number_check"' in message:
                        status = 'Please input unit number in this format:"#_-_" '
                    elif message == 'list index out of range':
                        status = 'Please input a valid Singapore Address'
                    elif 'violates unique constraint "hdb_units_hdb_address_hdb_unit_number_key"' in message:
                        status = '%s %s already exists' % (request.POST['hdb_address'].upper(),request.POST['hdb_unit_number'])

                    
                    else:
                        status = message

            else:
                status = '%s %s already exists' % (request.POST['hdb_address'].upper(),request.POST['hdb_unit_number'])

    context['status'] = status
 
    return render(request, "app/userunitsadd.html", context)



@login_required(login_url = 'login')
def profile(request):
    email = request.user.username
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE email_address = %s", [email])
        row = cursor.fetchone()
    context = {'name': row[0], 'email': email, 'number': row[2]}
    return render(request, 'app/profile.html', context)

@login_required(login_url = 'login')
def change_profile(request):
    email = request.user.username
    
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE email_address = %s", [email])
        row = cursor.fetchone()
    context = {'old_name': row[0], 'old_number': row[2]}

    if request.method == 'POST':
        name = request.POST.get('name')
        number = request.POST.get('number')
        context['old_name'] = name
        context['old_number'] = number
	
        if name == row[0] and number == str(row[2]):
            messages.error(request, 'New profile is identical to the old one!') 
            return render(request, 'app/change_profile.html', context)
	
        with connection.cursor() as cursor:
            try:
                cursor.execute("UPDATE users SET name = %s, mobile_number = %s WHERE email_address = %s", [name, number, email])
		
            except Exception as e:
                string = str(e)
                message = ""
		
                if 'new row for relation "users" violates check constraint "users_mobile_number_check"' in string:
                    message = 'Please enter a valid Singapore number!'
		
                elif 'out of range for type integer' in string:
                    message = 'Please enter a valid Singapore number!'
		
                messages.error(request, message) 
                return render(request, 'app/change_profile.html', context)
	
            messages.success(request, 'Profile has been successfully updated!')
            return redirect('profile')    

    return render(request, 'app/change_profile.html', context)

@login_required(login_url = 'login')
def change_password(request):
    email = request.user.username
    user = User.objects.get(username = email)
    context = {'old_password': '', 'new_password': '', 'confirm_new_password': ''}

    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_new_password = request.POST.get('confirm_new_password')
	
        context['old_password'] = old_password
        context['new_password'] = new_password
        context['confirm_new_password'] = confirm_new_password
	
        if not user.check_password(old_password):
            messages.error(request, 'Old password entered is incorrect')
            return render(request, 'app/change_password.html', context)
	
        elif new_password != confirm_new_password:
            messages.error(request, 'Passwords do not match!')
            return render(request, 'app/change_password.html', context)
	
        user.set_password(new_password)
        user.save()
        login(request, user)
        messages.success(request, 'Password has been successfully updated!')  
	
    return render(request, 'app/change_password.html', context)

@login_required(login_url = 'login')
def user_bookings(request):
    email = request.user.username
    current_date = date.today()
    format_date = current_date.strftime("%B %d, %Y")

    with connection.cursor() as cursor:
        cursor.execute("SELECT b.booking_id, b.hdb_id, h.hdb_address, h.hdb_unit_number, b.start_date, b.end_date, b.credit_card_type, b.credit_card_number, b.total_price\
		       FROM bookings b, hdb_units h WHERE b.hdb_id = h.hdb_id AND b.end_date < format_date AND booked_by = %s ORDER BY b.booking_id", [email])
        past_bookings = cursor.fetchall()

    with connection.cursor() as cursor:
        cursor.execute("SELECT b.booking_id, b.hdb_id, h.hdb_address, h.hdb_unit_number, b.start_date, b.end_date, b.credit_card_type, b.credit_card_number, b.total_price\
		       FROM bookings b, hdb_units h WHERE b.hdb_id = h.hdb_id AND b.start_date > format_date AND booked_by = %s ORDER BY b.booking_id", [email])
        upcoming_bookings = cursor.fetchall()	
	
    context = {}
    context['past_bookings'] = past_bookings
    context['upcoming_bookings'] = upcoming_bookings
    return render(request, 'app/userbookings.html', context)


@login_required(login_url = 'login')
def book(request, id):
    email = request.user.username
    context = {}
    context["start_date"] = ""
    context["end_date"] = ""

    with connection.cursor() as cursor:
        cursor.execute("SELECT hu1.hdb_address, hu1.hdb_unit_number, hu1.price_per_day FROM hdb_units hu1 WHERE hu1.hdb_id = %s", [id])
        row = cursor.fetchone()

    context["hdb_id"] = id
    context["hdb_address"] = row[0]
    context["hdb_unit_number"] = row[1]
    context["booked_by"] = email
    request.session["hdb_id"] = id
    request.session["hdb_address"] = row[0]
    request.session["hdb_unit_number"] = row[1]
    

    if request.method == "POST":
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        context["start_date"] = start_date
        context["end_date"] = end_date
        request.session["start_date"] = start_date
        request.session["end_date"] = end_date
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO bookings(hdb_id, booked_by, start_date, end_date, credit_card_type, credit_card_number, total_price)\
                            VALUES ({}, '{}', '{}', '{}', 'mastercard', '2221000000000000', 0)".format(id, email, start_date, end_date))
                cursor.execute("DELETE FROM bookings WHERE hdb_id = %s AND booked_by = %s AND start_date = %s AND end_date = %s", [id, email, start_date, end_date])
            
        except Exception as e:
            error = str(e)

            if "Booking Dates Not Available" in error:
                messages.error(request, "Selected dates are not available")

            elif 'invalid input syntax' in error:
                messages.error(request, "Please fill in the dates")

            elif 'violates check constraint "bookings_start_date_check"' in error:
                messages.error(request, 'There are no bookings to be made earlier than 2022-04-11, please choose another start date')

            elif 'violates check constraint "bookings_check"' in error:
                messages.error(request, 'Please input a valid start and end date, the start date should be before end date')

            else:
                messages.error(request, error)

            return render(request, "app/book.html", context)

        request.session["total_price"] = str((datetime.strptime(end_date, '%Y-%m-%d') - datetime.strptime(start_date, '%Y-%m-%d')).days * row[2])

        return redirect("payment")

    return render(request, "app/book.html", context)

@login_required(login_url = 'login')
def payment(request):
    email = request.user.username
    context = {}
    
    context["start_date"] = request.session["start_date"]
    context["end_date"] = request.session["end_date"]
    context["hdb_id"] = request.session["hdb_id"]
    context["hdb_address"] = request.session["hdb_address"]
    context["hdb_unit_number"] = request.session["hdb_unit_number"]
    context["booked_by"] = email
    context["total_price"] = request.session["total_price"]
##    context["total_price"] = ""
    context["credit_card_number"] = ""
    context["credit_card_type"] = ""

    if request.method == 'POST':
        start_date = request.session["start_date"]
        end_date = request.session["end_date"]
        hdb_id = request.session["hdb_id"]
        hdb_address = request.session["hdb_address"]
        hdb_unit_number = request.session["hdb_unit_number"]
        card_number = request.POST.get("credit_card_number")
        card_type = request.POST.get("credit_card_type")
        total_price = request.session["total_price"]
        context["start_date"] = start_date
        context["end_date"] = end_date
        context["hdb_id"] = hdb_id
        context["hdb_address"] = hdb_address
        context["hdb_unit_number"] = hdb_unit_number
        context["credit_card_number"] = card_number
        context["credit_card_type"] = card_type
        context["booked_by"] = email
        context["total_price"] = total_price

        if card_type == "Mastercard":
            sql_card_type = "mastercard"
        elif card_type == "VISA":
            sql_card_type = "visa"
        else:
            sql_card_type = "americanexpress"
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO bookings(hdb_id, booked_by, start_date, end_date, credit_card_type, credit_card_number, total_price)\
                                VALUES ({}, '{}', '{}', '{}', '{}', '{}', {})".format(hdb_id, email, start_date, end_date, sql_card_type, card_number, total_price))

        except Exception as e:
            error = str(e)

            if 'new row for relation "bookings" violates check constraint "bookings_check1"' in error:
                if card_type == "Mastercard":
                    messages.error(request, "Please input a valid Mastercard number")
                elif card_type == "VISA":
                    messages.error(request, "Please input a valid VISA card number")
                else:
                    messages.error(request, "Please input a valid American Express card number")
            else:
                messages.error(request, error)
                
            return render(request, "app/payment.html", context)

        messages.success(request, "Successful booking for HDB address {} unit {} from {} to {}".format(hdb_address, hdb_unit_number, start_date, end_date))

        return redirect("listings")

    return render(request, "app/payment.html", context)
