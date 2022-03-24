from django.urls import path

from . import views


urlpatterns = [
    

    path('bookings/',views.adminb,name='adminbookings'),
    path('units/',views.adminu,name='adminunits'),
    path('units/view/<str:id>/',views.viewunits),
    path('bookings/view/<str:id>/',views.viewbookings),
    path('units/edit/<str:id>/',views.editunits),
    path('bookings/edit/<str:id>/',views.editbookings),
    path('units/add/',views.addunits,name='adminaddunits'),
    path('mrts/',views.adminm,name='adminmrts'),
    path('mrts/add',views.addmrt,name='adminaddmrt')
    

]