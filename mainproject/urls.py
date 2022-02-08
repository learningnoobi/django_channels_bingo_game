
from django.urls import path,include,re_path
from django.conf import settings
from django.views.static import serve

urlpatterns = [
    path('', include('bingo.urls')),
    # re_path(r'^static/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}),
] 

