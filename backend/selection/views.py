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
    if request.method == "GET":
        return HttpResponse("test")
    elif request.method == "POST":
        #print(request.POST)
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
                    p = Participant.objects.get(participant_id = participant_id)
                    if p.group_number == -99:
                        return HttpResponse("not_grouped")
                    group = Group.objects.get(group_number = p.group_number)
                    lastpair = Pair.objects.get(pairNumber = p.pair6)                    
                    trustPairs = f"{p.pair3}_{p.pair4}_{p.pair5}_{p.pair6}"                    
                    trustRoles = []
                    for i in range(3,7):
                        pair = Pair.objects.get(pairNumber = getattr(p, f"pair{i}"))
                        role = "A" if pair.roleA == participant_id else "B"
                        trustRoles.append(role)
                    trustRoles = "".join(trustRoles)
                    response = "|".join(["start", group.condition, group.reward_order, str(lastpair.token), str(p.winning_block), str(p.winning_trust), trustRoles, trustPairs, str(p.id)])
                    return HttpResponse(response)
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
            # receiving results from a trust game 
            participant = Participant.objects.get(participant_id = participant_id)                                      
            pair = Pair.objects.get(pairNumber = getattr(participant, f"pair{int(block) + 2}"))
            if pair.preparedA and pair.preparedB and pair.sentB >= 0:
                response = "_".join(map(str, [block, pair.sentA, pair.sentB]))
            else:
                response = ""                
            return HttpResponse(response)            
        elif block == "paidtoken":
            # saving information whether a token was paid
            participant = Participant.objects.get(participant_id = participant_id)            
            participant.token = bool(offer)
            participant.save()
            return HttpResponse("ok")
        elif offer == "outcome":
            # sending information about outcome of the other participants
            participant = Participant.objects.get(participant_id = participant_id)  
            pair = Pair.objects.get(pairNumber = getattr(participant, f"pair{block}"))
            other = pair.roleA if pair.roleB == participant_id else pair.roleB        
            try:
                outcome = Outcome.objects.get(participant_id = other, roundNumber = block)
            except ObjectDoesNotExist:
                return HttpResponse("False")
            version = outcome.version
            if block == "6":
                if not pair.token:
                    version += "_control"
                else:
                    otherParticipant = Participant.objects.get(participant_id = other)                
                    version += "_contributed" if otherParticipant.paidtoken else "_notContributed"
            response = "|".join(["outcome", str(outcome.wins), str(outcome.reward), version]) + "_True"         
            return HttpResponse(response)
        elif block.startswith("trust"):
            # saving outcome from trust
            block = block.lstrip("_trust")
            participant = Participant.objects.get(participant_id = participant_id)  
            pair = Pair.objects.get(pairNumber = getattr(participant, f"pair{int(block) + 2}"))  
            offers = offer.split("_")     
            if pair.roleA == participant_id:
                pair.preparedA = True
                pair.sentA = int(offers[6])
                pair.save()
                if pair.preparedB:
                    resolvePair(pair.pairNumber)
            else:
                pair.preparedB = True                
                pair.returns = "_".join(offers[:6])
                pair.save()
                if pair.preparedA:
                    resolvePair(pair.pairNumber)      
            return HttpResponse("ok")      
        elif offer.startswith("outcome"):
            # saving outcome from dice
            participant = Participant.objects.get(participant_id = participant_id)  
            _, wins, reward, version = offer.split("|")            
            outcome = Outcome(participant_id = participant_id, roundNumber = block, wins = wins, reward = reward, version = version)  
            outcome.save()
            return HttpResponse("ok")
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
 
     


def resolvePair(pairNumber):
    pair = Pair.objects.get(pairNumber = pairNumber)
    if not pair.preparedA or not pair.preparedB:
        return
    returns = pair.returns.split("_")
    which = int(pair.sentA * 5 / pair.endowment)
    pair.sentB = returns[which]
    pair.save()


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
    
    participants = [participant.participant_id for participant in Participant.objects.filter(session = currentSession.session_number)]
    if len(participants) < 6:
        if response:
            return HttpResponse("Není přihlášeno 6 participantů, experiment nelze spustit")
        else:
            return "Není přihlášeno 6 participantů, experiment nelze spustit"

    currentSession.status = "ongoing"
    currentSession.save()

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
        for pid in ps:
            p = Participant.objects.get(participant_id = pid)
            p.group_number = group.group_number
            p.save()
        for r, pairs in generate_rounds(ps, check = len(participants) == 6).items():
            round_pairings[r].extend(pairs)

    all_pairings = list(itertools.combinations(participants, 2))  
    all_pairings = [(i[0], i[1]) if i[0] < i[1] else (i[1], i[0]) for i in all_pairings]
    used_pairs = [x for xs in round_pairings.values() for x in xs]
    used_pairs = [(i[0], i[1]) if i[0] < i[1] else (i[1], i[0]) for i in used_pairs]
    unused_pairs = list(set(all_pairings) - set(used_pairs))
    round_pairings[3] = generate_third(unused_pairs, participants)
        
    for r, pairing in round_pairings.items():
        for thispair in pairing:
            currentPair = list(thispair)
            random.shuffle(currentPair)        
            pA, pB = currentPair[0], currentPair[1]
            pAobj = Participant.objects.get(participant_id = pA)        
            pBobj = Participant.objects.get(participant_id = pB)        
            g = Group.objects.get(group_number = pAobj.group_number)
            condition = g.condition if r != 3 else ""
            token = random.choice([True, False]) if r == 6 else None
            e = ["middle"] + g.reward_order.split("-") + ["middle"]
            endowments = {"low": 50, "middle": 100, "high": 200}
            if token:
                pAobj.token = True
                pBobj.token = True
            pair = Pair(session = currentSession.session_number, roundNumber = r, condition = condition, token = token, roleA = pA, roleB = pB, endowment = endowments[e[r-3]])
            pair.save()
            setattr(pAobj, f"pair{r}", pair.pairNumber)
            setattr(pBobj, f"pair{r}", pair.pairNumber)
            pAobj.save()
            pBobj.save()

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

        for i in range(3,7):            
            pair = Pair.objects.get(pairNumber = getattr(participant, f"pair{i}"))
            if pair.roleA == participant_id and not pair.preparedA:
                pair.preparedA = True
                pair.sentA = pair.endowment
                pair.save()
                if pair.preparedB:
                    resolvePair(pair.pairNumber)
            elif pair.roleB == participant_id and not pair.preparedB:
                pair.preparedB = True
                pair.returns = "_".join([str(int((sent * 2 * pair.endowment) / 5)) for sent in range(6)])
                pair.save()
                if pair.preparedA:
                    resolvePair(pair.pairNumber)                          

            try:
                outcome = Outcome.objects.get(participant_id = participant_id, roundNumber = i) 
            except ObjectDoesNotExist:
                outcome = Outcome(participant_id = participant_id, roundNumber = i, wins = 6, reward = 63, version = "control")         
                outcome.save()

            if participant.paidtoken is None:
                participant.paidtoken = False

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