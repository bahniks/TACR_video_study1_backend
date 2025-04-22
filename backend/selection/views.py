from django.template import loader
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.db import transaction

from time import localtime, strftime
from collections import Counter

import random
import os
import zipfile
import itertools

from .models import Participant



frames = ["Initial",
          "Intro",
          "Login",    
          "VideoIntro1",
          "VideoIntro2",
          "Sound",
          "Videos", "JOL", "IMI1", "Quiz1",
          "VideoIntro4",
          "Videos", "JOL", "IMI2", "Quiz2",
          "VideoIntro5",
          "Selection",
          "VideoIntro6",
          "Videos", "Videos", "Videos", "Videos", "Videos",
          "IMI3",
          "Quiz3",
          "QuestInstructions",
          "NFC",
          "Boredom",
          "Hexaco",
          "Social",
          "Demographics",
          "Comments",
          "Ending"
         ]



@csrf_exempt 
def manager(request):
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
            try:
                Participant.objects.get(participant_id = participant_id)
                return HttpResponse("already_logged")
            except ObjectDoesNotExist:                                  
                participant = Participant(participant_id = participant_id)
                participant.save()         
                return HttpResponse("start")  
        elif block == "-99":
            # uploading reward at the end
            participant = Participant.objects.get(participant_id = participant_id)    
            participant.reward = offer
            participant.finished = True
            participant.save()
            return HttpResponse("ok")
        elif offer == "continue":           
            try:
                participant = Participant.objects.get(participant_id = participant_id)
            except ObjectDoesNotExist:
                return HttpResponse("no")
            if participant.time - timezone.now() < timezone.timedelta(minutes=90):
                return HttpResponse("continue")
            else:
                return HttpResponse("no")
     

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
    zip_filename = "data_TACR1_{}_{}.zip".format(strftime("%y_%m_%d_%H%M%S", writeTime), len(files))
    zip_file_path = os.path.join(file_path, zip_filename)
    with zipfile.ZipFile(zip_file_path, "w") as zip_file:
        for file in files:
            file_full_path = os.path.join(file_path, file)
            zip_file.write(file_full_path, file)
    with open(zip_file_path, "rb") as f:
        response = HttpResponse(f.read(), content_type="application/zip")
        response["Content-Disposition"] = "attachment; filename={}".format(zip_filename)
        return response  


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
    tables = {"Participants": Participant}
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
    zip_filename = "all_data_TACR1_{}_{}_{}.zip".format(strftime("%y_%m_%d_%H%M%S", writeTime), len(files) - len(tables))
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
    Participant.objects.all().delete() # pylint: disable=no-member
    return HttpResponse("Databáze vyčištěna")


@login_required(login_url='/admin/login/')
def deleteData(request):
    file_path = results_path()
    files = os.listdir(file_path)    
    for f in files:
        if not ".gitignore" in f:            
            os.remove(os.path.join(file_path, f))
    return HttpResponse("Data smazána")




@login_required(login_url='/admin/login/')
def administration(request):
    participants = {}
    waiting = {}
    status = ""
    if request.method == "POST" and request.POST['answer'].strip():
        answer = request.POST['answer']
        if "ukazat" in answer or "data" in answer:
            info = "Hotovo"            
            if "vse" in answer and ("data" in answer or "stahnout"):
                return downloadAll(request)
            pattern = {"participant": Participant}
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
                filename = {"participant": "Participants"}[key]
                return downloadData(content, filename)
        elif "stahnout" in answer:
            info = "Hotovo" 
            return(download(request))   
        else:
            info = "Toto není validní příkaz"
    else:        
        try:
            recentParticipants = Participant.objects.filter(time__gte=timezone.now() - timezone.timedelta(minutes=90))
            activeParticipants = recentParticipants.filter(finished = False)           
            info = "Přihlášeno {} participantů".format(len(activeParticipants))
            parts = recentParticipants.filter(finished = True).order_by("time")
            for part in parts:
                files = os.listdir(results_path())                    
                filePresent = any(part.participant_id in file for file in files)
                participants[part.participant_id] = {"reward": part.reward, "file": filePresent}
        except Exception as e:
            info = e
    localContext = {"info": info, "participants": participants}
    template = loader.get_template('index.html')
    return HttpResponse(template.render(localContext, request))