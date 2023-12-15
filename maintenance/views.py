from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.views import PasswordResetView
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.forms import inlineformset_factory
from django.db.models import Sum, Count, F, ExpressionWrapper, FloatField
from .models import *
from visits.models import Visit, VisitType
from .forms import ContractForm, CustomerForm, RegisterForm
from .filters import ContractFilter, CustomerFilter
from django.contrib.humanize.templatetags.humanize import intcomma
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm
from datetime import date, datetime, timedelta
from django.db.models.functions import Now
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.timezone import datetime
from django.contrib import messages



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

    # expiring in the next 60 days
    plus60 = date.today() + timedelta(days=60)
    today = date.today()
    expire_list = Contract.objects.filter(
        end_date__range=[today, plus60])

    myFilter = ContractFilter()
    context = {'contracts': contracts, 'customers': customers,
               'total_customers': total_customers,
               'total_contracts_value': total_contracts_value, 'expire_list': expire_list,
               'myFilter': myFilter, 'active_contracts': active_contracts, 'total_active_contracts': total_active_contracts}
    return render(request, 'maintenance/dashboard.html', context)


@ login_required(login_url="/login")
@ permission_required("maintenance.add_customer", login_url="/login", raise_exception=True)
def createCustomer(request):
    form = CustomerForm(initial={'customer': customer})
    if request.method == 'POST':
        # print('Printing POST:', request.POST)
        form = CustomerForm(request.POST)
        if form.is_valid():
            # form.save()
            instance = form.save()
            # the instance.pk returns user to newly created customer
        return redirect('customer', instance.pk)
    context = {'form': form}
    return render(request, 'maintenance/customer_form.html', context)

# below is the view for a list of customers with search capabilities


@ login_required(login_url="/login")
def customers(request):
    customers = Customer.objects.all()
    customers_count = customers.count()
    myFilter = CustomerFilter(request.GET, queryset=customers)
    customers = myFilter.qs
    context = {'customers': customers,
               'customers_count': customers_count, 'myFilter': myFilter}

    return render(request, 'maintenance/customers.html', context)

# below is the view for a specific customer


@ login_required(login_url="/login")
def customer(request, pk):
    customer = Customer.objects.get(id=pk)
    contracts = customer.contract_set.all()
    # print(contracts)
    # contracts_count = contracts.count()
    # amounts = customer.contract_set.values_list('price', flat=True)
    # total_customer_contracts_value = sum(amounts)
    myFilter = ContractFilter(request.GET, queryset=contracts)
    allcontracts = myFilter.qs

    active_contracts = myFilter.qs.filter(
        # start_date__gte=datetime.now()-timedelta(days=365))
        end_date__gte=datetime.now())
    active_count = active_contracts.count()
    # print(active_count)
    amounts = active_contracts.aggregate(Sum('price', flat=True))
    # print(amounts)
    get_total = list(amounts.values())[0]
    if get_total is None:
        get_total = 0
    # print(type(get_total))
    # print(get_total)
    get_total = int(get_total)
    active_contracts_value = get_total

    expired_contracts = myFilter.qs.filter(
        # start_date__gte=datetime.now()-timedelta(days=365))
        end_date__lt=datetime.now())

    context = {'customer': customer, 'contracts': contracts, 'myFilter': myFilter,
               'active_contracts_value': active_contracts_value,
               'active_contracts': active_contracts,
               'expired_contracts': expired_contracts, 'active_count': active_count}
    return render(request, 'maintenance/customer.html', context)


# below is the view for updating a customer
@ login_required(login_url="/login")
def updateCustomer(request, pk):
    customer = Customer.objects.get(id=pk)
    form = CustomerForm(instance=customer)

    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            return redirect('customer', pk)
    context = {'form': form}
    return render(request, 'maintenance/customer_form.html', context)

# below is the view for all maintenance contracts


@ login_required(login_url="/login")
def maintenance(request):
    contracts = Contract.objects.all()
    contracts_count = contracts.count()
    myFilter = ContractFilter(request.GET, queryset=contracts)
    contracts = myFilter.qs
    context = {'contracts': contracts,
               'contracts_count': contracts_count, 'myFilter': myFilter}

    return render(request, 'maintenance/maintenance.html', context)


@ login_required(login_url="/login")
def createContract(request, pk):
    # customer = Customer.objects.get(id=pk) ~ this used to work but stopped, changed get to filter
    customer = Customer.objects.get(id=pk)
    form = ContractForm(initial={'customer': customer})
    if request.method == 'POST':
        # print('Printing POST:', request.POST)
        form = ContractForm(request.POST)
        if form.is_valid():
            instance = form.save()
            # form.save()
            return redirect('view_contract', instance.pk)
    context = {'form': form}
    return render(request, 'maintenance/contract_form.html', context)


@ login_required(login_url="/login")
def copyContract(request, pk):
    contract = Contract.objects(id=pk)
    contract.pk = None
    contract.save()

    site_name = Contract.objects.filter(id=pk)
    form = ContractForm(
        initial={'customer': customer})
    # form = ContractForm(
    #     initial={'customer': customer, 'site_name': Contract.site_name, 'contract.price': Contract.price})
    if request.method == 'POST':
        # print('Printing POST:', request.POST)
        form = ContractForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/')

    context = {'form': form}
    return render(request, 'maintenance/contract_form.html', context)


# below was copied from def customer and modified

@ login_required(login_url="/login")
def viewContract(request, pk):
    contract = Contract.objects.get(id=pk)
    price = float(contract.price)
    payments = float(contract.payments)
    # print(type(payments))
    payment_amount = price / payments
    visit_man_hours = float(0)
    visits = Visit.objects.filter(visit_contract=contract)
    for visit in visits:
        visit_man_hours += float(visit.total_man_hours)
    print(visit_man_hours)
    # th = float(0)
    # th = sum(float(visit.total_man_hours))       
    # print(type(th))

    visits_count = visits.count()
    context = {'contract': contract, 'payment_amount': payment_amount, 'visits': visits, 'visits_count': visits_count, 'visit_man_hours': visit_man_hours}
    return render(request, 'maintenance/contract_view.html', context)


@ login_required(login_url="/login")
def updateContract(request, pk):
    contract = Contract.objects.get(id=pk)
    form = ContractForm(instance=contract)

    if request.method == 'POST':
        form = ContractForm(request.POST, instance=contract)
        if form.is_valid():
            form.save()
            return redirect('view_contract', pk)
    context = {'form': form}
    return render(request, 'maintenance/contract_form.html', context)


@ login_required(login_url="/login")
def deleteContract(request, pk):
    contract = Contract.objects.get(id=pk)
    if request.method == 'POST':
        contract.delete()
        return redirect('/')

    context = {'item': contract}
    return render(request, 'maintenance/delete.html', context)


# from https://dev.to/earthcomfy/django-reset-password-3k0l


class ResetPasswordView(SuccessMessageMixin, PasswordResetView):
    template_name = 'maintenance/password_reset.html'
    email_template_name = 'maintenance/password_reset_email.html'
    subject_template_name = 'maintenance/password_reset_subject'
    success_message = "We've emailed you instructions for setting your password, " \
                      "if an account exists with the email you entered. You should receive them shortly." \
                      " If you don't receive an email, " \
                      "please make sure you've entered the address you registered with, and check your spam folder."
    success_url = reverse_lazy('home')
