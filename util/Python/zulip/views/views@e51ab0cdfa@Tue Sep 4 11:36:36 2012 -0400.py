from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.shortcuts import render
from django.utils.timezone import utc

from django.contrib.auth.models import User
from zephyr.models import Zephyr, UserProfile, ZephyrClass, Subscription, \
    Recipient, filter_by_subscriptions, get_display_recipient
from zephyr.forms import RegistrationForm

import tornado.web
from zephyr.decorator import asynchronous

import datetime
import simplejson

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']
            u = User.objects.create_user(username=username, password=password)
            u.save()
            user = authenticate(username=username, password=password)
            login(request, user)
            return HttpResponseRedirect(reverse('zephyr.views.home'))
    else:
        form = RegistrationForm()

    return render(request, 'zephyr/register.html', {
        'form': form,
    })

def accounts_home(request):
    return render_to_response('zephyr/accounts_home.html',
                              context_instance=RequestContext(request))    
    
def home(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('accounts/home/')

    zephyrs = filter_by_subscriptions(Zephyr.objects.all(), request.user)

    user = request.user
    user_profile = UserProfile.objects.get(user=user)
    if user_profile.pointer == -1 and zephyrs:
        user_profile.pointer = min([zephyr.id for zephyr in zephyrs])
        user_profile.save()
    zephyr_json = simplejson.dumps([zephyr.to_dict() for zephyr in zephyrs])
    return render_to_response('zephyr/index.html',
                              {'zephyr_json' : zephyr_json,
                               'user_profile': user_profile },
                              context_instance=RequestContext(request))

def update(request):
    if not request.POST:
        # Do something
        pass
    user = request.user
    user_profile = UserProfile.objects.get(user=user)
    if request.POST.get('pointer'):
        user_profile.pointer = request.POST.get("pointer")
        user_profile.save()
    return HttpResponse(simplejson.dumps({}), mimetype='application/json')

@login_required
def get_state(request):
    if not request.GET:
        # Do something
        pass

    user_profile = UserProfile.objects.get(user=request.user)
    return HttpResponse(simplejson.dumps({"pointer": user_profile.pointer}),
                        mimetype='application/json')

@asynchronous
def get_updates_longpoll(request, handler):
    if not request.POST:
        # TODO: Do something
        pass
   
    last_received = request.POST.get('last_received')
    if not last_received:
        # TODO: return error?
        pass

    user = request.user
    user_profile = UserProfile.objects.get(user=user)

    def on_receive(zephyrs):
        if handler.request.connection.stream.closed():
            return
        try:
            handler.finish({'zephyrs': [zephyr.to_dict() for zephyr in zephyrs]})
        except socket.error as e:
            pass

    # We need to replace this abstraction with the message list
    user_profile.add_callback(handler.async_callback(on_receive), last_received)

@login_required
def personal_zephyr(request):
    recipient_username = request.POST['recipient']
    if User.objects.filter(username=recipient_username):
        recipient_user = User.objects.get(username=recipient_username)
    else:
        # Do something reasonable.
        return HttpResponse('')

    # Right now, you can't make recipients on the fly by sending zephyrs to new
    # classes or people.
    recipient_user_profile = UserProfile.objects.get(user=recipient_user)
    recipient = Recipient.objects.get(user_or_class=recipient_user_profile.id, type="personal")
    sender = UserProfile.objects.get(user=request.user)
    content = request.POST['new_personal_zephyr']
    pub_date = datetime.datetime.utcnow().replace(tzinfo=utc)

    new_zephyr = Zephyr(sender=sender, recipient=recipient, content=content,
                        instance='', pub_date=pub_date)
    new_zephyr.save()

    return HttpResponse('')

@login_required
def zephyr(request):
    class_name = request.POST['class']
    if ZephyrClass.objects.filter(name=class_name):
        my_class = ZephyrClass.objects.get(name=class_name)
    else:
        my_class = ZephyrClass()
        my_class.name = class_name
        my_class.save()

    # Right now, you can't make recipients on the fly by sending zephyrs to new
    # classes or people.
    recipient = Recipient.objects.get(user_or_class=my_class.id, type="class")

    new_zephyr = Zephyr()
    new_zephyr.sender = UserProfile.objects.get(user=request.user)
    new_zephyr.content = request.POST['new_zephyr']
    new_zephyr.recipient = recipient
    new_zephyr.instance = request.POST['instance']
    new_zephyr.pub_date = datetime.datetime.utcnow().replace(tzinfo=utc)
    new_zephyr.save()

    return HttpResponse('')

@login_required
def subscriptions(request):
    userprofile = UserProfile.objects.get(user=request.user)
    subscriptions = Subscription.objects.filter(userprofile_id=userprofile, active=True)
    # For now, don't display the subscription for your ability to receive personals.
    sub_names = [get_display_recipient(sub.recipient_id) for sub in subscriptions if sub.recipient_id.type != "personal"]

    return render_to_response('zephyr/subscriptions.html',
                              {'subscriptions': sub_names, 'user_profile': userprofile},
                              context_instance=RequestContext(request))

@login_required
def manage_subscriptions(request):
    if not request.POST:
        # Do something reasonable.
        return
    user_profile = UserProfile.objects.get(user=request.user)

    unsubs = request.POST.getlist('subscription')
    for sub_name in unsubs:
        zephyr_class = ZephyrClass.objects.get(name=sub_name)
        recipient = Recipient.objects.get(user_or_class=zephyr_class.id, type="class")
        subscription = Subscription.objects.get(
            userprofile_id=user_profile.id, recipient_id=recipient)
        subscription.active = False
        subscription.save()

    return HttpResponseRedirect(reverse('zephyr.views.subscriptions'))

@login_required
def add_subscriptions(request):
    if not request.POST:
        # Do something reasonable.
        return
    user_profile = UserProfile.objects.get(user=request.user)

    new_subs = request.POST.get('new_subscriptions')
    if not new_subs:
        return HttpResponseRedirect(reverse('zephyr.views.subscriptions'))

    for sub_name in new_subs.split(","):
        zephyr_class = ZephyrClass.objects.filter(name=sub_name)
        if zephyr_class:
            zephyr_class = zephyr_class[0]
        else:
            zephyr_class = ZephyrClass(name=sub_name)
            zephyr_class.save()

        recipient = Recipient.objects.filter(user_or_class=zephyr_class.pk, type="class")
        if recipient:
            recipient = recipient[0]
        else:
            recipient = Recipient(user_or_class=zephyr_class.pk, type="class")
        recipient.save()

        subscription = Subscription.objects.filter(userprofile_id=user_profile,
                                                   recipient_id=recipient)
        if subscription:
            subscription = subscription[0]
            subscription.active = True
            subscription.save()
        else:
            new_subscription = Subscription(userprofile_id=user_profile,
                                            recipient_id=recipient)
            new_subscription.save()

    return HttpResponseRedirect(reverse('zephyr.views.subscriptions'))