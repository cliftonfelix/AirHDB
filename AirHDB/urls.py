from django.contrib import admin
from django.urls import path

import app.views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', app.views.login_page, name='login'),
    
    path('register/', app.views.register, name = 'register')
    path('listings/', app.views.listings, name = 'listings')
    
#     path('add', app.views.add, name='add'),
#     path('view/<str:id>', app.views.view, name='view'),
#     path('edit/<str:id>', app.views.edit, name='edit'),
]
