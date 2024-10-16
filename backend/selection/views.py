from django.template import loader
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from time import localtime, strftime
from collections import Counter

import random
import os
import zipfile
import itertools

from .models import Session, Group, Participant, Pair, Outcome
from .combinations import generate_rounds, generate_third





@csrf_exempt 
def manager(request):
    # TODO
    if request.method == "GET":
        return HttpResponse("test")
    elif request.method == "POST":
        participant_id = request.POST.get("id")
        block = request.POST.get("round")
        offer = request.POST.get("offer")
        if offer == "progress":
            participant = Participant.objects.get(participant_id = participant_id)            
            participant.screen = int(block)
            participant.lastprogress = timezone.now()
            participant.save()
            return HttpResponse("ok")  
        elif offer == "login":
            # login screen
            try:
                currentSession = Session.objects.latest('start')
            except ObjectDoesNotExist:
                return HttpResponse("no_open")
            if currentSession.status == "open":
                try:
                    Participant.objects.get(participant_id = participant_id)
                    return HttpResponse("already_logged")
                except ObjectDoesNotExist:                    
                    currentSession.participants += 1
                    currentSession.save()                    
                    participant = Participant(participant_id = participant_id, group_number = -99, session = currentSession.session_number, winning_block = random.randint(1,6), winning_trust = random.randint(3,6))
                    participant.save()         
                    return HttpResponse("login_successful")   
            elif currentSession.status == "ongoing":
                try:
                    participant = Participant.objects.get(participant_id = participant_id)
                    if participant.group_number == -99:
                        return HttpResponse("not_grouped")
                    group = Group.objects.get(group_number = participant.group_number)
                    return HttpResponse("_".join(["start", group.condition, str(participant.number_in_group), str(group.winning_block), str(participant.id)]))
                except ObjectDoesNotExist:
                    return HttpResponse("ongoing")
            elif currentSession.status == "closed":
                try:
                    Participant.objects.get(participant_id = participant_id)
                    return HttpResponse("already_logged")
                except ObjectDoesNotExist:       
                    return HttpResponse("closed")
            else:
                return HttpResponse("no_open")
        elif block == "-99":
            # uploading reward at the end
            participant = Participant.objects.get(participant_id = participant_id)    
            participant.reward = offer
            participant.finished = True
            participant.save()
            return HttpResponse("ok")
        elif offer == "trust":
            # getting result of voting
            participant = Participant.objects.get(participant_id = participant_id)            
            group = Group.objects.get(group_number = participant.group_number)
            condition = "treatment" if participant.number_in_group == group.winner else "control"                                
            response = "_".join(map(str, [condition, group.winner, group.votes]))                                        
            return HttpResponse(response)
        elif offer == "token":
            pass
        elif offer == "outcome":
            pass
        elif "trust" in offer:
            pass
        elif offer.starstwith("outcome"):
            pass
        elif "outcome" in offer:
            # outcome of the AFTER version in the third round
            participant = Participant.objects.get(participant_id = participant_id)            
            group = Group.objects.get(group_number = participant.group_number)
            if offer == "outcome":       
                finishedParticipants = Participant.objects.filter(group_number = group.group_number).exclude(finished_after = False)
                all_completed = len(finishedParticipants) == group.participants
                response = "outcome_"
                for i in range(4):       
                    p = Participant.objects.get(group_number = group.group_number, number_in_group = i+1)             
                    wins = str(p.wins_in_after) if not p.finished is None else "-99"
                    response += "|".join([str(p.number_in_group), wins, str(p.reward_in_after)]) + "_"
                response += str(all_completed)
                return HttpResponse(response)
            else:
                # uploading the outcome
                if block == "3":
                    _, winsInAfter, rewardInAfter = offer.split("|")
                    participant.wins_in_after = winsInAfter
                    participant.reward_in_after = rewardInAfter
                    participant.finished_after = True
                elif block == "4":
                    _, rewardInFourth = offer.split("|")
                    participant.reward_in_fourth = rewardInFourth
                    participant.finished_fourth = True
                participant.save()
                return HttpResponse("ok")
        elif offer == "result":
            # sending outcome of all group members in the fourth round
            participant = Participant.objects.get(participant_id = participant_id)            
            group = Group.objects.get(group_number = participant.group_number)  
            finishedParticipants = Participant.objects.filter(group_number = group.group_number).exclude(finished_fourth = False)
            all_completed = len(finishedParticipants) == group.participants
            response = "result"
            for i in range(4):       
                p = Participant.objects.get(group_number = group.group_number, number_in_group = i+1)    
                if p.finished is None:
                    response += "_-99"         
                else:                    
                    response += "_" + str(p.reward_in_fourth)
            response += "_" + str(all_completed)
            return HttpResponse(response)            
        elif offer == "continue":           
            try:
                participant = Participant.objects.get(participant_id = participant_id)
                currentSession = Session.objects.latest('start')
            except ObjectDoesNotExist:
                return HttpResponse("no")
            if participant.session == currentSession.session_number and currentSession.status == "ongoing":
                return HttpResponse("continue")
            else:
                return HttpResponse("no")
        elif offer == "pairing":
            participant = Participant.objects.get(participant_id = participant_id)                 
            pair = Pair.objects.get(pairNumber = participant.pairNumber)
            if participant.role == "A":
                pair.preparedA = True                                
            else:
                pair.preparedB = True
            pair.save()
            if not (pair.preparedA and pair.preparedB):
                return HttpResponse("")
            else:
                pairNumber = pair.pairNumber
                role = participant.role
                condition = pair.condition
                response = "_".join([str(pairNumber), role, condition])
                return HttpResponse(response)         
        elif block == "dictator1A" or block == "dictator2A":
            participant = Participant.objects.get(participant_id = participant_id)                 
            roundNumber = int(block.lstrip("dictator").rstrip("A"))
            decision = Decision(pairNumber = participant.pairNumber, roundNumber = roundNumber, took = int(offer))
            decision.save()            
            return HttpResponse("ok")
        elif block == "dictator1B":
            participant = Participant.objects.get(participant_id = participant_id)                 
            responses = offer.split("_")
            for r in responses:
                decision, response, message, money = r.split("|")
                response = Response(pairNumber = participant.pairNumber, decision = int(decision), response = response, message = int(message), money = int(money))
                response.save()
            return HttpResponse("ok")
        elif offer == "decision1":
            participant = Participant.objects.get(participant_id = participant_id) 
            pair = Pair.objects.get(pairNumber = participant.pairNumber)            
            try:
                pairNumber = pair.pairNumber
                decision = Decision.objects.get(pairNumber = pairNumber, roundNumber = 1)                                
                took = decision.took                
                response = Response.objects.get(pairNumber = pairNumber, decision = took)
                data = "_".join(map(str, [pairNumber, took, response.response, response.message, response.money])) 
                return HttpResponse(data)
            except ObjectDoesNotExist:
                return HttpResponse("")
        elif offer == "decision2":
            participant = Participant.objects.get(participant_id = participant_id) 
            pair = Pair.objects.get(pairNumber = participant.pairNumber)            
            try:
                pairNumber = pair.pairNumber
                decision = Decision.objects.get(pairNumber = pairNumber, roundNumber = 2)                
                data = "_".join(map(str, [pairNumber, decision.took]))    
                return HttpResponse(data)
            except ObjectDoesNotExist:
                return HttpResponse("")            
        else:
            # TODO
            pass




def results_path():
    if not os.path.exists("results/"):
        os.mkdir("results/")
        # with(open(".gitignore", mode = "w")) as f:
        #     f.write("*\n!.gitignore")
    return "results/"


@csrf_exempt 
def results(request):  
    uploaded_file = request.FILES["results"]
    with open(results_path() + uploaded_file.name, "wb") as f:
        for chunk in uploaded_file.chunks():
            f.write(chunk)
    return HttpResponse("ok")



@login_required(login_url='/admin/login/')
def download(request):
    file_path = results_path()
    files = os.listdir(file_path)
    if ".gitignore" in files:
        files.remove(".gitignore")
    files_to_remove = [x for x in files if x.endswith(".zip")]
    for f in files_to_remove:
        os.remove(os.path.join(file_path, f))
        files.remove(f)
    writeTime = localtime()
    try:
        currentSession = Session.objects.latest('start').session_number
    except ObjectDoesNotExist:
        currentSession = "X"
    zip_filename = "data_Selection3_{}_{}_{}.zip".format(strftime("%y_%m_%d_%H%M%S", writeTime), currentSession, len(files))
    zip_file_path = os.path.join(file_path, zip_filename)
    with zipfile.ZipFile(zip_file_path, "w") as zip_file:
        for file in files:
            file_full_path = os.path.join(file_path, file)
            zip_file.write(file_full_path, file)
    with open(zip_file_path, "rb") as f:
        response = HttpResponse(f.read(), content_type="application/zip")
        response["Content-Disposition"] = "attachment; filename={}".format(zip_filename)
        return response  




@login_required(login_url='/admin/login/')
def openSession(request, response = True):
    try:
        currentSession = Session.objects.latest('start')
    except ObjectDoesNotExist:
        currentSession = None
    if currentSession and currentSession.status == "closed":
        currentSession.status = "open"
    elif currentSession and currentSession.status == "ongoing":
        if response:
            return HttpResponse("Není možné otevřít nové sezení, když je spuštěné jiné sezení")
        else:
            return "Není možné otevřít nové sezení, když je spuštěné jiné sezení"
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
    try:
        currentSession = Session.objects.latest('start')
        if currentSession.status == "finished" or currentSession.status == "ongoing":
            raise Exception
    except Exception:
        if response:
            return HttpResponse("Není zahájeno žádné sezení")
        else:
            return "Není zahájeno žádné sezení"        
    currentSession.status = "ongoing"
    currentSession.save()
    participants = [participant.participant_id for participant in Participant.objects.filter(session = currentSession.session_number)]

    random.shuffle(participants)
    if len(participants) % 2 != 0:
        removed = participants.pop()
    round_pairings = {x:[] for x in range(3,7)}
    num_groups = len(participants) // 4
    for i in range(num_groups):
        if i == num_groups - 1:
            ps = participants[slice(4*i, len(participants))]
        else:
            ps = participants[slice(4*i, 4*i+4)]
        condition = random.choice(["control", "version", "reward", "version_reward"])
        reward_order = random.choice(["high-low", "low-high"])
        group = Group(session = currentSession.session_number, participants = len(ps), condition = condition, reward_order = reward_order)
        group.save()        
        for p in ps:
            p = Participant.objects.get(participant_id = p)
            p.group = group.group_number
            p.save()
        for r, pairs in generate_rounds(ps).items():
            round_pairings[r].extend(pairs)

    all_pairings = list(itertools.combinations(participants, 2))  
    all_pairings = [(i[0], i[1]) if i[0] < i[1] else (i[1], i[0]) for i in all_pairings]
    used_pairs = [x for xs in round_pairings.values() for x in xs]
    used_pairs = [(i[0], i[1]) if i[0] < i[1] else (i[1], i[0]) for i in used_pairs]
    unused_pairs = list(set(all_pairings) - set(used_pairs))
    round_pairings[3] = generate_third(unused_pairs, participants)
        
    for r, pairing in round_pairings.items():
        incentive = "TODO"
        currentPair = list(pairing)
        random.shuffle(currentPair)
        pA, pB = *currentPair
        pAobj = Participant.objects.get(participant_id = pA)        
        pBobj = Participant.objects.get(participant_id = pB)                
        g = Group.objects.get(group_number = p.group_number)
        condition = g.condition if r != 3 else ""
        token = random.choice([True, False]) if r == 7 else None
        endowments = ["middle"] + g.reward_order.split("-") + ["middle"]
        if token:
            pAobj.token = True
            pBobj.token = True
            pAobj.save()
            pBobj.save()
        pair = Pair(session = currentSession.session_number, roundNumber = r, condition = condition, token = token, roleA = pA, roleB = pB, endowment = endowments[r-3])
        pair.save()

    if response:
        return HttpResponse("Sezení {} zahájeno s {} participanty".format(currentSession.session_number, len(participants)))
    else:
        return "Sezení {} zahájeno s {} participanty".format(currentSession.session_number, len(participants))


def showEntries(objectType):
    entries = objectType.objects.all() # pylint: disable=no-member
    if not entries:
        return None
    else:
        fields = [field.name for field in objectType._meta.get_fields()] # pylint: disable=no-member
        content = "\t".join(fields) + "\n" + "\n".join([str(entry) for entry in entries])
        return content


def downloadData(content, filename):
    response = HttpResponse(content, content_type="text/plain,charset=utf8")
    response['Content-Disposition'] = 'attachment; filename={0}.txt'.format(filename)
    return response


@login_required(login_url='/admin/login/')
def downloadAll(request):
    file_path = results_path()
    files = os.listdir(file_path)
    if ".gitignore" in files:
        files.remove(".gitignore")
    tables = {"Sessions": Session, "Groups": Group, "Participants": Participant, "Pairs": Pair, "Outcomes": Outcome}
    for table, objectType in tables.items():        
        content = showEntries(objectType)
        filename = table + ".txt"
        files.append(filename)
        with open(os.path.join(file_path, filename), mode = "w") as f:
            if content:
                f.write(content)
            else:
                f.write("")
    files_to_remove = [x for x in files if x.endswith(".zip")]
    for f in files_to_remove:
        os.remove(os.path.join(file_path, f))
        files.remove(f)
    writeTime = localtime()
    try:
        currentSession = Session.objects.latest('start').session_number
    except ObjectDoesNotExist:
        currentSession = "X"
    zip_filename = "all_data_Selection2_{}_{}_{}.zip".format(strftime("%y_%m_%d_%H%M%S", writeTime), currentSession, len(files) - len(tables))
    zip_file_path = os.path.join(file_path, zip_filename)
    with zipfile.ZipFile(zip_file_path, "w") as zip_file:
        for file in files:
            file_full_path = os.path.join(file_path, file)
            zip_file.write(file_full_path, file)
    for table in tables:
        filename = os.path.join(file_path, table + ".txt")
        if os.path.exists(filename):
            os.remove(filename)
    with open(zip_file_path, "rb") as f:
        response = HttpResponse(f.read(), content_type="application/zip")
        response["Content-Disposition"] = "attachment; filename={}".format(zip_filename)
        return response      


@login_required(login_url='/admin/login/')
def delete(request):
    Session.objects.all().delete() # pylint: disable=no-member
    Group.objects.all().delete() # pylint: disable=no-member
    Participant.objects.all().delete() # pylint: disable=no-member
    Pair.objects.all().delete()
    Outcome.objects.all().delete()
    return HttpResponse("Databáze vyčištěna")


@login_required(login_url='/admin/login/')
def deleteData(request):
    file_path = results_path()
    files = os.listdir(file_path)    
    for f in files:
        if not ".gitignore" in f:            
            os.remove(os.path.join(file_path, f))
    return HttpResponse("Data smazána")


def removeParticipant(participant_id):
    # TODO
    try:
        participant = Participant.objects.get(participant_id = participant_id) 
        if participant.finished:
            return("Participant již sezení ukončil")
        elif participant.finished is None:
            return("Participant již byl přeskočen")
        else:
            participant.finished = None
            participant.save()
        session = Session.objects.get(session_number = participant.session)
        if session.status != "ongoing":
            return("Participant není z aktivního sezení")
        pair = Pair.objects.get(pairNumber = participant.pairNumber)
        if participant.role == "A":
            pair.preparedA = True       
            decision1 = Decision(pairNumber = participant.pairNumber, roundNumber = 1, took = 0)
            decision1.save()                                
            decision2 = Decision(pairNumber = participant.pairNumber, roundNumber = 2, took = 0)
            decision2.save()                                
        else:
            pair.preparedB = True
            for r in range(6):
                message = random.randint(1,2)
                res = random.randint(0,1)
                response = Response(pairNumber = participant.pairNumber, decision = r*2, response = pair.condition.split("-")[res], message = message, money = 0)
                response.save()  
        pair.save()      
        group = Group.objects.get(group_number = participant.group_number)
        group.participants -= 1
        group.save()
        group_votes = Participant.objects.filter(group_number = participant.group_number).exclude(vote = 0).exclude(finished = None)
        if len(group_votes) == group.participants:
            determineWinner(participant.group_number)
        return("Participant bude ve studii přeskočen")
    except ObjectDoesNotExist as e:
        return("Participant s daným id nenalezen")



@login_required(login_url='/admin/login/')
def administration(request):
    participants = {}
    waiting = {}
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
        elif "ukazat" in answer or "data" in answer:
            info = "Hotovo"            
            if "vse" in answer and ("data" in answer or "stahnout"):
                return downloadAll(request)
            pattern = {"sezeni": Session, "skupiny": Group, "participant": Participant, "pary": Pair, "vysledky": Outcome}
            for key in pattern:
                if key in answer:
                    content = showEntries(pattern[key])
                    break 
            else:      
                content = None
            if not content:                
                info = "Data požadovaného typu nenalezena"
            elif "ukazat" in answer:
                return HttpResponse(content, content_type='text/plain')
            else:
                filename = {"sezeni": "Sessions", "skupiny": "Groups", "participant": "Participants", "pary": "Pairs", "vysledky": "Outcome"}[key]
                return downloadData(content, filename)
        elif "stahnout" in answer:
            info = "Hotovo" 
            return(download(request))
        elif "preskocit" in answer:
            splitted = answer.split()
            if len(splitted) != 2:
                info = "Participantovo id neuvedeno správně"
            else:
                participant_id = splitted[1].strip()
                info = removeParticipant(participant_id)
        else:
            info = "Toto není validní příkaz"
    else:        
        try:
            currentSession = Session.objects.latest('start')
            participantsInSession = Participant.objects.filter(session = currentSession.session_number)
            numberOfParticipants = len(participantsInSession)
            status = currentSession.status 
            if status == "open":
                info = "Přihlášeno {} participantů do sezení {}, které nebylo zatím spuštěno".format(numberOfParticipants, currentSession.session_number)
            elif status == "ongoing":
                info = "Probíhá sezení {} s {} participanty".format(currentSession.session_number, numberOfParticipants)
                parts = Participant.objects.filter(session = currentSession.session_number, finished = True).order_by("time")
                for part in parts:
                    files = os.listdir(results_path())                    
                    filePresent = any(part.participant_id in file for file in files)
                    participants[part.participant_id] = {"reward": part.reward, "file": filePresent}
                waits = Participant.objects.filter(session = currentSession.session_number, finished = False).order_by("lastprogress")
                waiting = {}
                for wait in waits:
                    duration = timezone.now() - wait.lastprogress
                    if duration.seconds > 300:
                        waiting[wait.participant_id] = {"group": wait.group_number, "screen": wait.screen, "time": duration.seconds}
            elif status == "closed":
                info = "Přihlášeno {} participantů do sezení {}, které nebylo zatím spuštěno, ale je uzavřeno pro přihlašování".format(numberOfParticipants, currentSession.session_number)
            elif status == "finished":
                info = "Poslední sezení {} bylo ukončeno".format(currentSession.session_number)
        except ObjectDoesNotExist:
            info = "V databázi není žádné sezení"
        except Exception as e:
            info = e
    localContext = {"info": info, "status": status, "participants": participants, "waiting": waiting}
    template = loader.get_template('index.html')
    return HttpResponse(template.render(localContext, request))