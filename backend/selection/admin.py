from django.contrib import admin
from .models import Session, Group, Participant, Pair, Decision, Response

admin.site.register(Session)
admin.site.register(Participant)
admin.site.register(Group)
admin.site.register(Pair)
admin.site.register(Decision)
admin.site.register(Response)

