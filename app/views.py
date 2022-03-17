from django.shortcuts import render, redirect
from django.db import connection
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
import re

# Create your views here.
def login_page(request):
    if request.user.is_authenticated: #check if user is admin or not from users table
        return redirect('listings')
    if request.method == 'POST':
        email = request.POST.get('email').lower()
        password = request.POST.get('password')
        try: 
            user = User.objects.get(username = email)
        except:
            messages.error(request, 'Invalid Username!')
            return render(request, 'app/login.html')  
        user = authenticate(request, username = email, password = password)
        if user is not None:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE email_address = %s", [email])
                row = cursor.fetchone()
                login(request, user)
                if row[4] == 'Yes':
                    return redirect('admin')
                elif row[4] == 'No':
                    return redirect('listings')
        else:
            messages.error(request, 'Wrong password entered!')
    return render(request, 'app/login.html')

def logout_page(request):
    logout(request)
    return redirect('login')

def register_page(request):
    if request.method == 'POST':
        # Ensure password matches confirmation
        name = request.POST.get('name')
        number = int(request.POST.get('number'))
        email = request.POST.get('email').lower()
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE email_address = %s", [email])
            row = cursor.fetchone()
            
            invalid = False
            if name == '' or number == '' or email == '' or password == '' or confirm_password == '':
                messages.error(request, 'Please fill in all fields!')
                invalid = True
            if not (number >= 30000000 and number <= 39999999) or not (number >= 60000000 and number <= 69999999) \
            or not (number >= 80000000 and number <= 89999999) or not (number >= 90000000 and number <= 98999999):
                messages.error(request, 'Please enter a valid Singapore number!')
                invalid = True
            if re.search(".@.\.", email) == None:
                messages.error(request, 'Please enter a valid email address!')
                invalid = True
            if password != confirm_password:
                messages.error(request, 'Passwords do not match!')
                invalid = True
            if invalid:
                return render(request, 'app/register.html')
            
            if row == None:
                user = User.objects.create_user(email, password = password)
                user.save()
                return redirect('login')
            else:
                messages.error(request, 'The email has been used by another user!')
    return render(request, 'app/register.html')
    
@login_required(login_url = 'login')
def listings(request):
    """Shows the main page"""
    
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM hdb_units")
        units = cursor.fetchall()
        
    result_dict = {'records': units}

    return render(request, 'app/index.html', result_dict)

@login_required(login_url = 'login')
def admin(request):
    return render(request, 'app/admin.html')
       


