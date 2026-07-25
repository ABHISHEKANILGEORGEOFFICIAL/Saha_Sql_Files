from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('communityapp.urls')),
    path('api/', include('Adminapp.urls')),
    path('api/', include('Guestapp.urls')),
    path('api/teacher/', include('Teacherapp.urls')),
    path('api/', include('communityapp.urls')),
    path('api/', include('Teacherapp.urls')),
    path('api/', include('studentapp.studentapp_urls')),
    path('api/chat/', include('chat.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
