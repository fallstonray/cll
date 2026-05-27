from django.shortcuts import render, redirect
from .models import *
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, permission_required
from .forms import EmployeeForm

# Create your views here.


EMPLOYEE_SORT_FIELDS = {
    'first_name': 'first_name',
    'last_name':  'last_name',
    'position':   'employee_title__employee_title',
}

def _employee_list(request, active):
    sort  = request.GET.get('sort', 'last_name')
    order = request.GET.get('order', 'asc')
    field = EMPLOYEE_SORT_FIELDS.get(sort, 'last_name')
    qs = Employee.objects.filter(is_active=active).order_by(
        f'-{field}' if order == 'desc' else field
    )
    return qs, sort, order


@ login_required(login_url="/login")
def employees(request):
    qs, sort, order = _employee_list(request, active=True)
    context = {
        'employees': qs,
        'employees_count': qs.count(),
        'show_inactive': False,
        'sort': sort,
        'order': order,
    }
    return render(request, 'employee/employees.html', context)


@ login_required(login_url="/login")
def inactive_employees(request):
    qs, sort, order = _employee_list(request, active=False)
    context = {
        'employees': qs,
        'employees_count': qs.count(),
        'show_inactive': True,
        'sort': sort,
        'order': order,
    }
    return render(request, 'employee/employees.html', context)


@ login_required(login_url="/login")
@ permission_required("employee.add_employee", login_url="/login", raise_exception=True)
def createEmployee(request):
    form = EmployeeForm()
    # form = VisitForm(initial={'visit': visit})
    if request.method == 'POST':
        # print('Printing POST:', request.POST)
        form = EmployeeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/employees/')

    context = {'form': form}
    return render(request, 'employee/employee_form.html', context)


@ login_required(login_url="/login")
def viewEmployee(request, uuid):
    employee = Employee.objects.get(uuid=uuid)
    context = {'employee': employee}
    return render(request, 'employee/employee_view.html', context)


@ login_required(login_url="/login")
def updateEmployee(request, uuid):
    employee = Employee.objects.get(uuid=uuid)
    form = EmployeeForm(instance=employee)

    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            return redirect('view_employee', uuid)
    context = {'form': form}
    return render(request, 'employee/employee_form.html', context)
