from django.db import models


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
    group_number = models.AutoField(primary_key=True)   
    session = models.IntegerField(default=0)
    participants = models.IntegerField(default=0)
    condition = models.CharField(max_length=12, default="")
    winner = models.IntegerField(default=0)
    votes = models.IntegerField(default=0)
    winning_block = models.IntegerField(default=0)

    def __str__(self):
        field_values = []
        for field in self._meta.get_fields(): # pylint: disable=no-member
            field_values.append(str(getattr(self, field.name, '')))
        return '\t'.join(field_values)

class Participant(models.Model):
    participant_id = models.CharField(max_length=50, default="")  
    id_number = models.AutoField(primary_key=True) 
    group_number = models.IntegerField(default=0)    
    number_in_group = models.IntegerField(default=0)
    session = models.IntegerField(default=0)    
    time = models.DateTimeField(auto_now=True)
    wins_in_after = models.IntegerField(default=0)
    reward_in_after = models.IntegerField(default=0)
    finished_after = models.BooleanField(default=False)
    reward_in_fourth = models.IntegerField(default=0)
    finished_fourth = models.BooleanField(default=False)
    vote = models.IntegerField(default=0)
    finished = models.BooleanField(default=False, null=True)
    reward = models.IntegerField(default=0)
    pairNumber = models.IntegerField(default=0)    
    role = models.CharField(max_length=1, default="") 

    def __str__(self):
        field_values = []
        for field in self._meta.get_fields(): # pylint: disable=no-member
            field_values.append(str(getattr(self, field.name, '')))
        return '\t'.join(field_values)
  
class Pair(models.Model):
    pairNumber = models.AutoField(primary_key=True) 
    session = models.IntegerField(default=0)
    condition = models.CharField(max_length=20, default="") 
    roleA = models.CharField(max_length=50, default="") 
    roleB = models.CharField(max_length=50, default="")
    preparedA = models.BooleanField(default=False) 
    preparedB = models.BooleanField(default=False)

    def __str__(self):
        field_values = []
        for field in self._meta.get_fields(): # pylint: disable=no-member
            field_values.append(str(getattr(self, field.name, '')))
        return '\t'.join(field_values)

class Decision(models.Model):
    pairNumber = models.IntegerField(default=0)    
    roundNumber = models.IntegerField(default=0)    
    took = models.IntegerField(default=0)

    def __str__(self):
        field_values = []
        for field in self._meta.get_fields(): # pylint: disable=no-member
            field_values.append(str(getattr(self, field.name, '')))
        return '\t'.join(field_values)

class Response(models.Model):
    pairNumber = models.IntegerField(default=0)    
    decision = models.IntegerField(default=0)    
    response = models.CharField(max_length=10, default="")     
    message = models.IntegerField(default=0)    
    money = models.IntegerField(default=0)    

    def __str__(self):
        field_values = []
        for field in self._meta.get_fields(): # pylint: disable=no-member
            field_values.append(str(getattr(self, field.name, '')))
        return '\t'.join(field_values)
