from django.shortcuts import render, redirect
from .models import *
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, permission_required
from .forms import VisitForm

# Create your views here.


@ login_required(login_url="/login")
def visits(request):
    visits = Visit.objects.all()
    context = {
        'visits': visits
    }
    return render(request, 'visits/visits.html', context)


@ login_required(login_url="/login")
@ permission_required("visit.add_customer", login_url="/login", raise_exception=True)
def createVisit(request):
    form = VisitForm(initial={'visit': visit})
    if request.method == 'POST':
        # print('Printing POST:', request.POST)
        form = VisitForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/')

    context = {'form': form}
    return render(request, 'visits/visit_form.html', context)


# @ login_required(login_url="/login")
# def maintenance(request):
#     contracts = Contract.objects.all()
#     contracts_count = contracts.count()
#     myFilter = ContractFilter(request.GET, queryset=contracts)
#     contracts = myFilter.qs
#     context = {'contracts': contracts,
#                'contracts_count': contracts_count, 'myFilter': myFilter}

#     return render(request, 'maintenance/maintenance.html', context)
