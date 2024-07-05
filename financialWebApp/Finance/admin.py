from django.contrib import admin
from .models import Student,LevelBill,Payment,Session

# Register your models here.
admin.site.register(Student)
admin.site.register(LevelBill)
admin.site.register(Payment)
admin.site.register(Session)