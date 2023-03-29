from django.contrib import admin
from .models import Session, Group, Participant, Bid, Winner

admin.site.register(Session)
admin.site.register(Participant)
admin.site.register(Group)
admin.site.register(Bid)
admin.site.register(Winner)
