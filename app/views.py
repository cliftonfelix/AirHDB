from django.db import connection
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

# Create your views here.
def login_page(request):
    if request.user.is_authenticated:
        email = request.user.username
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE email_address = %s", [email])
            row = cursor.fetchone()
            if row[3] == 'Yes':
                return redirect('admin')
            elif row[3] == 'No':
                return redirect('listings')
        
    if request.method == 'POST':
        email = request.POST.get('email').lower()
        password = request.POST.get('password')
        try: 
            user = User.objects.get(username = email)
        except:
            messages.error(request, 'Invalid email address!')
            return render(request, 'app/login.html')  
        user = authenticate(request, username = email, password = password)
        if user is not None:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE email_address = %s", [email])
                row = cursor.fetchone()
                login(request, user)
                if row[3] == 'Yes':
                    return redirect('admin')
                elif row[3] == 'No':
                    return redirect('listings')
        else:
            messages.error(request, 'Wrong password entered!')
            return render(request, 'app/login.html')
    return render(request, 'app/login.html')

def logout_page(request):
    logout(request)
    return redirect('login')

def register_page(request):
    if request.method == 'POST':
        # Ensure password matches confirmation
        name = request.POST.get('name')
        number = request.POST.get('number')
        email = request.POST.get('email').lower()
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match!')
            return render(request, 'app/register.html')
        
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
                messages.error(request, message)
                return render(request, 'app/register.html')
            
            user = User.objects.create_user(email, password = password)
            user.save()
            messages.success(request, 'Account has been successfully registered!')
            return redirect('login')
    return render(request, 'app/register.html')
    
@login_required(login_url = 'login')
def listings(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT DISTINCT town FROM towns ORDER BY town")
        towns = cursor.fetchall()
        
        cursor.execute("SELECT DISTINCT region FROM towns ORDER BY region")
        regions = cursor.fetchall()
        
        cursor.execute("SELECT DISTINCT mrt_name FROM mrt_stations ORDER BY mrt_name")
        mrt_stations = cursor.fetchall()
        
        cursor.execute("SELECT DISTINCT hdb_type FROM hdb_types_info ORDER BY hdb_type")
        hdb_types = cursor.fetchall()
        
    result_dict = {'towns': towns, 'regions': regions, 'mrt_stations': mrt_stations, 'hdb_types': hdb_types}
        
    if request.method == "POST":
        
        result = ""
        sqlquery = "SELECT * FROM hdb_listings hl"
        
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        if start_date is None and end_date is None:
            result += sqlquery 
        else:
            result +=  "(" + sqlquery + ",bookings b WHERE hl.hdb_id NOT IN b.hdb_id AND hl.start_date " + "<" + str(start_date) + " AND hl.end_date < " + str(end_date) +
            " UNION " + sqlquery + ",bookings b WHERE hl.hdb_id NOT IN b.hdb_id AND hl.start_date " + ">" + str(start_date) + " AND hl.end_date > " + str(end_date) + ")"
        
            
        min_price_per_day = request.POST.get('min_price_per_day')        
        max_price_per_day = request.POST.get('max_price_per_day')
        if min_price_per_day is None and max_price_per_day is None:
            result += " INTERSECT " + sqlquery
        elif min_price_per_day is None and max_price_per_day is not None:
            result += " INTERSECT " + sqlquery + "WHERE hl.price_per_day <= " + str(max_price_per_day)
        elif min_price_per_day is not None and max_price_per_day is None:
            result += " INTERSECT" + sqlquery + "WHERE hl.price_per_day >= " + str(min_price_per_day)
        else:
            result += " INTERSECT " + sqlquery + "WHERE hl.price_per_day >= " + str(min_price_per_day) + " AND hl.price_per_day <= " + str(max_price_per_day)
       
        region = request.POST.getlist('region')
        if len(region) == 0:
            result += " INTERSECT " + sqlquery
        else:
            result += " INTERSECT ("
            for i in range(len(region)-1):
                result += sqlquery + ",towns t" + "WHERE" + "hl.town = t.town" + "AND t.region = " + region[i] + " UNION "
             result += sqlquery + ",towns t" + "WHERE" + "hl.town = t.town" + "AND t.region = " + region[len(region)-1] + ")"     
        
        towns = request.POST.getlist('towns')
        if len(towns) == 0:
            result += " INTERSECT " + sqlquery
        else:
            result += " INTERSECT ("
            for i in range(len(towns)-1):
                result += sqlquery + "WHERE" + "hl.town = " + towns[i] + " UNION "
             result += sqlquery + "WHERE" + "hl.town = " + towns[len(towns)-1] + ")"
        
        hdb_types = request.POST.getlist('hdb_types')
        if len(hdb_types) == 0:
            result += " INTERSECT " + sqlquery
        else:
            result += "INTERSECT ("
            for i in range(len(hdb_types)-1):
                result += sql_query + "WHERE" + "hl.type = " + hdb_types[i] + " UNION "
            result += sql_query + "WHERE" + "hl.type = " + hdb_types[len(hdb_types)-1] + ")"
        
        min_size = request.POST.get('min_size')       
        max_size = request.POST.get('max_size')
        if min_size is None and max_size is None:
            result += " INTERSECT " + sqlquery
        elif min_size is None and max_size is not None:
            result += " INTERSECT " + sqlquery + "WHERE hl.size <= " + str(max_size)
        elif min_price_per_day is not None and max_price_per_day is None:
            result += " INTERSECT " + sqlquery + "WHERE hl.size >= " + str(min_size)
        else:
            result += " INTERSECT " + sqlquery + "WHERE hl.size>= " + str(min_size) + " AND hl.size <= " + str(max_size)
       
        num_bedrooms = request.POST.get('num_bedrooms')
        result += " INTERSECT " + sqlquery + ", hdb_types_info hi " +"WHERE hl.hdb_type = hi.hdb_type AND " + "hi.number_of_bedrooms = " + str(num_bedrooms)
        
        num_bathrooms = request.POST.get('num_bathrooms')
        result += "INTERSECT " + sqlquery + ", hdb_types_info hi " +"WHERE hl.hdb_type = hi.hdb_type AND " + "hi.number_of_bathrooms = " + str(num_bathrooms)
        
        nearest_mrt = request.POST.getlist('nearest_mrt')
        if len(nearest_mrt) == 0:
            result += "INTERSECT " + sqlquery
        else:
            result += "INTERSECT ("
            for i in range(len(nearest_mrt)-1):
                result += sql_query + "WHERE" + "hl.nearest_mrt = " + nearest_mrt[i] + " UNION "
            result += sql_query + "WHERE" + "hl.nearest_mrt = " + nearest_mrt[len(nearest_mrt)-1] + ")"
        
        #need to get rid of the symbols that the options return and the m as well
        nearest_mrt_dist = request.POST.getlist('nearest_mrt_dist')
        if len(nearest_mrt_dist) == 0:
            result += "INTERSECT " + sqlquery
        else:
            result += "INTERSECT ("
            for i in range(len(nearest_mrt_dist)-1):
                result += sql_query + "WHERE" + "hl.nearest_mrt_distt = " + nearest_mrt_dist[i] + " UNION "
            result += sql_query + "WHERE" + "hl.nearest_mrt_dist = " + nearest_mrt_dist[len(nearest_mrt)-1] + ")"

        return render(request, 'app/listings.html', result_dict)
    
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM hdb_listings")
        listings = cursor.fetchall()
        
    result_dict['listings'] = listings

    return render(request, 'app/listings.html', result_dict)

@login_required(login_url = 'login')
def admin(request):
    return render(request, 'app/admin.html')
