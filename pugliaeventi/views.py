from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect

from recommender_webapp.initializer import data_loader
from recommender_webapp.models import User


@csrf_protect
def index(request):
    user_data = {}
    places_dict = data_loader.data_in_memory['places_dict']
    if request.user.is_authenticated:
        user_data = {'email': request.user.email, 'email_splitted': request.user.email.split('@')[0]}
        user = User.objects.get(email=user_data['email'])
        user_data['city'] = user.profile.location
        user_data['profession'] = user.profile.profession
        user_data['birth_date'] = user.profile.birth_date
        user_data['bio'] = user.profile.bio
        user_data['empathy'] = user.profile.empathy

    return render(request, 'base.html', user_data)



