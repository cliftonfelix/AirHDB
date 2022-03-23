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
