from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect

from recommender_webapp.common import lightfm_manager, constant
from recommender_webapp.forms import SearchRecommendationForm
from recommender_webapp.models import Mood, Rating


@csrf_protect
def index(request):
    """
    Pagina principale:
    La view, prima di procedere con la visualizzazione della pagina principale, verifica il numero di rating effettuati
    dall'utente. In questa prima versione, il rating consiste nell'aggiunta di un luogo al proprio profilo, senza un rate
    numerico. Dato che LightFM implementa un modello implicito, non è necessario un rate numerico. Se il numero di rating
    è inferiore al numero di rating necessari per la configurazione del profilo, significa che l'utente non ha ancora
    concluso la procedura di configurazione. In tal caso, l'utente viene reindirizzato alla pagina della configurazione
    del profilo. In caso contrario, si procede con la visualizzazione della pagina principale.
    La pagina principale consente di visualizzare i posti raccomandati in base al mood (angry, joyful, sad), alla
    companionship (withFriends oppure alone), alla distanza in KM e alla presenza di eventi. Questi sono i filtri presenti
    nel form. Per ricevere le raccomandazioni viene utilizzato il metodo find_recommendations del modulo lightfm_manager.
    L'ID utente utilizzato da LightFM, e quindi passato al metodo find_recommendations, è una stringa che si costituisce
    delle seguenti componenti: (ID utente in Django incrementato di 100) + ID mood + ID companionship. Ad esempio, se l'id
    utente in django è 4, l'ID mood è 2 e l'ID companionship è 1 allora la stringa rappresentante l'utente è: 10421. L'id
    utente di django viene sommato a 100 in quanto gli utenti da 1 a 100 sono già presenti nel dataset di LightFM (vedi
    data/users.csv e ratings_train.csv)
    """

    context = {}
    recommended_places = []
    # places_dict = data_loader.data_in_memory['places_dict']

    if request.user.is_authenticated:

        # Check if the user has completed the profile configuration
        user_ratings = Rating.objects.filter(user=request.user.profile)
        if len(user_ratings) < (constant.RATINGS_PER_CONTEXT_CONF * constant.CONTEXTS):
            return redirect('/profile_configuration')
        else:
            search_rec_form = SearchRecommendationForm(request.POST or None)
            # search_rec_form.fields['mood'].disabled = True
            initial_mood = (Mood.joyful.name, Mood.joyful.value)
            search_rec_form.fields['mood'].initial = initial_mood

            if search_rec_form.is_valid():
                mood = search_rec_form.cleaned_data.get('mood')
                companionship = search_rec_form.cleaned_data.get('companionship')
                distance = search_rec_form.cleaned_data.get('km_range')
                any_events = search_rec_form.cleaned_data.get('any_events')
                lightfm_user_id = constant.DJANGO_USER_ID_BASE_START_LIGHTFM + request.user.id
                contextual_lightfm_user_id = str(lightfm_user_id) + str(mood) + str(companionship)

                recommended_places = lightfm_manager.find_recommendations(
                    contextual_lightfm_user_id,
                    request.user.profile.location,
                    int(distance),
                    any_events)

            context = {
                'search_form': search_rec_form,
                'email': request.user.email,
                'email_splitted': request.user.email.split('@')[0],
                'recommended_places': recommended_places
            }

    return render(request, 'index.html', context)



