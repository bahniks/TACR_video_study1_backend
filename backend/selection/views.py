from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

import random

from .models import Bid, Session


@csrf_exempt 
def manager(request):
    if request.method == "GET":
        return HttpResponse("test")
    elif request.method == "POST":
        participant_id = request.POST.get("id")
        block = request.POST.get("round")
        offer = request.POST.get("offer")
        if offer == "result":
            participant = Participant.objects.get(participant_id = participant_id)            
            group = Group.objects.get(group_number = participant.group_number)
            all_members = Participant.objects.filter(group_number = participant.group_number)
            bids = []
            for p in all_members:
                b = Bid.objects.get(participant_id = p.participant_id, block = block)
                if p.participant_id == participant_id:
                    myoffer = b.bid
                bids.append(b.bid)
            if len(bids) == group.participants:
                response = "|".join(map(str, [condition, maxoffer, secondoffer, myoffer]))
            else:
                response = ""
            return HttpResponse(response)
        elif offer == "login":
            currentSession = Session.objects.latest('start')
            currentSession.participants += 1
            currentSession.save()
            participant = Participant(participant_id = participant_id, group_number = -99, session = currentSession)
            participant.save()         
            return HttpResponse("ok")   
        else:
            bid = Bid(participant_id = participant_id, block = block, bid = offer)
            bid.save()
            return HttpResponse("ok")

        

@login_required(login_url='/admin/login/')
def openSession(request):
    session = Session()
    session.save()


@login_required(login_url='/admin/login/')
def startSession(request):
    currentSession = Session.objects.latest('start')
    participants = Participant.filter(session = currentSession)
    number = len(participants)
    groups = number//4
    assignment = [i for i in range(number)]
    random.shuffle(assignment)    
    num = 0
    for i in range(groups):
        group = Group(session = currentSession, participants = 4)
        group.save()
        for j in range(4):
            p = participants[num]
            p.group_number = group.group_number
            p.save()
            num += 1


@login_required(login_url='/admin/login/')
def sessionInfo(request):
    pass