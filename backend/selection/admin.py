from django.contrib import admin
from .models import Session, Group, Participant

admin.site.register(Session)
admin.site.register(Participant)
admin.site.register(Group)

