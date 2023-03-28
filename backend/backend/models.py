from django.db import models
import uuid


class Session(models.Model):
    start = models.DateTimeField(auto_now_add=True)
    

class Bid(models.Model):
    participant_id = models.CharField(max_length=50, default="")
    block = models.IntegerField(default=0)
    bid = models.IntegerField(default=0)    
    
    def __str__(self):
        field_values = []
        for field in self._meta.get_fields(): # pylint: disable=no-member
            field_values.append(str(getattr(self, field.name, '')))
        return '\t'.join(field_values)   