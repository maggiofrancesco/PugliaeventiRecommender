from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect

from recommender_webapp.initializer import data_loader
from recommender_webapp.models import User


@csrf_protect
def index(request):
    context = {}
    # places_dict = data_loader.data_in_memory['places_dict']
    if request.user.is_authenticated:

        context = {
            'email': request.user.email,
            'email_splitted': request.user.email.split('@')[0]
        }

    return render(request, 'index.html', context)



