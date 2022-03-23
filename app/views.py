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
    result_dict['num_guests'] = ''
    result_dict['min_price_per_day'] = ''
    result_dict['max_price_per_day'] = ''
    result_dict['regions_default'] = '' #TODO: Default value
    result_dict['towns_default'] = '' #TODO: Default value
    result_dict['hdb_types_default'] = '' #TODO: Default value
    result_dict['min_size'] = ''
    result_dict['max_size'] = ''
    result_dict['num_bedrooms'] = '' #TODO: Default value
    result_dict['num_bathrooms'] = '' #TODO: Default value
    result_dict['nearest_mrts'] = '' #TODO: Default value
    result_dict['nearest_mrt_dist'] = '' #TODO: Default value

    if request.method == "POST":
        result = ""
        sqlquery = "SELECT * FROM hdb_listings hl1"

        #START AND END DATE FILTER
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
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
            for type in hdb_types:
                if temp:
                    temp += " UNION "
                temp += """{0} 
			   WHERE hl1.hdb_type = '{1}'""".format(sqlquery, type)

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
            if "1" in num_bedrooms:
                temp += """{0} 
                           WHERE hl1.number_of_bedrooms = 1""".format(sqlquery)

            if "2" in num_bedrooms:
                if temp:
                    temp += " UNION "
                temp += """{0} 
                           WHERE hl1.number_of_bedrooms = 2""".format(sqlquery)
				
            if "3" in num_bedrooms:
                if temp:
                    temp += " UNION "
                temp += """{0} 
                           WHERE hl1.number_of_bedrooms = 3""".format(sqlquery)

            if "4" in num_bedrooms:
                if temp:
                    temp += " UNION "
                temp += """{0} 
                           WHERE hl1.number_of_bedrooms = 4""".format(sqlquery)

            if temp:
                if result:
                    result += " INTERSECT "
                result += "({})".format(temp)
			
	#NUM BATHROOMS FILTER
        num_bathrooms = request.POST.getlist('num_bathrooms')
        if num_bathrooms:
            temp = ""
            if "1" in num_bathrooms:
                temp += """{0} 
                           WHERE hl1.number_of_bathrooms = 1""".format(sqlquery)

            if "2" in num_bathrooms:
                if temp:
                    temp += " UNION "
                temp += """{0} 
                           WHERE hl1.number_of_bathrooms = 2""".format(sqlquery)
				
            if "3" in num_bathrooms:
                if temp:
                    temp += " UNION "
                temp += """{0} 
                           WHERE hl1.number_of_bathrooms = 3""".format(sqlquery)

            if temp:
                if result:
                    result += " INTERSECT "
                result += "({})".format(temp)
			
	#NEAREST MRT FILTER
        nearest_mrts = request.POST.getlist('nearest_mrts')

        if nearest_mrts:
            temp = ""
            for nearest_mrt in nearest_mrts:
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
                temp += """{0} 
			   WHERE hl1.nearest_mrt_distance < 0.1""".format(sqlquery)

            if "100 - 250 m" in nearest_mrt_dists:
                if temp:
                    temp += " UNION "
                temp += """{0} 
			   WHERE hl1.nearest_mrt_distance BETWEEN 0.1 AND 0.25""".format(sqlquery)
				
            if "250 m - 1 km" in nearest_mrt_dists:
                if temp:
                    temp += " UNION "
                temp += """{0} 
                           WHERE hl1.nearest_mrt_distance BETWEEN 0.25 AND 1""".format(sqlquery)

            if "1 - 2 km" in nearest_mrt_dists:
                if temp:
                    temp += " UNION "
                temp += """{0} 
                           WHERE hl1.nearest_mrt_distance BETWEEN 1 AND 2""".format(sqlquery)

            if "> 2 km" in nearest_mrt_dists:
                if temp:
                    temp += " UNION "
                temp += """{0} 
			   WHERE hl1.nearest_mrt_distance > 2""".format(sqlquery)

            if temp:
                if result:
                    result += " INTERSECT "
                result += "({})".format(temp)
	
        with connection.cursor() as cursor:
            if result:
                result = "SELECT * FROM ({}) temp ORDER BY temp.hdb_id".format(result)
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
    
    context = {'old_name': row[0], 'email': email, 'old_number': row[2]}
    if request.method == 'POST':
        name = request.POST.get('name')
        number = request.POST.get('number')
        
        if name == row[0] and number == row[2]:
            messages.error(request, 'New profile is identical to the old one!') 
            return render(request, 'app/change_profile.html', context)
	
        cursor.execute("UPDATE users SET name = %s, mobile_number = %s WHERE email_address = %s", [name, number, email])
	"""
        except Exception as e:
            string = str(e)
            message = ""
            if 'new row for relation "users" violates check constraint "users_mobile_number_check"' in string:
                messages.error(request, 'Please enter a valid Singapore number!') 
            return render(request, 'app/change_profile.html', context)
        messages.success(request, 'Profile has been successfully updated!')
	"""
        return redirect('profile')
    return render(request, 'app/change_profile.html', context)
