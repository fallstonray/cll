import csv
import os
import re
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from datetime import date, timedelta
from django.db.models import Count, Sum
from .models import Bid, ChangeOrder, DailyLogEntry, BidDocument
from .forms import BidForm, BidUpdateForm, ChangeOrderForm, DailyLogEntryForm, BidDocumentForm
from .filters import BidFilter
from employee.models import Employee


# ── Document filename helpers ─────────────────────────────────────────────────

def _sanitize_slug(s):
    s = s.lower().strip()
    s = re.sub(r'[^\w\s]', '', s)
    s = re.sub(r'\s+', '_', s)
    return re.sub(r'_+', '_', s).strip('_')


def _build_doc_filename(bid, doc_type, other_desc, ext):
    project_slug = _sanitize_slug(bid.project_name)
    desc_slug = _sanitize_slug(other_desc or 'other') if doc_type == 'other' else doc_type
    base = f"{project_slug}_{desc_slug}"
    ext = ext.lower().lstrip('.')
    if doc_type == 'other':
        existing_count = bid.biddocument_set.filter(doc_type='other', other_desc=other_desc).count()
    else:
        existing_count = bid.biddocument_set.filter(doc_type=doc_type).count()
    if existing_count == 0:
        return f"{base}.{ext}"
    return f"{base}_{existing_count + 1}.{ext}"


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
def landscapeDashboard(request):
    today = date.today()

    active_projects_qs = Bid.objects.filter(phase__in=['awarded', 'likely']).exclude(status='completed')
    pipeline_qs = Bid.objects.filter(phase__in=['estimating', 'submitted', 'on_hold'])
    pending_cos_qs = ChangeOrder.objects.filter(status='pending')

    phase_counts = dict(
        Bid.objects.values_list('phase').annotate(n=Count('id'))
    )

    completed_qs = Bid.objects.filter(status='completed')
    warranties_expiring = sum(
        1 for b in completed_qs if b.end_date and 0 <= b.warranty_days_left <= 60
    )

    active_project_value = active_projects_qs.aggregate(total=Sum('amount'))['total'] or 0
    pipeline_value = pipeline_qs.aggregate(total=Sum('amount'))['total'] or 0
    pending_co_value = pending_cos_qs.aggregate(total=Sum('amount'))['total'] or 0
    completed_this_year = Bid.objects.filter(status='completed', end_date__year=today.year).count()

    active_projects = active_projects_qs.order_by('start_date')[:5]
    overdue_followups = Bid.objects.filter(
        next_follow_up__isnull=False,
        next_follow_up__lte=today,
    ).exclude(phase__in=['lost', 'dead']).exclude(status='completed').order_by('next_follow_up')[:5]
    pending_cos = pending_cos_qs.select_related('bid').order_by('date_submitted')[:10]

    top_customers = (
        Bid.objects.filter(customer__isnull=False)
        .values('customer__uuid', 'customer__name')
        .annotate(bid_count=Count('id'), total_value=Sum('amount'))
        .order_by('-bid_count')[:5]
    )
    top_states = (
        Bid.objects.filter(state__isnull=False, state__gt='')
        .values('state')
        .annotate(bid_count=Count('id'), total_value=Sum('amount'))
        .order_by('-bid_count')[:5]
    )

    context = {
        'phase_counts': phase_counts,
        'active_project_count': active_projects_qs.count(),
        'pipeline_count': pipeline_qs.count(),
        'pending_co_count': pending_cos_qs.count(),
        'warranties_expiring': warranties_expiring,
        'active_project_value': active_project_value,
        'pipeline_value': pipeline_value,
        'pending_co_value': pending_co_value,
        'completed_this_year': completed_this_year,
        'active_projects': active_projects,
        'overdue_followups': overdue_followups,
        'pending_cos': pending_cos,
        'top_customers': top_customers,
        'top_states': top_states,
    }
    return render(request, 'landscape/dashboard.html', context)


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

    filter_fields = {'project_name', 'state', 'estimator', 'customer', 'phase'}
    is_filtered = any(request.GET.get(f) for f in filter_fields)

    context = {
        'bids': bids,
        'bids_count': bids.count(),
        'myFilter': myFilter,
        'sort': sort,
        'order': order,
        'is_filtered': is_filtered,
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
    from django.db.models.functions import Cast
    change_orders = bid.changeorder_set.all().order_by(
        Case(
            When(status='approved', then=Value(0)),
            When(status='pending',  then=Value(1)),
            When(status='rejected', then=Value(2)),
            default=Value(3),
            output_field=IntegerField(),
        ),
        # Within approved: blank/null co_number sorts after numbered ones
        Case(
            When(status='approved', co_number__isnull=False, co_number__gt='', then=Value(0)),
            default=Value(1),
            output_field=IntegerField(),
        ),
        # Sort approved numbered COs numerically by co_number
        Case(
            When(status='approved', co_number__isnull=False, co_number__gt='', then=Cast('co_number', IntegerField())),
            default=Value(999999),
            output_field=IntegerField(),
        ),
        'date_submitted',
    )
    log_entries = bid.dailylogentry_set.all()  # ordered by Meta: -date, -created_at
    log_form = DailyLogEntryForm()
    doc_entries = bid.biddocument_set.order_by('doc_type', 'note')
    doc_form = BidDocumentForm()
    context = {
        'bid': bid,
        'bid_form': BidUpdateForm(instance=bid),
        'change_orders': change_orders,
        'log_entries': log_entries,
        'log_form': log_form,
        'doc_entries': doc_entries,
        'doc_form': doc_form,
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
            messages.success(request, "Bid updated.")
            return redirect('view_bid', uuid)
    return render(request, 'landscape/bid_form.html', {'form': form, 'action': 'Update Bid'})


@login_required(login_url="/login")
@permission_required('landscape.delete_bid', raise_exception=True)
def deleteBid(request, uuid):
    bid = Bid.objects.get(uuid=uuid)
    if request.method == 'POST':
        bid.delete()
        messages.success(request, "Bid deleted.")
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
            messages.success(request, "Change order added.")
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
            messages.success(request, "Change order updated.")
            return redirect('view_bid', co.bid.uuid)
    return render(request, 'landscape/co_form.html', {'form': form, 'bid': co.bid})


@login_required(login_url="/login")
@permission_required('landscape.delete_changeorder', raise_exception=True)
def deleteChangeOrder(request, uuid):
    co = ChangeOrder.objects.get(uuid=uuid)
    bid_uuid = co.bid.uuid
    if request.method == 'POST':
        co.delete()
        messages.success(request, "Change order deleted.")
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
            messages.success(request, "Log entry added.")
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
            messages.success(request, "Log entry updated.")
    return redirect('view_bid', bid_uuid)


@login_required(login_url="/login")
@permission_required('landscape.delete_dailylogentry', raise_exception=True)
def deleteLogEntry(request, uuid):
    entry = DailyLogEntry.objects.get(uuid=uuid)
    bid_uuid = entry.bid.uuid
    if request.method == 'POST':
        entry.delete()
        messages.success(request, "Log entry deleted.")
        return redirect('view_bid', bid_uuid)
    return render(request, 'landscape/bid_delete.html', {'item': entry})


# ── Document CRUD ─────────────────────────────────────────────────────────────

@login_required(login_url="/login")
@permission_required('landscape.add_biddocument', raise_exception=True)
def uploadDocument(request, uuid):
    bid = Bid.objects.get(uuid=uuid)
    if request.method == 'POST':
        form = BidDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc_type = form.cleaned_data['doc_type']
            note = form.cleaned_data.get('note', '')
            other_desc = note if doc_type == 'other' else ''
            uploaded_file = request.FILES['file']
            _, ext = os.path.splitext(uploaded_file.name)
            filename = _build_doc_filename(bid, doc_type, other_desc, ext)
            try:
                uploaded_by = Employee.objects.get(user=request.user)
            except Employee.DoesNotExist:
                uploaded_by = None
            doc = BidDocument(
                bid=bid,
                note=note,
                doc_type=doc_type,
                other_desc=other_desc,
                uploaded_by=uploaded_by,
            )
            doc.file.save(filename, uploaded_file, save=True)
            messages.success(request, "Document uploaded.")
    return redirect('view_bid', bid.uuid)


@login_required(login_url="/login")
@permission_required('landscape.change_biddocument', raise_exception=True)
def updateDocumentNote(request, uuid):
    doc = BidDocument.objects.get(uuid=uuid)
    bid_uuid = doc.bid.uuid
    if request.method == 'POST':
        doc.note = request.POST.get('note', '').strip()
        doc.save()
        messages.success(request, "Note updated.")
    return redirect('view_bid', bid_uuid)


@login_required(login_url="/login")
@permission_required('landscape.delete_biddocument', raise_exception=True)
def deleteDocument(request, uuid):
    doc = BidDocument.objects.get(uuid=uuid)
    bid_uuid = doc.bid.uuid
    if request.method == 'POST':
        doc.file.delete(save=False)
        doc.delete()
        messages.success(request, "Document deleted.")
        return redirect('view_bid', bid_uuid)
    return render(request, 'landscape/bid_delete.html', {'item': doc})
