from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from django.shortcuts import render, redirect

# Create your views here.
from django.views.decorators.csrf import csrf_protect

from recommender_webapp.forms import ProfileForm, UserRegisterForm
from recommender_webapp.models import Comune


@csrf_protect
def user_login(request):
    if request.POST:
        email = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=email, password=password)
        if user is not None and user.is_active:
            print('User login: Email: ' + email + '     Password: ' + password)
            print(request.POST)
            login(request, user)
            return render(request, 'base.html', {'email_splitted': user.email.split('@')[0]})
        else:
            return render(request, 'base.html', {'message': 'Username or Password wrong!'})
    else:
        return render(request, '404.html')


def user_logout(request):
    logout(request)
    return HttpResponse()


@csrf_protect
def user_signup(request):
    user_form = UserRegisterForm(request.POST or None)
    profile_form = ProfileForm(request.POST or None)

    if user_form.is_valid() and profile_form.is_valid():
        user = user_form.save(commit=False)
        password = user_form.cleaned_data.get('password')
        location = profile_form.cleaned_data.get('location')
        user.set_password(password)
        user.save()

        location_found = Comune.objects.filter(nome__iexact=location)
        user.profile.location = location_found.first().nome
        user.save()

        new_user = authenticate(username=user.email, password=password)
        login(request, new_user)
        return redirect('/')

    context = {
        'user_form': user_form,
        'profile_form': profile_form
    }

    return render(request, "signup.html", context)
