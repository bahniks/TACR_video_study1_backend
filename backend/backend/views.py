from django.http import HttpResponse

def manager(request):
    if request.method == "GET":
        return HttpResponse("test")
