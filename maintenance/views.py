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
from landscape.models import Bid, ChangeOrder
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
    today = date.today()
    contracts = Contract.objects.all()
    customers = Customer.objects.all()
    active_contracts = contracts.filter(end_date__gte=today)
    expire_list = active_contracts.filter(end_date__lte=today + timedelta(days=60)).order_by('end_date')
    amounts = active_contracts.values_list('price', flat=True)
    total_contracts_value = sum(amounts)
    visits_this_month = Visit.objects.filter(
        visit_date__year=today.year,
        visit_date__month=today.month,
    ).count()

    pipeline_phases = ['estimating', 'submitted', 'on_hold']
    project_phases = ['awarded', 'likely']
    pipeline_bids = Bid.objects.filter(phase__in=pipeline_phases)
    active_projects = Bid.objects.filter(phase__in=project_phases)
    pipeline_value = Bid.objects.filter(
        phase__in=pipeline_phases + project_phases
    ).aggregate(total=Sum('amount'))['total'] or 0
    pending_co_count = ChangeOrder.objects.filter(status='pending').count()
    landscape_snapshot = Bid.objects.filter(
        phase__in=pipeline_phases + project_phases
    ).order_by('-created_at')[:5]

    show_maintenance = request.user.is_superuser or request.user.groups.filter(name='Maintenance').exists()
    show_landscape = request.user.is_superuser or request.user.groups.filter(name='Landscape').exists()

    context = {
        'total_customers': customers.count(),
        'total_active_contracts': active_contracts.count(),
        'total_contracts_value': total_contracts_value,
        'expire_list': expire_list,
        'visits_this_month': visits_this_month,
        'pipeline_count': pipeline_bids.count(),
        'active_project_count': active_projects.count(),
        'pipeline_value': pipeline_value,
        'pending_co_count': pending_co_count,
        'landscape_snapshot': landscape_snapshot,
        'show_maintenance': show_maintenance,
        'show_landscape': show_landscape,
    }
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
def maintenanceDashboard(request):
    today = date.today()

    all_contracts = Contract.objects.all()
    active_contracts = all_contracts.filter(end_date__gte=today)
    expire_list = active_contracts.filter(end_date__lte=today + timedelta(days=60)).order_by('end_date')
    active_count = active_contracts.count()

    active_contract_value = active_contracts.aggregate(total=Sum('price'))['total'] or 0
    avg_contract_value = (active_contract_value / active_count) if active_count else 0

    visits_this_month = Visit.objects.filter(
        visit_date__year=today.year, visit_date__month=today.month
    ).count()
    visits_this_year = Visit.objects.filter(visit_date__year=today.year).count()
    man_hours_this_year = (
        Visit.objects.filter(visit_date__year=today.year)
        .aggregate(total=Sum('total_man_hours'))['total'] or 0
    )

    recent_visits = Visit.objects.select_related(
        'visit_contract', 'crew_leader', 'visit_type_name'
    ).order_by('-visit_date', '-created_at')[:5]

    service_mix = [
        ('Irrigation',        'irrigation',     active_contracts.filter(irrigation=True).count()),
        ('Turf Applications', 'turf_apps',      active_contracts.filter(turf_apps=True).count()),
        ('Aeration/Overseed', 'aeration',       active_contracts.filter(aeration_overseed=True).count()),
        ('Spring Flowers',    'spring_flowers', active_contracts.filter(flowers_spring__gt=0).count()),
        ('Fall Flowers',      'fall_flowers',   active_contracts.filter(flowers_fall__gt=0).count()),
        ('Mulch',             'mulch',          active_contracts.filter(mulch_yd__gt=0).count()),
    ]

    top_customers = (
        active_contracts.filter(site_customer__isnull=False)
        .values('site_customer__uuid', 'site_customer__name')
        .annotate(contract_count=Count('id'), total_value=Sum('price'))
        .order_by('-contract_count')[:5]
    )

    by_salesrep = (
        active_contracts.filter(salesrep__isnull=False)
        .values('salesrep__salesman')
        .annotate(contract_count=Count('id'), total_value=Sum('price'))
        .order_by('-contract_count')
    )

    context = {
        'active_count': active_count,
        'expire_count': expire_list.count(),
        'expire_list': expire_list,
        'total_customers': Customer.objects.count(),
        'visits_this_month': visits_this_month,
        'active_contract_value': active_contract_value,
        'avg_contract_value': avg_contract_value,
        'visits_this_year': visits_this_year,
        'man_hours_this_year': man_hours_this_year,
        'recent_visits': recent_visits,
        'service_mix': service_mix,
        'top_customers': top_customers,
        'by_salesrep': by_salesrep,
    }
    return render(request, 'maintenance/maint_dashboard.html', context)


@ login_required(login_url="/login")
@ permission_required("maintenance.view_contract", raise_exception=True)
def maintenance(request):
    all_contracts = Contract.objects.all()
    contracts_count = all_contracts.count()

    myFilter = ContractFilter(request.GET, queryset=all_contracts)
    contracts = myFilter.qs

    SERVICE_FILTERS = {
        'irrigation':     ('Irrigation',        {'irrigation': True}),
        'turf_apps':      ('Turf Applications', {'turf_apps': True}),
        'aeration':       ('Aeration/Overseed', {'aeration_overseed': True}),
        'spring_flowers': ('Spring Flowers',    {'flowers_spring__gt': 0}),
        'fall_flowers':   ('Fall Flowers',      {'flowers_fall__gt': 0}),
        'mulch':          ('Mulch',             {'mulch_yd__gt': 0}),
    }

    sort_fields = {
        'customer':  'site_customer__name',
        'site_name': 'site_name',
    }
    sort  = request.GET.get('sort', 'site_name')
    order = request.GET.get('order', 'asc')
    field = sort_fields.get(sort, 'site_name')

    service_key = request.GET.get('service')
    service_label = None
    active_contracts = contracts.filter(end_date__gte=datetime.now())
    if service_key in SERVICE_FILTERS:
        service_label, service_q = SERVICE_FILTERS[service_key]
        active_contracts = active_contracts.filter(**service_q)
    active_contracts = active_contracts.order_by(f'-{field}' if order == 'desc' else field)
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
               'contracts_count': contracts_count, 'myFilter': myFilter,
               'total_active_contracts': total_active_contracts,
               'sort': sort, 'order': order,
               'service_label': service_label, 'service_key': service_key}

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
