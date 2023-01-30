from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.forms import inlineformset_factory
from django.db.models import Sum
from .models import *
from .forms import ContractForm, CustomerForm, RegisterForm
from .filters import ContractFilter, CustomerFilter
from django.contrib.humanize.templatetags.humanize import intcomma
from django.contrib.auth.forms import UserCreationForm
from datetime import datetime, timedelta
from django.db.models.functions import Now
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, permission_required


def sign_up(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
        login(request, user)
        return redirect('/home')
    else:
        form = RegisterForm()
    return render(request, 'registration/sign_up.html', {"form": form})


def loginPage(request):
    context = {}
    return render(request, 'accounts/login.html', context)


@login_required(login_url="/login")
def home(request):
    contracts = Contract.objects.all()
    customers = Customer.objects.all()
    total_customers = customers.count()

    active_contracts = contracts.filter(
        end_date__gte=datetime.now())
    total_active_contracts = active_contracts.count()

    # total_contracts_value = Contract.objects.aggregate(Sum('price')) - This is an alt way to do the same as below but returns a tupol
    # amounts = Contract.objects.values_list('price', flat=True)
    # total_contracts_value = sum(amounts)

    amounts = active_contracts.values_list('price', flat=True)
    total_contracts_value = sum(amounts)

    # Upcoming expirations
    expire_list = Contract.objects.filter(
        end_date__lte=datetime.now()+timedelta(days=60))

    myFilter = ContractFilter()
    context = {'contracts': contracts, 'customers': customers,
               'total_customers': total_customers,
               'total_contracts_value': total_contracts_value, 'expire_list': expire_list,
               'myFilter': myFilter, 'active_contracts': active_contracts, 'total_active_contracts': total_active_contracts}
    return render(request, 'maintenance/dashboard.html', context)


@login_required(login_url="/login")
@permission_required("maintenance.add_customer", login_url="/login", raise_exception=True)
def createCustomer(request):
    form = CustomerForm(initial={'customer': customer})
    if request.method == 'POST':
        # print('Printing POST:', request.POST)
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/')

    context = {'form': form}
    return render(request, 'maintenance/customer_form.html', context)

# below is the view for a list of customers with search capabilities


@login_required(login_url="/login")
def customers(request):
    customers = Customer.objects.all()
    customers_count = customers.count()
    myFilter = CustomerFilter(request.GET, queryset=customers)
    customers = myFilter.qs
    context = {'customers': customers,
               'customers_count': customers_count, 'myFilter': myFilter}

    return render(request, 'maintenance/customers.html', context)

# below is the view for a specific customer


@login_required(login_url="/login")
def customer(request, pk):
    customer = Customer.objects.get(id=pk)
    contracts = customer.contract_set.all()
    contracts_count = contracts.count()
    amounts = customer.contract_set.values_list('price', flat=True)
    total_customer_contracts_value = sum(amounts)
    myFilter = ContractFilter(request.GET, queryset=contracts)
    allcontracts = myFilter.qs

    active_contracts = myFilter.qs.filter(
        # start_date__gte=datetime.now()-timedelta(days=365))
        end_date__gte=datetime.now())

    expired_contracts = myFilter.qs.filter(
        # start_date__gte=datetime.now()-timedelta(days=365))
        end_date__lt=datetime.now())

    context = {'customer': customer, 'contracts': contracts,
               'contracts_count': contracts_count, 'total_customer_contracts_value': total_customer_contracts_value, 'myFilter': myFilter, 'active_contracts': active_contracts, 'expired_contracts': expired_contracts}
    return render(request, 'maintenance/customer.html', context)


# below is the view for updating a customer
@login_required(login_url="/login")
def updateCustomer(request, pk):
    customer = Customer.objects.get(id=pk)
    form = CustomerForm(instance=customer)

    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            return redirect('/customers/')
    context = {'form': form}
    return render(request, 'maintenance/customer_form.html', context)

# below is the view for all maintenance contracts


@login_required(login_url="/login")
def maintenance(request):
    contracts = Contract.objects.all()
    contracts_count = contracts.count()
    myFilter = ContractFilter(request.GET, queryset=contracts)
    contracts = myFilter.qs
    context = {'contracts': contracts,
               'contracts_count': contracts_count, 'myFilter': myFilter}

    return render(request, 'maintenance/maintenance.html', context)


@login_required(login_url="/login")
def createContract(request, pk):
    customer = Customer.objects.get(id=pk)
    form = ContractForm(initial={'customer': customer})
    if request.method == 'POST':
        # print('Printing POST:', request.POST)
        form = ContractForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/')

    context = {'form': form}
    return render(request, 'maintenance/contract_form.html', context)

# below was copied from def customer and modified


@login_required(login_url="/login")
def viewContract(request, pk):
    contract = Contract.objects.get(id=pk)
    context = {'customer': customer,
               'contract': contract, 'visits': contract.visits, }
    return render(request, 'maintenance/contract_view.html', context)


@login_required(login_url="/login")
def updateContract(request, pk):
    contract = Contract.objects.get(id=pk)
    form = ContractForm(instance=contract)

    if request.method == 'POST':
        form = ContractForm(request.POST, instance=contract)
        if form.is_valid():
            form.save()
            return redirect('/maintenance/')
    context = {'form': form}
    return render(request, 'maintenance/contract_form.html', context)


@login_required(login_url="/login")
def deleteContract(request, pk):
    contract = Contract.objects.get(id=pk)
    if request.method == 'POST':
        contract.delete()
        return redirect('/')

    context = {'item': contract}
    return render(request, 'maintenance/delete.html', context)
