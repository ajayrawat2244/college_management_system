from django.contrib import admin
from .models import *

admin.site.register(College)
admin.site.register(CollegeSubscription)
admin.site.register(SubscriptionInvoice)
admin.site.register(SubscriptionPayment)
admin.site.register(FileAsset)