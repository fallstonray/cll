# /employee/url.py
from django.contrib import admin
from django.urls import path, include
from . import views
from maintenance.models import Contract, Customer

urlpatterns = [
    path('employees/', views.employees, name='employees'),
    path('create_employee/',
         views.createEmployee, name='create_employee'),
]
