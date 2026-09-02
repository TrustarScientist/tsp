# apps/core/views.py — new file
from django.http import HttpResponse

def whoami(request):
    if request.tenant:
        return HttpResponse(f"Resolved tenant: {request.tenant.name} ({request.tenant.subdomain})")
    return HttpResponse("No tenant resolved.")