from django.shortcuts import render, redirect
from .models import *
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, permission_required
from .forms import VisitForm
from .filters import VisitsFilter
# Create your views here.


@ login_required(login_url="/login")
def visits(request):
    visits = Visit.objects.all()
    visits_count = visits.count()
    myFilter = VisitsFilter(request.GET, queryset=visits)
    visits = myFilter.qs
    context = {
        'visits': visits, 'visits_count': visits_count, 'myFilter': myFilter,
    }
    return render(request, 'visits/visits.html', context)


@ login_required(login_url="/login")
@ permission_required("visits.add_visit", login_url="/login", raise_exception=True)
def createVisit(request):
    form = VisitForm()
    if request.method == 'POST':
        form = VisitForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/visits/')

    context = {'form': form}
    return render(request, 'visits/visit_form.html', context)


@ login_required(login_url="/login")
def viewVisit(request, uuid):
    visit = Visit.objects.get(uuid=uuid)
    context = {'visit': visit}
    return render(request, 'visits/visit_view.html', context)


@ login_required(login_url="/login")
def updateVisit(request, uuid):
    visit = Visit.objects.get(uuid=uuid)
    form = VisitForm(instance=visit)
    if request.method == 'POST':
        form = VisitForm(request.POST, instance=visit)
        if form.is_valid():
            form.save()
            return redirect('view_visit', uuid)
    return render(request, 'visits/visit_form.html', {'form': form})


@ login_required(login_url="/login")
def deleteVisit(request, uuid):
    visit = Visit.objects.get(uuid=uuid)
    if request.method == 'POST':
        visit.delete()
        return redirect('/visits/')
    return render(request, 'visits/visit_delete.html', {'item': visit})
