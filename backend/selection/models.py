from django.db import models


class Session(models.Model):
    session_number = models.AutoField(primary_key=True) 
    start = models.DateTimeField(auto_now_add=True)
    participants = models.IntegerField(default = 0)
    status = models.CharField(max_length=10, default="closed")
       
    # def __str__(self):
    #     field_values = []
    #     for field in self._meta.get_fields(): # pylint: disable=no-member
    #         field_values.append(str(getattr(self, field.name, '')))
    #     return '\t'.join(field_values)


class Group(models.Model):
    group_number = models.AutoField(primary_key=True)   
    session = models.IntegerField(default=0)
    participants = models.IntegerField(default=0)
    bdm_one = models.IntegerField(default=0)
    bdm_two = models.IntegerField(default=0)
    condition = models.CharField(max_length=5, default="")


class Winner(models.Model):
    group_number = models.IntegerField(default=0)      
    block = models.IntegerField(default=0)
    winner = models.CharField(max_length=50, default="")
    maxoffer = models.IntegerField(default=0)
    secondoffer = models.IntegerField(default=0)


class Participant(models.Model):
    participant_id = models.CharField(max_length=50, default="")  
    group_number = models.IntegerField(default=0)
    session = models.IntegerField(default=0)
    finished = models.BooleanField(default=False)
    reward = models.IntegerField(default=0)
    #frame = models.IntegerField(default=0)
    

class Bid(models.Model):
    participant_id = models.CharField(max_length=50, default="")
    block = models.IntegerField(default=0)
    bid = models.IntegerField(default=0)
    time = models.DateTimeField(auto_now_add=True)
    group_number = models.IntegerField(default=0)