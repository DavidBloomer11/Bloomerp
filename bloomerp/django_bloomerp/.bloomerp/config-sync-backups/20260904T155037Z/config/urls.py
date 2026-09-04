from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from django.conf import settings

def healthcheck(_request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", healthcheck, name="healthcheck"),
    path("", include("bloomerp.urls")),
    path("", include("config.project_urls")),
]

if settings.DEBUG:
    urlpatterns.append(
        path("__reload__/", include("django_browser_reload.urls")),
    )
