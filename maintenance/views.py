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
from landscape.models import Bid
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
from django.forms.models import model_to_dict #this is for copyContract line 197
from django.db.models.fields.related import ForeignKey #this is for copyContract line 197



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
    form = CustomerForm()
    if request.method == 'POST':
        # print('Printing POST:', request.POST)
        form = CustomerForm(request.POST)
        if form.is_valid():
            # form.save()
            instance = form.save()
            # the instance.pk returns user to newly created customer
        return redirect('customer', instance.uuid)
    context = {'form': form}
    return render(request, 'maintenance/customer_form.html', context)

# below is the view for a list of customers with search capabilities


@ login_required(login_url="/login")
@ permission_required("maintenance.view_customer", raise_exception=True)
def customers(request):
    ctype = request.GET.get('type', 'all')
    if ctype == 'gc':
        base_qs = Customer.objects.filter(is_general_contractor=True).order_by('name')
        page_title = 'GC Customers'
    elif ctype == 'maintenance':
        base_qs = Customer.objects.filter(is_general_contractor=False).order_by('name')
        page_title = 'Maintenance Customers'
    else:
        base_qs = Customer.objects.all().order_by('name')
        page_title = 'All Customers'

    myFilter = CustomerFilter(request.GET, queryset=base_qs)
    customers = myFilter.qs
    context = {
        'customers': customers,
        'customers_count': customers.count(),
        'myFilter': myFilter,
        'page_title': page_title,
        'ctype': ctype,
    }
    return render(request, 'maintenance/customers.html', context)

# below is the view for a specific customer


@ login_required(login_url="/login")
@ permission_required("maintenance.view_customer", raise_exception=True)
def customer(request, uuid):
    customer = Customer.objects.get(uuid=uuid)
    contracts = customer.contract_set.all()
    # print(contracts)
    # contracts_count = contracts.count()
    # amounts = customer.contract_set.values_list('price', flat=True)
    # total_customer_contracts_value = sum(amounts)
    myFilter = ContractFilter(request.GET, queryset=contracts)
    allcontracts = myFilter.qs

    active_contracts = myFilter.qs.filter(is_active=True).order_by('site_name')
    active_count = active_contracts.count()
    amounts = active_contracts.aggregate(Sum('price', flat=True))
    get_total = list(amounts.values())[0]
    if get_total is None:
        get_total = 0
    active_contracts_value = int(get_total)

    expired_contracts = myFilter.qs.filter(is_active=False)

    current_work = Bid.objects.filter(
        customer=customer,
        phase__in=['awarded', 'likely']
    ).exclude(status='completed').order_by('project_name')

    completed_work = Bid.objects.filter(
        customer=customer,
        phase__in=['awarded', 'likely'],
        status='completed'
    ).order_by('project_name')

    bid_history = Bid.objects.filter(
        customer=customer,
        phase__in=['estimating', 'submitted', 'on_hold', 'lost', 'dead']
    ).order_by('-created_at')

    context = {'customer': customer, 'contracts': contracts, 'myFilter': myFilter,
               'active_contracts_value': active_contracts_value,
               'active_contracts': active_contracts,
               'expired_contracts': expired_contracts, 'active_count': active_count,
               'current_work': current_work,
               'completed_work': completed_work,
               'bid_history': bid_history}
    return render(request, 'maintenance/customer.html', context)


# below is the view for updating a customer
@ login_required(login_url="/login")
@ permission_required("maintenance.change_customer", raise_exception=True)
def updateCustomer(request, uuid):
    customer = Customer.objects.get(uuid=uuid)
    form = CustomerForm(instance=customer)

    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            return redirect('customer', uuid)
    context = {'form': form}
    return render(request, 'maintenance/customer_form.html', context)

# below is the view for all maintenance contracts


@ login_required(login_url="/login")
@ permission_required("maintenance.view_contract", raise_exception=True)
def maintenance(request):
    all_contracts = Contract.objects.all()
    contracts_count = all_contracts.count()

    myFilter = ContractFilter(request.GET, queryset=all_contracts)
    contracts = myFilter.qs

    active_contracts = contracts.filter(
        end_date__gte=datetime.now()).order_by('site_name')
    total_active_contracts = active_contracts.count()

    if request.GET.get('export') == 'csv':
        import csv
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="active_maintenance_contracts.csv"'
        writer = csv.writer(response)
        headers = ['Site Name', 'Customer', 'Location', 'Start Date', 'End Date', 'Visits']
        if request.user.is_superuser:
            headers.append('Price')
        writer.writerow(headers)
        for c in active_contracts:
            row = [
                c.site_name,
                str(c.site_customer) if c.site_customer else '',
                c.location or '',
                c.start_date or '',
                c.end_date or '',
                c.site_visits or 0,
            ]
            if request.user.is_superuser:
                row.append(c.price or '')
            writer.writerow(row)
        return response

    context = {'all_contracts': all_contracts, 'active_contracts': active_contracts,
               'contracts_count': contracts_count, 'myFilter': myFilter, 'total_active_contracts': total_active_contracts}

    return render(request, 'maintenance/maintenance.html', context)




@ login_required(login_url="/login")
@ permission_required("maintenance.add_contract", raise_exception=True)
def createContract(request, uuid):
    customer = Customer.objects.get(uuid=uuid)
    form = ContractForm(initial={'customer': customer})
    if request.method == 'POST':
        form = ContractForm(request.POST)
        if form.is_valid():
            instance = form.save()
            return redirect('view_contract', instance.uuid)
    context = {'form': form}
    return render(request, 'maintenance/contract_form.html', context)


@ login_required(login_url="/login")
@ permission_required("maintenance.add_contract", raise_exception=True)
def copyContract(request, uuid):
    if request.method != 'POST':
        return redirect('view_contract', uuid)

    original_contract = Contract.objects.get(uuid=uuid)
    contract_data = model_to_dict(original_contract)

    for field in Contract._meta.get_fields():
        if isinstance(field, ForeignKey):
            field_name = field.name
            if field_name in contract_data:
                contract_data[field_name] = getattr(original_contract, field_name)

    contract = Contract(**contract_data)
    contract.pk = None
    contract.save()

    return redirect('update_contract', contract.uuid)



# below was copied from def customer and modified

@ login_required(login_url="/login")
@ permission_required("maintenance.view_contract", raise_exception=True)
def viewContract(request, uuid):
    contract = Contract.objects.get(uuid=uuid)
    price = float(contract.price)
    payments = float(contract.payments)
    # print(type(payments))
    payment_amount = price / payments
    visit_man_hours = float(0)
    visits = Visit.objects.filter(visit_contract=contract).order_by('visit_date')
    for visit in visits:
        visit_man_hours += float(visit.total_man_hours)
    # th = float(0)
    # th = sum(float(visit.total_man_hours))       
    # print(type(th))

    visits_count = visits.count()
    context = {'contract': contract, 'payment_amount': payment_amount, 'visits': visits, 'visits_count': visits_count, 'visit_man_hours': visit_man_hours}
    return render(request, 'maintenance/contract_view.html', context)


@ login_required(login_url="/login")
@ permission_required("maintenance.change_contract", raise_exception=True)
def updateContract(request, uuid):
    contract = Contract.objects.get(uuid=uuid)
    form = ContractForm(instance=contract)

    if request.method == 'POST':
        form = ContractForm(request.POST, instance=contract)
        if form.is_valid():
            form.save()
            return redirect('view_contract', uuid)
    context = {'form': form}
    return render(request, 'maintenance/contract_form.html', context)


@ login_required(login_url="/login")
@ permission_required("maintenance.delete_contract", raise_exception=True)
def deleteContract(request, uuid):
    contract = Contract.objects.get(uuid=uuid)
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
