import django
from django.shortcuts import render_to_response
from django.http import HttpResponse

from pyorbited.simple import Client
orbit = Client()
django.chatusers = []

def chat(request):
    return render_to_response("chat/chat.html")

def user_keys():
    return ['%s, %s, /djangochat' % (u, s) for (u, s) in django.chatusers]

def join(request):
    id = request.GET.get("id", None)
    user = request.GET.get("user")
    session = request.GET.get("session", "0")
    if (user, session) not in django.chatusers:
        django.chatusers.append((user, session))
        orbit.event(user_keys(), '<b>%s joined</b>' % user)
    return HttpResponse('')
    
def msg(request):
    id = request.GET.get("id", None)
    user = request.GET.get("user")
    msg = request.GET.get("msg")
    session = request.GET.get("session", "0")
    orbit.event(user_keys(), '<b>%s</b> %s' % (user, msg))
    return HttpResponse('')
