from django.contrib import admin
from .models import Bid, ChangeOrder, DailyLogEntry

admin.site.register(Bid)
admin.site.register(ChangeOrder)
admin.site.register(DailyLogEntry)
