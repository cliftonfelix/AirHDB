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
    result_dict['start_date'] = ''
    result_dict['end_date'] = ''

    if request.method == "POST":
        result = ""
        sqlquery = "SELECT * FROM hdb_listings hl1"

        #START AND END DATE FILTER
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        if start_date and end_date: #TODO: if only start_date filled in then show end_date to be start + 1 and vice versa
            result += """({0}
                          WHERE NOT EXISTS (SELECT *
                          FROM bookings b1
                          WHERE hl1.hdb_id = b1.hdb_id AND
                                (('{1}' :: DATE BETWEEN b1.start_date AND b1.end_date - 1 OR
                                '{2}' :: DATE - 1 BETWEEN b1.start_date AND b1.end_date - 1) OR
                                (b1.start_date BETWEEN '{1}' :: DATE AND '{2}' :: DATE - 1 OR
                                b1.end_date - 1 BETWEEN '{1}' :: DATE AND '{2}' :: DATE - 1))))""".format(sqlquery, start_date, end_date)

            result_dict['start_date'] = start_date
            result_dict['end_date'] = end_date

        #MIN AND MAX PRICE FILTER
        min_price_per_day = request.POST.get('min_price_per_day')
        max_price_per_day = request.POST.get('max_price_per_day')
        temp = ""

        if min_price_per_day:
            temp = "({} WHERE hl.price_per_day >= {}".format(sqlquery, min_price_per_day)
            if not max_price_per_day:
                temp += ")"

        if max_price_per_day:
            if not temp:
                temp = "({} WHERE hl.price_per_day <= {})".format(sqlquery, max_price_per_day)
            else:
                temp += " INTERSECT {} WHERE hl.price_per_day <= {})".format(sqlquery, max_price_per_day)

        if temp:
            if result:
                result += " INTERSECT "
            result += temp

        with connection.cursor() as cursor:
            if result:
                cursor.execute(result)
            else:
                cursor.execute("SELECT * FROM hdb_listings")
            listings = cursor.fetchall()

        result_dict['listings'] = listings

        return render(request, 'app/listings.html', result_dict)

    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM hdb_listings")
        listings = cursor.fetchall()

    result_dict['listings'] = listings

    return render(request, 'app/listings.html', result_dict)

@login_required(login_url = 'login')
def admin(request):
    return render(request, 'app/admin.html')
