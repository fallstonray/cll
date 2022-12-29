from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.forms import inlineformset_factory
from django.db.models import Sum
from .models import *
from .forms import ContractForm, CustomerForm
from .filters import ContractFilter, CustomerFilter
from django.contrib.humanize.templatetags.humanize import intcomma


def home(request):
    contracts = Contract.objects.all()
    customers = Customer.objects.all()
    total_customers = customers.count()
    total_contracts = contracts.count()
    # total_contracts_value = Contract.objects.aggregate(Sum('price')) - This is an alt way to do the same as below but returns a tupol
    amounts = Contract.objects.values_list('price', flat=True)
    total_contracts_value = sum(amounts)

    context = {'contracts': contracts, 'customers': customers,
               'total_customers': total_customers, 'total_contracts': total_contracts, 'total_contracts_value': total_contracts_value}
    return render(request, 'maintenance/dashboard.html', context)


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


def customers(request):
    customers = Customer.objects.all()
    customers_count = customers.count()
    myFilter = CustomerFilter(request.GET, queryset=customers)
    customers = myFilter.qs
    context = {'customers': customers,
               'customers_count': customers_count, 'myFilter': myFilter}

    return render(request, 'maintenance/customers.html', context)

# below is the view for a specific customer


def customer(request, pk):
    customer = Customer.objects.get(id=pk)
    contracts = customer.contract_set.all()
    contracts_count = contracts.count()
    amounts = customer.contract_set.values_list('price', flat=True)
    total_customer_contracts_value = sum(amounts)
    myFilter = ContractFilter(request.GET, queryset=contracts)
    contracts = myFilter.qs
    context = {'customer': customer, 'contracts': contracts,
               'contracts_count': contracts_count, 'total_customer_contracts_value': total_customer_contracts_value, 'myFilter': myFilter}
    return render(request, 'maintenance/customer.html', context)


# below is the view for updating a customer
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


def maintenance(request):
    contracts = Contract.objects.all()
    contracts_count = contracts.count()
    myFilter = ContractFilter(request.GET, queryset=contracts)
    contracts = myFilter.qs
    context = {'contracts': contracts,
               'contracts_count': contracts_count, 'myFilter': myFilter}

    return render(request, 'maintenance/maintenance.html', context)


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


def viewContract(request, pk):
    contract = Contract.objects.get(id=pk)
    # owner = contract.customer_set.all()
    # contracts_count = contracts.count()
    # amounts = customer.contract_set.values_list('price', flat=True)
    # total_customer_contracts_value = sum(amounts)
    # myFilter = ContractFilter(request.GET, queryset=contracts)
    # contracts = myFilter.qs
    context = {'customer': customer, 'contracs': contract, }
    return render(request, 'maintenance/contract_view.html', context)


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


def deleteContract(request, pk):
    contract = Contract.objects.get(id=pk)
    if request.method == 'POST':
        contract.delete()
        return redirect('/')

    context = {'item': contract}
    return render(request, 'maintenance/delete.html', context)
