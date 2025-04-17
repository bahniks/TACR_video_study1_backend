from django.db import models
from django.utils import timezone



class Participant(models.Model):
    participant_id = models.CharField(max_length=50, default="")  
    time = models.DateTimeField(auto_now=True)
    finished = models.BooleanField(default=False, null=True)
    reward = models.IntegerField(default=0)
    screen = models.IntegerField(default=0)
    lastprogress = models.DateTimeField(default=timezone.now)

    def __str__(self):
        field_values = []
        for field in self._meta.get_fields(): # pylint: disable=no-member
            field_values.append(str(getattr(self, field.name, '')))
        return '\t'.join(field_values)
