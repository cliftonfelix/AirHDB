from django.shortcuts import render, redirect
from django.db import connection
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages

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
     
        user = authenticate(request, username = email, password = password)
        if user is not None:
            login(request, user)
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
        email = request.POST.get('email').lower()
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM user WHERE email = %s", [email])
            row = cursor.fetchone()
            if password != confirmation:
                messages.error(request, 'Passwords do not match!')

                ## No user with same email
            if row == None:
                cursor.execute("INSERT INTO users VALUES (%s, %s, %s, %s, %s)", [name, email, password, number, 'no'])
                user = User.objects.create_user(email, password = password)
                user.save()
                login(request, user)
                return redirect('listings')
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
       


