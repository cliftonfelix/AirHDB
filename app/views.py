from django.shortcuts import render, redirect
from django.db import connection
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages

# Create your views here.
def login_page(request):
    if request.user.is_authenticated:
        return redirect('listings')
#     with connection.cursor() as cursor:
#         cursor.execute("SELECT * FROM users")
#         users = cursor.fetchall()
       
#     for user in users:
#         user_temp = User.objects.create_user(user[2], password = user[1])
#         user_temp.save()
        
    if request.method == 'POST':
        username = request.POST.get('username').lower()
        password = request.POST.get('password')
        try: 
            user = User.objects.get(username = username)
        except:
            messages.error(request, 'User does not exist!')
     
        user = authenticate(request, username = username, password = password)
        if user is not None:
            login(request, user)
            return redirect('listings')

    context = {}
    return render(request, 'app/login.html', context)

def logout_page(request):
    logout(request)
    context = {}
    return render(request, 'app/login.html', context)

def register_page(request):
    form = UserCreationForm()
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit = False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'An error occured during registration')
        """
        name = request.POST.get('name')
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        try:
            user = User.objects.get(username = username)
        except:
            messages.error(request, 'User does not exist!')
            """
    return render(request, 'app/register.html', {'form': form})
    
@login_required(login_url = 'login')
def listings(request):
    """Shows the main page"""
    
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM hdb_units")
        units = cursor.fetchall()
        
    result_dict = {'records': units}

    return render(request, 'app/index.html', result_dict)
       


