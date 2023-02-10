from django.shortcuts import render, redirect
from .models import *
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, permission_required
from .forms import EmployeeForm

# Create your views here.


@ login_required(login_url="/login")
def employees(request):
    employees = Employee.objects.all()
    employees_count = employees.count()
    context = {
        'employees': employees, 'employees_count': employees_count,
    }
    return render(request, 'employee/employees.html', context)


@ login_required(login_url="/login")
@ permission_required("visit.add_visit", login_url="/login", raise_exception=True)
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
def viewEmployee(request, pk):
    employee = Employee.objects.get(id=pk)
    context = {'employee': employee}
    return render(request, 'employee/employee_view.html', context)


@ login_required(login_url="/login")
def updateEmployee(request, pk):
    employee = Employee.objects.get(id=pk)
    form = EmployeeForm(instance=employee)

    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            return redirect('view_employee', pk)
    context = {'form': form}
    return render(request, 'employee/employee_form.html', context)
