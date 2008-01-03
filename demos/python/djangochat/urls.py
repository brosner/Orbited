import os
from django.conf.urls.defaults import *

djangochat_dir = os.path.dirname(os.path.abspath(__file__))

urlpatterns = patterns('',
    (r'^djangochat', 'djangochat.chat.views.chat'),
    (r'^join', 'djangochat.chat.views.join'),
    (r'^msg', 'djangochat.chat.views.msg'),
    ##Media
    (r'^files/(.*)$', 'django.views.static.serve',
     {'document_root': os.path.join(djangochat_dir, 'media'), 'show_indexes': True} ), 
    (r'^css/(.*)$', 'django.views.static.serve',
     {'document_root': os.path.join(djangochat_dir, 'media', 'css'), 'show_indexes': True}), 
    (r'^js/(.*)$', 'django.views.static.serve',
     {'document_root': os.path.join(djangochat_dir, 'media', 'js'), 'show_indexes': True}), 
    # Uncomment this for admin:
#     (r'^admin/', include('django.contrib.admin.urls')),
)
