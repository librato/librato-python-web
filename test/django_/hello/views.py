from django.http import HttpResponse, HttpResponseNotFound


def index(request):
    return HttpResponse("Welcome to the hello app!")


def error_notfound(request):
    return HttpResponseNotFound("Verify this text!")


def error_5xx(request):
    return HttpResponse(status=500)


def error_exception(request):
    raise Exception("Unexpected app exception")
