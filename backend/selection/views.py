from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist

import random

from .models import Bid, Session, Group, Participant


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
            group_bids = getBids(participant_id, block)
            bids = group_bids["bids"]
            myoffer = group_bids["myoffer"]
            if len(bids) == group.participants:
                bids.sort()
                maxoffer = bids[len(bids) - 1]
                secondoffer = bids[len(bids) - 2]
                condition = "treatment" if myoffer == maxoffer else "control" # upravit pro rovnost                
                response = "|".join(map(str, [condition, maxoffer, secondoffer, myoffer]))
            else:
                response = ""
            return HttpResponse(response)
        elif offer == "login":
            currentSession = Session.objects.latest('start')
            currentSession.participants += 1
            currentSession.save()
            participant = Participant(participant_id = participant_id, group_number = -99, session = currentSession.session_number)
            participant.save()         
            return HttpResponse("ok")   
        else:
            bid = Bid(participant_id = participant_id, block = block, bid = offer)
            bid.save()
            participant = Participant.objects.get(participant_id = participant_id) 
            group = Group.objects.get(group_number = participant.group_number)
            group_bids = getBids(participant_id, block)["bids"]
            if len(group_bids) == group.participants:
                pass # vybrat, kdo vyhral a ulozit do Group auction
            return HttpResponse("ok")


def getBids(participant_id, block):
        participant = Participant.objects.get(participant_id = participant_id)            
        group = Group.objects.get(group_number = participant.group_number)
        all_members = Participant.objects.filter(group_number = participant.group_number)
        bids = []
        for p in all_members:
            try:
                b = Bid.objects.get(participant_id = p.participant_id, block = block)
            except ObjectDoesNotExist:
                pass
            if p.participant_id == participant_id:
                myoffer = b.bid
            bids.append(b.bid)
        return {"bids": bids, "myoffer": myoffer}


@login_required(login_url='/admin/login/')
def openSession(request):
    session = Session()
    session.save()
    return HttpResponse("Session {} otevřena".format(session.session_number))


@login_required(login_url='/admin/login/')
def startSession(request):
    currentSession = Session.objects.latest('start')
    participants = Participant.objects.filter(session = currentSession.session_number)
    number = len(participants)
    groups = number//4
    assignment = [i for i in range(number)]
    random.shuffle(assignment)    
    num = 0
    for i in range(groups):
        group = Group(session = currentSession.session_number, participants = 4)
        group.save()
        for j in range(4):
            p = participants[num]
            p.group_number = group.group_number
            p.save()
            num += 1
    return HttpResponse("Session {} zahájena s {} participanty".format(currentSession.session_number, currentSession.participants))


@login_required(login_url='/admin/login/')
def sessionInfo(request):
    pass