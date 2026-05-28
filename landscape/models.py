from django.db import models
from datetime import date, timedelta
import uuid


PHASE_CHOICES = [
    ('estimating', 'Estimating'),
    ('submitted', 'Submitted'),
    ('on_hold', 'On Hold'),
    ('likely', 'Likely'),
    ('awarded', 'Awarded'),
    ('lost', 'Lost'),
    ('dead', 'Dead'),
]

STATUS_CHOICES = [
    ('in_progress', 'In Progress'),
    ('scheduled', 'Scheduled'),
    ('paused', 'Paused'),
    ('delayed', 'Delayed'),
    ('completed', 'Completed'),
    ('waiting', 'Waiting'),
]

CO_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
]


class Bid(models.Model):
    project_name    = models.CharField(max_length=255)
    customer        = models.ForeignKey('maintenance.Customer', null=True, blank=True, on_delete=models.SET_NULL)
    location        = models.CharField(max_length=255, null=True, blank=True)
    city            = models.CharField(max_length=100, null=True, blank=True)
    state           = models.CharField(max_length=2, default='MD', blank=True)
    zip             = models.CharField(max_length=10, null=True, blank=True)
    amount          = models.FloatField(null=True, blank=True)
    estimator       = models.ForeignKey('employee.Employee', null=True, blank=True, on_delete=models.SET_NULL)
    phase           = models.CharField(max_length=20, choices=PHASE_CHOICES, default='estimating')
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, null=True, blank=True)
    bid_submitted   = models.DateField(null=True, blank=True)
    last_contact    = models.DateField(null=True, blank=True)
    next_follow_up  = models.DateField(null=True, blank=True)
    follow_up_notes = models.TextField(null=True, blank=True)
    start_date      = models.DateField(null=True, blank=True)
    end_date        = models.DateField(null=True, blank=True)
    contract_signed = models.BooleanField(default=False)
    warranty_days   = models.IntegerField(default=365, blank=True, help_text="Warranty period in days")
    notes           = models.TextField(null=True, blank=True)
    uuid            = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['next_follow_up', 'project_name']

    def __str__(self):
        return self.project_name

    @property
    def is_project(self):
        return self.phase in ('awarded', 'likely')

    @property
    def approved_co_total(self):
        return sum(co.amount for co in self.changeorder_set.filter(status='approved'))

    @property
    def warranty_expires(self):
        if self.end_date and self.warranty_days:
            return self.end_date + timedelta(days=self.warranty_days)
        return None

    @property
    def warranty_days_left(self):
        if self.warranty_expires:
            delta = self.warranty_expires - date.today()
            return delta.days
        return None


class ChangeOrder(models.Model):
    bid            = models.ForeignKey(Bid, on_delete=models.CASCADE)
    co_number      = models.CharField(max_length=50, null=True, blank=True, verbose_name='CO Number', help_text='Assigned only when status is Approved')
    name           = models.CharField(max_length=255)
    amount         = models.FloatField()
    status         = models.CharField(max_length=20, choices=CO_STATUS_CHOICES, default='pending')
    date_submitted = models.DateField(null=True, blank=True)
    scope_of_work  = models.TextField(null=True, blank=True)
    notes          = models.TextField(null=True, blank=True)
    uuid           = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at     = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} — {self.bid.project_name}"


DOC_TYPE_CHOICES = [
    ('proposal',         'Proposal'),
    ('signed_contract',  'Signed Contract'),
    ('estimating_sheet', 'Estimating Sheet'),
    ('plans',            'Plans'),
    ('change_order',     'Change Order'),
    ('other',            'Other'),
]


def _bid_doc_upload_path(instance, filename):
    return f"bid_documents/{instance.bid.uuid}/{filename}"


class BidDocument(models.Model):
    bid         = models.ForeignKey(Bid, on_delete=models.CASCADE)
    file        = models.FileField(upload_to=_bid_doc_upload_path)
    name        = models.CharField(max_length=255)
    doc_type    = models.CharField(max_length=20, choices=DOC_TYPE_CHOICES)
    other_desc  = models.CharField(max_length=100, blank=True)
    uploaded_by = models.ForeignKey('employee.Employee', null=True, blank=True, on_delete=models.SET_NULL)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uuid        = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.name


class DailyLogEntry(models.Model):
    bid        = models.ForeignKey(Bid, on_delete=models.CASCADE)
    date       = models.DateField(default=date.today)
    author     = models.ForeignKey('employee.Employee', null=True, blank=True, on_delete=models.SET_NULL)
    entry      = models.TextField()
    uuid       = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.date} — {self.bid.project_name}"
