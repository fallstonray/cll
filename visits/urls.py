# /visits/url.py
from django.contrib import admin
from django.urls import path, include
from . import views
from maintenance.models import Contract, Customer

urlpatterns = [
    path('visits/', views.visits, name='visits'),
    path('create_visit/',
         views.createVisit, name='create_visit'),
]

# path('', views.home, name="home"),
# path('', include('django.contrib.auth.urls')),
# path('home', views.home, name='home'),
# path('sign-up', views.sign_up, name='sign_up'),
# path('customers/', views.customers, name='customers'),
# path('create_customer/',
#      views.createCustomer, name="create_customer"),
# path('customer/<str:pk>/', views.customer, name="customer"),
# path('update_customer/<str:pk>/',
#      views.updateCustomer, name="update_customer"),

# path('maintenance/', views.maintenance, name="maintenance"),

# path('create_contract/<str:pk>/',
#      views.createContract, name="create_contract"),
# path('view_contract/<str:pk>/',
#      views.viewContract, name="view_contract"),
# path('update_contract/<str:pk>/',
#      views.updateContract, name="update_contract"),
# path('copy_contract/<str:pk>/',
#      views.copyContract, name="copy_contract"),
# path('delete_contract/<str:pk>/',
#      views.deleteContract, name="delete_contract"),
