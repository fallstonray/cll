from django.contrib import admin
from .models import *
from visits.models import Visit, VisitType

# Models for main app 'maintenance'

admin.site.register(Customer)
admin.site.register(Contract)
admin.site.register(Soldby)
admin.site.register(Mulchcolor)


# Models for 2nd app 'visits'
admin.site.register(Visit)
admin.site.register(VisitType)
