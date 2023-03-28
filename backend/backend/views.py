from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

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
            response = "|".join(["treatment", 30, 20, 30]) #!
            return HttpResponse(response)
        else:
            bid = Bid(participant_id = participant_id, block = block, bid = offer)
            bid.save()
            return HttpResponse("ok")

        
