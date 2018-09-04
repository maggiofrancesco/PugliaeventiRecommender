from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect

from recommender_webapp.common import lightfm_manager, constant
from recommender_webapp.forms import SearchRecommendationForm
from recommender_webapp.models import Mood, Place


@csrf_protect
def index(request):
    context = {}
    recommended_places = []
    # places_dict = data_loader.data_in_memory['places_dict']

    if request.user.is_authenticated:

        search_rec_form = SearchRecommendationForm(request.POST or None)
        # search_rec_form.fields['mood'].disabled = True
        initial_mood = (Mood.joyful.name, Mood.joyful.value)
        search_rec_form.fields['mood'].initial = initial_mood

        if search_rec_form.is_valid():
            mood = search_rec_form.cleaned_data.get('mood')
            companionship = search_rec_form.cleaned_data.get('companionship')
            lightfm_user_id = constant.DJANGO_USER_ID_BASE_START_LIGHTFM + request.user.id
            contextual_lightfm_user_id = str(lightfm_user_id) + str(mood) + str(companionship)
            recommended_places = lightfm_manager.find_recommendations(contextual_lightfm_user_id)

        context = {
            'search_form': search_rec_form,
            'email': request.user.email,
            'email_splitted': request.user.email.split('@')[0],
            'recommended_places': recommended_places
        }

    return render(request, 'index.html', context)



