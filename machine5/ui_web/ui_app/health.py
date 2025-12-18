from django.http import JsonResponse
import requests
from django.conf import settings

def health_check(request):
    """
    Endpoint de santé pour Consul
    """
    health_status = {
        "service": "ui-web",
        "status": "healthy",
        "dependencies": {}
    }
    
    # Vérifier la connectivité avec les services backend
    services = {
        "auth": settings.AUTH_SERVICE_URL,
        "menu": settings.MENU_SERVICE_URL,
        "order": settings.ORDER_SERVICE_URL
    }
    
    for service_name, service_url in services.items():
        try:
            response = requests.get(f"{service_url}/health/", timeout=2)
            health_status["dependencies"][service_name] = "ok" if response.status_code == 200 else "error"
        except:
            health_status["dependencies"][service_name] = "unreachable"
    
    return JsonResponse(health_status, status=200)