import csv
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, permission_required
from datetime import date, timedelta
from .models import Bid, ChangeOrder, DailyLogEntry
from .forms import BidForm, BidUpdateForm, ChangeOrderForm, DailyLogEntryForm
from .filters import BidFilter
from employee.models import Employee


# ── List / Pipeline Views ─────────────────────────────────────────────────────

PIPELINE_SORT_FIELDS = {
    'project_name': 'project_name',
    'customer':     'customer__name',
    'city':         'city',
    'state':        'state',
    'amount':       'amount',
    'phase':        'phase',
    'estimator':    'estimator__last_name',
    'bid_submitted':'bid_submitted',
}

ACTIVE_SORT_FIELDS = {
    'project_name': 'project_name',
    'customer':     'customer__name',
    'city':         'city',
    'state':        'state',
    'amount':       'amount',
    'status':       'status',
    'start_date':   'start_date',
    'end_date':     'end_date',
}

COMPLETED_SORT_FIELDS = {
    'project_name': 'project_name',
    'customer':     'customer__name',
    'city':         'city',
    'state':        'state',
    'amount':       'amount',
    'end_date':     'end_date',
}


@login_required(login_url="/login")
@permission_required('landscape.view_bid', raise_exception=True)
def bidPipeline(request):
    """Active bid pipeline — estimating/submitted/on_hold/lost/dead only."""
    bids = Bid.objects.exclude(phase__in=['awarded', 'likely'])
    myFilter = BidFilter(request.GET, queryset=bids)

    sort  = request.GET.get('sort', 'bid_submitted')
    order = request.GET.get('order', 'desc')
    field = PIPELINE_SORT_FIELDS.get(sort, 'bid_submitted')
    bids  = myFilter.qs.order_by(f'-{field}' if order == 'desc' else field)

    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="bid_pipeline.csv"'
        writer = csv.writer(response)
        headers = ['Project Name', 'Customer / GC', 'City', 'State', 'Phase', 'Estimator', 'Bid Submitted']
        if request.user.is_superuser:
            headers.append('Amount')
        writer.writerow(headers)
        for bid in bids:
            row = [
                bid.project_name,
                str(bid.customer) if bid.customer else '',
                bid.city or '',
                bid.state or '',
                bid.get_phase_display(),
                str(bid.estimator) if bid.estimator else '',
                bid.bid_submitted or '',
            ]
            if request.user.is_superuser:
                row.append(bid.amount or '')
            writer.writerow(row)
        return response

    context = {
        'bids': bids,
        'bids_count': bids.count(),
        'myFilter': myFilter,
        'sort': sort,
        'order': order,
    }
    return render(request, 'landscape/bid_pipeline.html', context)


@login_required(login_url="/login")
@permission_required('landscape.view_bid', raise_exception=True)
def activeProjects(request):
    """Awarded projects that are not yet completed."""
    sort  = request.GET.get('sort', 'start_date')
    order = request.GET.get('order', 'asc')
    field = ACTIVE_SORT_FIELDS.get(sort, 'start_date')
    projects = Bid.objects.filter(phase__in=['awarded', 'likely']).exclude(status='completed').order_by(
        f'-{field}' if order == 'desc' else field
    )
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="active_projects.csv"'
        writer = csv.writer(response)
        headers = ['Project Name', 'Customer / GC', 'City', 'State', 'Status', 'Start Date', 'End Date']
        if request.user.is_superuser:
            headers += ['Amount', 'Approved COs']
        writer.writerow(headers)
        for p in projects:
            row = [
                p.project_name,
                str(p.customer) if p.customer else '',
                p.city or '',
                p.state or '',
                p.get_status_display() if p.status else '',
                p.start_date or '',
                p.end_date or '',
            ]
            if request.user.is_superuser:
                row += [p.amount or '', p.approved_co_total or '']
            writer.writerow(row)
        return response

    total_amount = sum(p.amount for p in projects if p.amount)

    context = {
        'projects': projects,
        'projects_count': projects.count(),
        'total_amount': total_amount,
        'sort': sort,
        'order': order,
    }
    return render(request, 'landscape/active_projects.html', context)


@login_required(login_url="/login")
@permission_required('landscape.view_bid', raise_exception=True)
def completedProjects(request):
    """Completed projects with warranty info."""
    sort  = request.GET.get('sort', 'end_date')
    order = request.GET.get('order', 'desc')
    field = COMPLETED_SORT_FIELDS.get(sort, 'end_date')
    projects = Bid.objects.filter(status='completed').order_by(
        f'-{field}' if order == 'desc' else field
    )

    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="completed_projects.csv"'
        writer = csv.writer(response)
        headers = ['Project Name', 'Customer / GC', 'City', 'State', 'End Date', 'Warranty Expires', 'Days Left']
        if request.user.is_superuser:
            headers.append('Amount')
        writer.writerow(headers)
        for p in projects:
            row = [
                p.project_name,
                str(p.customer) if p.customer else '',
                p.city or '',
                p.state or '',
                p.end_date or '',
                p.warranty_expires or '',
                p.warranty_days_left if p.warranty_days_left is not None else '',
            ]
            if request.user.is_superuser:
                row.append(p.amount or '')
            writer.writerow(row)
        return response

    context = {
        'projects': projects,
        'projects_count': projects.count(),
        'sort': sort,
        'order': order,
    }
    return render(request, 'landscape/completed_projects.html', context)


# ── Bid CRUD ──────────────────────────────────────────────────────────────────

@login_required(login_url="/login")
@permission_required('landscape.add_bid', raise_exception=True)
def createBid(request):
    today = date.today()

    # Try to find the logged-in user's Employee record to pre-populate estimator
    try:
        estimator = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        estimator = None

    initial = {
        'bid_submitted':  today,
        'last_contact':   today,
        'next_follow_up': today + timedelta(days=7),
        'estimator':      estimator,
        'phase':          'estimating',
    }

    form = BidForm(initial=initial)
    if request.method == 'POST':
        form = BidForm(request.POST)
        if form.is_valid():
            instance = form.save()
            return redirect('view_bid', instance.uuid)
    return render(request, 'landscape/bid_form.html', {'form': form, 'action': 'Create Bid'})


@login_required(login_url="/login")
@permission_required('landscape.view_bid', raise_exception=True)
def viewBid(request, uuid):
    bid = Bid.objects.get(uuid=uuid)
    from django.db.models import Case, When, Value, IntegerField
    change_orders = bid.changeorder_set.all().order_by(
        Case(
            When(status='approved', then=Value(0)),
            When(status='pending',  then=Value(1)),
            When(status='rejected', then=Value(2)),
            default=Value(3),
            output_field=IntegerField(),
        ),
        'date_submitted',
    )
    log_entries = bid.dailylogentry_set.all()  # ordered by Meta: -date, -created_at
    log_form = DailyLogEntryForm()
    context = {
        'bid': bid,
        'change_orders': change_orders,
        'log_entries': log_entries,
        'log_form': log_form,
    }
    return render(request, 'landscape/bid_view.html', context)


@login_required(login_url="/login")
@permission_required('landscape.change_bid', raise_exception=True)
def updateBid(request, uuid):
    bid = Bid.objects.get(uuid=uuid)
    form = BidUpdateForm(instance=bid)
    if request.method == 'POST':
        form = BidUpdateForm(request.POST, instance=bid)
        if form.is_valid():
            form.save()
            return redirect('view_bid', uuid)
    return render(request, 'landscape/bid_form.html', {'form': form, 'action': 'Update Bid'})


@login_required(login_url="/login")
@permission_required('landscape.delete_bid', raise_exception=True)
def deleteBid(request, uuid):
    bid = Bid.objects.get(uuid=uuid)
    if request.method == 'POST':
        bid.delete()
        return redirect('bid_pipeline')
    return render(request, 'landscape/bid_delete.html', {'item': bid})


# ── Change Order CRUD ─────────────────────────────────────────────────────────

@login_required(login_url="/login")
@permission_required('landscape.view_bid', raise_exception=True)
def viewChangeOrder(request, uuid):
    co = ChangeOrder.objects.get(uuid=uuid)
    return render(request, 'landscape/co_view.html', {'co': co})


@login_required(login_url="/login")
@permission_required('landscape.add_changeorder', raise_exception=True)
def addChangeOrder(request, uuid):
    bid = Bid.objects.get(uuid=uuid)
    form = ChangeOrderForm(initial={'date_submitted': date.today()})
    if request.method == 'POST':
        form = ChangeOrderForm(request.POST)
        if form.is_valid():
            co = form.save(commit=False)
            co.bid = bid
            co.save()
            return redirect('view_bid', bid.uuid)
    return render(request, 'landscape/co_form.html', {'form': form, 'bid': bid})


@login_required(login_url="/login")
@permission_required('landscape.change_changeorder', raise_exception=True)
def updateChangeOrder(request, uuid):
    co = ChangeOrder.objects.get(uuid=uuid)
    form = ChangeOrderForm(instance=co)
    if request.method == 'POST':
        form = ChangeOrderForm(request.POST, instance=co)
        if form.is_valid():
            form.save()
            return redirect('view_bid', co.bid.uuid)
    return render(request, 'landscape/co_form.html', {'form': form, 'bid': co.bid})


@login_required(login_url="/login")
@permission_required('landscape.delete_changeorder', raise_exception=True)
def deleteChangeOrder(request, uuid):
    co = ChangeOrder.objects.get(uuid=uuid)
    bid_uuid = co.bid.uuid
    if request.method == 'POST':
        co.delete()
        return redirect('view_bid', bid_uuid)
    return render(request, 'landscape/bid_delete.html', {'item': co})


# ── Daily Log CRUD ────────────────────────────────────────────────────────────

@login_required(login_url="/login")
@permission_required('landscape.add_dailylogentry', raise_exception=True)
def addLogEntry(request, uuid):
    bid = Bid.objects.get(uuid=uuid)
    if request.method == 'POST':
        form = DailyLogEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.bid = bid
            # Auto-set author from the logged-in user's Employee record
            try:
                entry.author = Employee.objects.get(user=request.user)
            except Employee.DoesNotExist:
                entry.author = None
            entry.save()
    return redirect('view_bid', bid.uuid)


@login_required(login_url="/login")
@permission_required('landscape.change_dailylogentry', raise_exception=True)
def updateLogEntry(request, uuid):
    entry = DailyLogEntry.objects.get(uuid=uuid)
    bid_uuid = entry.bid.uuid
    if request.method == 'POST':
        form = DailyLogEntryForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
    return redirect('view_bid', bid_uuid)


@login_required(login_url="/login")
@permission_required('landscape.delete_dailylogentry', raise_exception=True)
def deleteLogEntry(request, uuid):
    entry = DailyLogEntry.objects.get(uuid=uuid)
    bid_uuid = entry.bid.uuid
    if request.method == 'POST':
        entry.delete()
        return redirect('view_bid', bid_uuid)
    return render(request, 'landscape/bid_delete.html', {'item': entry})
