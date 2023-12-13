from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [

    path('', views.home, name="home"),
    path('', include('django.contrib.auth.urls')),
    path('home', views.home, name='home'),
    path('sign-up', views.sign_up, name='sign_up'),
    path('customers/', views.customers, name='customers'),
    path('create_customer/',
         views.createCustomer, name="create_customer"),
    path('customer/<str:pk>/', views.customer, name="customer"),
    path('update_customer/<str:pk>/',
         views.updateCustomer, name="update_customer"),

    path('maintenance/', views.maintenance, name="maintenance"),

    path('create_contract/<str:pk>/',
         views.createContract, name="create_contract"),
    path('view_contract/<str:pk>/',
         views.viewContract, name="view_contract"),
    path('update_contract/<str:pk>/',
         views.updateContract, name="update_contract"),
    path('copy_contract/<str:pk>/',
         views.copyContract, name="copy_contract"),
    path('delete_contract/<str:pk>/',
         views.deleteContract, name="delete_contract"),


    path('reset_password/', auth_views.PasswordResetView.as_view(template_name="maintenance/password_reset.html"),
         name="reset_password"),

    path('reset_password_sent/', auth_views.PasswordResetDoneView.as_view(template_name="maintenance/password_reset_sent.html"),
         name="password_reset_done"),

    path('reset_confirm/<uid64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name="maintenance/password_reset_confirm.html"),
         name="password_reset_confirm"),

    #     path('reset/<uid64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name="maintenance/password_reset_confirm.html"),
    #          name="password_reset_confirm"),

    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(template_name="maintenance/password_reset_done.html"),
         name="password_reset_complete"),

]
