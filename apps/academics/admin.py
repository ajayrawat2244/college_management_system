from django.contrib import admin
from .models import *

admin.site.register(AcademicYear)
admin.site.register(Term)
admin.site.register(Department)
admin.site.register(Program)
admin.site.register(Batch)
admin.site.register(Section)
admin.site.register(Subject)
admin.site.register(Enrollment)
admin.site.register(SubjectOffering)
admin.site.register(TimetableEntry)