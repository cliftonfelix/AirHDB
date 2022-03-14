from django.shortcuts import render, redirect
from django.db import connection

# Create your views here.
def index(request):
    """Shows the main page"""
    
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM hdb_listings")
        listings = cursor.fetchall()
        
    result_dict = {'records': listings}

    return render(request, 'app/index.html', result_dict)
