from django.db import models
from django.utils import timezone


class Session(models.Model):
    session_number = models.AutoField(primary_key=True) 
    start = models.DateTimeField(auto_now_add=True)
    participants = models.IntegerField(default = 0)
    status = models.CharField(max_length=10, default="closed")

    def __str__(self):
        field_values = []
        for field in self._meta.get_fields(): # pylint: disable=no-member
            field_values.append(str(getattr(self, field.name, '')))
        return '\t'.join(field_values)

class Group(models.Model):
    # group with 4 or 6 players having the same combination of condition and reward order
    group_number = models.AutoField(primary_key=True)   
    session = models.IntegerField(default=0)
    participants = models.IntegerField(default=0)
    condition = models.CharField(max_length=12, default="")
    reward_order = models.CharField(max_length=12, default="") # high-low or low-high

    def __str__(self):
        field_values = []
        for field in self._meta.get_fields(): # pylint: disable=no-member
            field_values.append(str(getattr(self, field.name, '')))
        return '\t'.join(field_values)

class Participant(models.Model):
    participant_id = models.CharField(max_length=50, default="")  
    group_number = models.IntegerField(default=0)    
    session = models.IntegerField(default=0)    
    time = models.DateTimeField(auto_now=True)
    winning_block = models.IntegerField(default=0)
    winning_trust = models.IntegerField(default=0)
    finished = models.BooleanField(default=False, null=True)
    reward = models.IntegerField(default=0)
    token = models.BooleanField(default=False)
    screen = models.IntegerField(default=0)
    lastprogress = models.DateTimeField(default=timezone.now)

    def __str__(self):
        field_values = []
        for field in self._meta.get_fields(): # pylint: disable=no-member
            field_values.append(str(getattr(self, field.name, '')))
        return '\t'.join(field_values)
  
class Pair(models.Model):
    # pairing for a single round
    pairNumber = models.AutoField(primary_key=True) 
    session = models.IntegerField(default=0)
    roundNumber = models.IntegerField(default=0)    
    endowment = models.IntegerField(default=0)  
    condition = models.CharField(max_length=20, default="") 
    token = models.BooleanField(default=None, null=True)
    returns = models.CharField(max_length=40, default="") 
    returned = models.IntegerField(default=0)
    roleA = models.CharField(max_length=50, default="") 
    roleB = models.CharField(max_length=50, default="")
    preparedA = models.BooleanField(default=False) 
    preparedB = models.BooleanField(default=False)

    def __str__(self):
        field_values = []
        for field in self._meta.get_fields(): # pylint: disable=no-member
            field_values.append(str(getattr(self, field.name, '')))
        return '\t'.join(field_values)

class Outcome(models.Model):
    # outcome of the dice task
    participant_id = models.CharField(max_length=50, default="") 
    roundNumber = models.IntegerField(default=0)     
    wins = models.IntegerField(default=0)    
    reward = models.IntegerField(default=0)    
    version = models.CharField(max_length=10, default="")     

    def __str__(self):
        field_values = []
        for field in self._meta.get_fields(): # pylint: disable=no-member
            field_values.append(str(getattr(self, field.name, '')))
        return '\t'.join(field_values)