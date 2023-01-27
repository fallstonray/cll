from django.contrib import admin
from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name="home"),
    path('login/'),
    path('customers/', views.customers),
    path('create_customer/',
         views.createCustomer, name="create_customer"),
    path('customer/<str:pk>/', views.customer, name="customer"),
    path('update_customer/<str:pk>/',
         views.updateCustomer, name="update_customer"),

    path('maintenance/', views.maintenance),
    path('create_contract/<str:pk>/',
         views.createContract, name="create_contract"),
    path('view_contract/<str:pk>/',
         views.viewContract, name="view_contract"),

    path('update_contract/<str:pk>/',
         views.updateContract, name="update_contract"),
    path('delete_contract/<str:pk>/',
         views.deleteContract, name="delete_contract"),


]
