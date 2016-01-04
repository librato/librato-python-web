from django.http import JsonResponse

from librato_python_web.instrumentor.context import _get_state


def index(request):
    """
    Return json array with states
    """
    return JsonResponse(_get_state())
