from django.template import loader
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist

import random

from .models import Bid, Session, Group, Participant, Winner


MAX_BDM_PRIZE = 300


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
            try:
                winner = Winner.objects.get(group_number = group.group_number, block = block)
                myoffer = Bid.objects.get(participant_id = participant_id, block = block).bid
                maxoffer = winner.maxoffer
                secondoffer = winner.secondoffer
                condition = "treatment" if participant_id == winner.winner else "control"          
                response = "|".join(map(str, [condition, maxoffer, secondoffer, myoffer]))
            except ObjectDoesNotExist:
                response = ""
            return HttpResponse(response)
        elif offer == "login":
            currentSession = Session.objects.latest('start')
            if currentSession.status == "open":
                try:
                    Participant.objects.get(participant_id = participant_id)
                    return HttpResponse("already_logged")
                    # participant = Participant.objects.get(participant_id = participant_id)
                    # if participant.frame == 0:
                    #     return HttpResponse("already_logged")
                    # else:
                    #     return HttpResponse("frame_" + str(participant.frame))
                except ObjectDoesNotExist:                    
                    currentSession.participants += 1
                    currentSession.save()
                    participant = Participant(participant_id = participant_id, group_number = -99, session = currentSession.session_number)
                    participant.save()         
                    return HttpResponse("login_successful")   
            elif currentSession.status == "ongoing":
                try:
                    participant = Participant.objects.get(participant_id = participant_id)
                    group = Group.objects.get(group_number = participant.group_number)
                    return HttpResponse("_".join(["start", str(group.bdm_one), str(group.bdm_two), group.condition]))
                except ObjectDoesNotExist:
                    return HttpResponse("ongoing")
            elif currentSession.status == "closed":
                return HttpResponse("closed")
            else:
                return HttpResponse("no_open")
        elif block == "-99":
            participant = Participant.objects.get(participant_id = participant_id)    
            participant.reward = offer
            participant.finished = True
            participant.save()
            return HttpResponse("ok")
        else:
            participant = Participant.objects.get(participant_id = participant_id) 
            bid = Bid(participant_id = participant_id, block = block, bid = offer, group_number = participant.group_number)
            bid.save()            
            group = Group.objects.get(group_number = participant.group_number)
            group_bids = Bid.objects.filter(block = block, group_number = participant.group_number)
            if len(group_bids) == group.participants:
                highest_bidder = []
                maxoffer = 0
                secondoffer = 0
                all_members = Participant.objects.filter(group_number = participant.group_number)
                for p in all_members:
                    b = Bid.objects.get(participant_id = p.participant_id, block = block)
                    bid = b.bid
                    if bid > maxoffer:
                        secondoffer = maxoffer
                        maxoffer = bid                        
                        highest_bidder = [b.participant_id]
                    elif bid == maxoffer:
                        secondoffer = maxoffer
                        highest_bidder.append(b.participant_id)
                    elif bid > secondoffer:
                        secondoffer = bid
                random.shuffle(highest_bidder)
                highest_bidder = highest_bidder[0]
                winner = Winner(group_number = group.group_number, block = block, winner = highest_bidder, maxoffer = maxoffer, secondoffer = secondoffer)
                winner.save()
            return HttpResponse("ok")


@login_required(login_url='/admin/login/')
def openSession(request, response = True):
    currentSession = Session.objects.latest('start')
    if currentSession.status == "closed":
        currentSession.status = "open"
    else:
        otherSessions = Session.objects.filter(status__in=["open", "ongoing", "closed"])
        for oldSession in otherSessions:
            oldSession.status = "finished"
            oldSession.save()
        currentSession = Session(status = "open")
    currentSession.save()    
    if response:
        return HttpResponse("Sezení {} otevřeno".format(currentSession.session_number))
    else:
        return "Sezení {} otevřeno".format(currentSession.session_number)


@login_required(login_url='/admin/login/')
def closeSession(request, response = True):
    try:
        currentSession = Session.objects.get(status = "open")    
        currentSession.status = "closed"    
        currentSession.save()
        text = "Sezení {} uzavřeno pro přihlašování".format(currentSession.session_number)
    except ObjectDoesNotExist:
        text = "Není otevřeno žádné sezení"
    if response:
        return HttpResponse(text)
    else:
        return text


@login_required(login_url='/admin/login/')
def endSession(request, response = True):
    try:
        currentSession = Session.objects.latest('start')
        if currentSession.status == "finished":
            text = "Poslední sezení bylo již ukončeno"
        else:
            currentSession.status = "finished"    
            currentSession.save()
            text = "Sezení {} ukončeno".format(currentSession.session_number)
    except ObjectDoesNotExist:
        text = "V databázi není žádné sezení"
    if response:
        return HttpResponse(text)
    else:
        return text


@login_required(login_url='/admin/login/')
def startSession(request, response = True):
    currentSession = Session.objects.latest('start')
    currentSession.status = "ongoing"
    currentSession.save()
    participants = Participant.objects.filter(session = currentSession.session_number)
    number = len(participants)
    groups = number//4
    assignment = [i for i in range(number)]
    random.shuffle(assignment)    
    num = 0
    for i in range(groups):
        bdm_one = random.randint(1, MAX_BDM_PRIZE)
        bdm_two = random.randint(1, MAX_BDM_PRIZE)
        condition = random.choice(["low", "high"])
        group = Group(session = currentSession.session_number, participants = 4, bdm_one = bdm_one, bdm_two = bdm_two)
        group.save()
        for j in range(4):
            p = participants[num]
            p.group_number = group.group_number
            p.save()
            num += 1
    if response:
        return HttpResponse("Sezení {} zahájeno s {} participanty".format(currentSession.session_number, currentSession.participants))
    else:
        return "Sezení {} zahájeno s {} participanty".format(currentSession.session_number, currentSession.participants)


@login_required(login_url='/admin/login/')
def administration(request):
    participants = {}
    status = ""
    if request.method == "POST" and request.POST['answer'].strip():
        answer = request.POST['answer']
        if "otevrit" in answer:
            info = openSession(request, response = False)            
        elif "spustit" in answer:
            info = startSession(request, response = False) 
        elif "uzavrit" in answer:
            info = closeSession(request, response = False) 
        elif "ukoncit" in answer:
            info = endSession(request, response = False) 
        else:
            info = "Toto není validní příkaz"
    else:        
        try:
            currentSession = Session.objects.latest('start')
        except ObjectDoesNotExist:
            info = "V databázi není žádné sezení"
        status = currentSession.status 
        if status == "open":
            info = "Přihlášeno {} participantů do sezení {}, které nebylo zatím spuštěno".format(currentSession.participants, currentSession.session_number)
        elif status == "ongoing":
            info = "Probíhá sezení {} s {} participanty".format(currentSession.session_number, currentSession.participants)
            parts = Participant.objects.filter(session = currentSession.session_number, finished = True)
            for part in parts:
                participants[part.participant_id] = part.reward
        elif status == "closed":
            info = "Přihlášeno {} participantů do sezení {}, které nebylo zatím spuštěno, ale je uzavřeno pro přihlašování".format(currentSession.participants, currentSession.session_number)
        elif status == "finished":
            info = "Poslední sezení {} bylo ukončeno".format(currentSession.session_number)
    localContext = {"info": info, "status": status, "participants": participants}
    template = loader.get_template('index.html')
    return HttpResponse(template.render(localContext, request))