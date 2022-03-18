from django.urls import path

from . import views


urlpatterns = [
    

    path('adminbookings/',views.adminb,name='adminbookings'),
    path('adminunits/',views.adminu,name='adminunits'),
    path('adminunits/view/<str:id>/',views.viewunits),
    path('adminbookings/view/<str:id>/',views.viewbookings),
    path('adminunits/edit/<str:id>/',views.editunits),
    path('adminbookings/edit/<str:id>/',views.editbookings),
    path('adminunits/add/',views.addunits,name='adminaddunits')
    

]