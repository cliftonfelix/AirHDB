"""AirHDB URL Configuration
The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls import handler404

import app.views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', app.views.login_page, name='login'),
    path('logout/', app.views.logout_page, name = "logout"),
    path('register/', app.views.register_page, name = 'register'),
    path('listings/', app.views.listings, name = 'listings'),
    path('bookings/', app.views.adminb, name='adminbookings'),
    path('units/', app.views.adminu, name='adminunits'),
    path('units/view/<str:id>/', app.views.viewunits),
    path('bookings/view/<str:id>/', app.views.viewbookings),
    path('units/edit/<str:id>/', app.views.editunits),
    path('bookings/edit/<str:id>/', app.views.editbookings),
    path('units/add/', app.views.adminaddunits, name='adminaddunits'),
    path('mrts/', app.views.adminm, name='adminmrts'),
    path('mrts/add', app.views.addmrt, name='adminaddmrt'),
    path('profile/', app.views.profile, name = 'profile'),
    path('change_profile/', app.views.change_profile, name = 'change_profile'),
    
    path('change_password/', app.views.change_password, name = 'change_password'),
    path('payment/', app.views.payment, name = "payment"),
    path('listings/book/<str:id>/', app.views.book),
    path('user_bookings/', app.views.user_bookings, name = 'user_bookings'),
    path('user_bookings/edit/<str:id>/', app.views.user_editbookings),
    path('user_bookings/view/<str:id>/', app.views.user_viewbookings),
    path('refund/', app.views.refund,name='adminrefund'),
    path('userrefund/', app.views.userrefund,name='userrefund'),

    path('user_posts/', app.views.user_posts, name = 'posts'),
    path('post_units/', app.views.useraddunits, name='useraddunits'),
    path('user_posts/view/<str:id>/', app.views.viewposts),
    path('user_posts/edit/<str:id>/', app.views.editposts)
]

handler404 = 'app.views.handler404'
