from django.contrib import admin
from admincontact.models import AdminMessage,Crontask

# Register your models here.
admin.site.register(AdminMessage)
admin.site.register(Crontask)

