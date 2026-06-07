from django.contrib import admin
from .models import *

admin.site.register(FeeStructure)
admin.site.register(StudentFeeAccount)
admin.site.register(FeeInvoice)