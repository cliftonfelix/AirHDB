from django.shortcuts import render, redirect
from django.db import connection
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

# Create your views here.
def listings(request):
    """Shows the main page"""
    
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM hdb_units")
        units = cursor.fetchall()
        
    result_dict = {'records': units}

    return render(request, 'app/index.html', result_dict)

def login_page(request):
#     with connection.cursor() as cursor:
#         cursor.execute("SELECT * FROM users")
#         users = cursor.fetchall()
       
#     for user in users:
#         user_temp = User.objects.create_user(user[1], password = user[2])
#         user_temp.save()
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
#         try:
#             user = User.objects.get(username = username)
#         except:
#             messages.error(request, 'User does not exist!')
        
    
        user = authenticate(request, username = username, password = password)
        if user is not None:
            login(request, user)
            return redirect('listings')

    context = {}
    return render(request, 'app/login.html', context)
