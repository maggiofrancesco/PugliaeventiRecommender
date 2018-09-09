import copy
from datetime import datetime

from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect

from recommender_webapp.common import lightfm_manager, constant
from recommender_webapp.forms import ProfileForm, UserRegisterForm, SearchNearPlacesForm, SearchPlacesDistanceRange, \
    AddRatingForm, FullProfileForm
from recommender_webapp.models import Comune, Distanza, Place, Mood, Companionship, Rating, User, Profile, Event


@csrf_protect
def user_login(request):
    """
    Login:
    La view permette l'autenticazione dell'utente. Successivamente all'autenticazione, viene verificato il numero di rating
    effettuati dall'utente. Se quest'ultimo risulta essere inferiore al numero di rating necessari per effettuare la
    configurazione del profilo, allora l'utente viene reindirizzato alla pagina della configurazione. In caso contrario,
    viene reindirizzato alla pagina principale.
    """

    if request.POST:
        email = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=email, password=password)
        if user is not None and user.is_active:
            print('User login: Email: ' + email + '     Password: ' + password)
            print(request.POST)
            login(request, user)

            # Check if the user has completed the profile configuration
            user_ratings = Rating.objects.filter(user=request.user.profile)
            if len(user_ratings) < (constant.RATINGS_PER_CONTEXT_CONF * constant.CONTEXTS):
                return redirect('/profile_configuration')
            else:
                return redirect('/')
        else:
            return render(request, 'index.html', {'message': 'Username or Password wrong!'})
    else:
        return render(request, '404.html')


def user_logout(request):
    """
    Logout:
    La view permette il logout dell'utente. Successivamente al logout si viene reindirizzati alla pagina principale.
    """

    logout(request)
    return redirect('/')


@csrf_protect
def user_signup(request):
    """
    Signup:
    La view permette la registrazione di un nuovo utente. All'utente standard di Django, vengono linkate ulteriori
    informazioni, racchiuse all'interno del model Profile, tra cui la città. In fase di signup è essenziale che l'utente
    fornisca la sua città (location). La location è importante per poter recuperare i posti nelle vicinanze in fase di
    configurazione del profilo utente e poter effettuare post-filtering sulle raccomandazioni fornite da LightFM. Al
    termine della procedura di signup, l'utente viene reindirizzato alla pagina principale.
    """

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


def profile_configuration(request):
    """
    Configurazione del profilo utente:
    La view, prima di procedere con la visualizzazione della pagina di configurazione del profilo utente, verifica il
    numero di rating effettuati dall'utente. Se quest'ultimo risulta essere inferiore  al numero di rating necessari per la
    configurazione del profilo utente, allora l'utente non ha ancora concluso la procedura di configurazione, per cui viene
    calcolata la percentuale di completamento della procedura. In caso contrario, la procedura è stata completata, quindi
    viene aggiornato il campo first_configuration presente nella tabella del profilo utente e si viene reindirizzati alla
    pagina principale.
    In questa prima versione del sistema, i contesti considerati sono 6, dati dalla combinazione delle variabili mood
    (angry, joyful, sad) e companionship (withFriends, alone). Per ciascun contesto, l'utente deve scegliere 3 luoghi,
    necessari per costruire il suo profilo utente e fornirgli raccomandazioni. Di volta in volta, l'utente ha la
    possibilità di scegliere tra quelli che sono i luoghi a lui più vicini (range di 10KM).
    IMPORTANTE: in questa prima versione del sistema, per ciascun contesto l'utente seleziona posti differenti, cioè un
    luogo non può essere selezionato in più contesti. Infatti, di volta in volta vengono restituiti i luoghi non ancora
    selezionati. Questa scelta è stata effettuata per meglio verificare i risultati restituiti da LightFM, dato che si
    tratta di un modello implicito (quindi non considera i rate forniti dall'utente, piuttosto sfrutta le features dei luoghi).
    Ciò non toglie che la procedura può essere impostata per consentire all'utente di scegliere il medesimo luogo in
    contesti differenti (ed è sensato, dato che una persona potrebbe preferire un luogo etichettato come MANGIARE e BERE,
    sia in un contesto JOYFUL-WITHFRIENDS, sia in un contesto ANGRY_WITHFRIENDS)
    """

    if request.user.is_authenticated:

        mood_configuration = {}
        companionship_configuration = {}
        rated_places = []
        user_contexts = []

        user_ratings = Rating.objects.filter(user=request.user.profile)
        user_contexts.append({'mood': Mood.joyful, 'companionship': Companionship.withFriends})
        user_contexts.append({'mood': Mood.joyful, 'companionship': Companionship.alone})
        user_contexts.append({'mood': Mood.angry, 'companionship': Companionship.withFriends})
        user_contexts.append({'mood': Mood.angry, 'companionship': Companionship.alone})
        user_contexts.append({'mood': Mood.sad, 'companionship': Companionship.withFriends})
        user_contexts.append({'mood': Mood.sad, 'companionship': Companionship.alone})

        if len(user_ratings) >= (constant.RATINGS_PER_CONTEXT_CONF * constant.CONTEXTS):
            # Profile configuration finished. We must add user data to LightFM dataset and recreate the model
            if not request.user.profile.first_configuration:
                lightfm_manager.add_user(request.user.id, request.user.profile.location, user_contexts, user_ratings)
                request.user.profile.first_configuration = True
                request.user.save()
            return redirect('/')

        else:
            percentage_completion = int(
                (len(user_ratings) * 100 / (constant.RATINGS_PER_CONTEXT_CONF * constant.CONTEXTS)))

            # We start asking preferences according to contexts (joyful, withfriends) and (joyful, alone)
            # I have to filter out places already selected in previous contexts
            # I put them at the end of the list; in this way the user could select different places in different contexts

            step = 1
            for user_context in user_contexts:
                contextual_ratings = user_ratings.filter(mood=user_context.get('mood').name, companionship=user_context.get('companionship').name)
                if len(contextual_ratings) < constant.RATINGS_PER_CONTEXT_CONF:
                    mood_configuration['index'] = user_context.get('mood').value
                    mood_configuration['name'] = user_context.get('mood').name
                    companionship_configuration['index'] = user_context.get('companionship').value
                    companionship_configuration['name'] = user_context.get('companionship').name
                    break
                else:
                    step += 1

            close_places = []
            user_location = request.user.profile.location
            locations_in_range = [distance[0] for distance in
                                  Distanza.objects.filter(
                                      cittaA=user_location,
                                      distanza__lte=constant.KM_RANGE_CONFIGURATION).order_by('distanza').values_list('cittaB')]
            locations_in_range = [user_location] + locations_in_range

            for location in locations_in_range:
                places = Place.objects.filter(location=location)
                for place in places:
                    place_dict = vars(place)
                    place_dict['labels'] = place.labels()
                    if Rating.objects.filter(place=place, user=request.user.profile).exists():
                        place_dict['rated'] = True
                        rated_places.append(place_dict)
                    else:
                        close_places.append(place_dict)

        # Excluded places already selected
        # close_places.extend(rated_places)

    else:
        return redirect('/')

    context = {
        'step': step,
        'percentage': percentage_completion,
        'mood': mood_configuration,
        'companionship': companionship_configuration,
        'places': close_places,
        'ratings_per_context': constant.RATINGS_PER_CONTEXT_CONF
    }

    return render(request, "profile_configuration.html", context)


def add_rating_config(request, place_id, mood, companionship):
    """
    Selezione di un luogo durante la procedura di configurazione del profilo utente:
    La view consente l'aggiunta di un luogo al proprio profilo utente, considerando il mood e la companionship.
    In questa prima versione del sistema l'utente non fornisce un rate numerico al luogo in quanto LightFM implementa un
    modello implicito, per cui non si basa sui punteggi forniti dall'utente. Ciò non toglie che il campo rating contenente
    il punteggio potrebbe essere utile in futuro. In questo caso, viene assegnato un rating di default. In seguito l'utente
    viene reindirizzato alla pagina della configurazione del profilo.
    """

    if request.user.is_authenticated:

        place = Place.objects.get(placeId=place_id)
        rating = Rating(user=request.user.profile,
                        mood=Mood(mood).name,
                        companionship=Companionship(companionship).name,
                        place=place,
                        rating=constant.DEFAULT_RATING)
        rating.save()
        return redirect('profile_configuration')
    else:
        return redirect('/')


def close_places(request):
    """
    Visualizzazione dei luoghi vicini all'utente:
    La view consente la visualizzazione dei luoghi vicini all'utente in un range di km che può essere di 5 oppure 10 KM.
    """

    context = {}
    close_places = []

    if request.user.is_authenticated:

        search_near_places_form = SearchNearPlacesForm(request.POST or None)
        initial_km_range = (SearchPlacesDistanceRange.km5.name, SearchPlacesDistanceRange.km5.value)
        search_near_places_form.fields['km_range'].initial = initial_km_range

        if search_near_places_form.is_valid():
            km_range = search_near_places_form.cleaned_data.get('km_range')
            user_location = request.user.profile.location
            locations_in_range = [distance[0] for distance in
                                  Distanza.objects.filter(
                                      cittaA=user_location,
                                      distanza__lte=km_range).order_by('distanza').values_list('cittaB')]
            locations_in_range = [user_location] + locations_in_range

            for distance in locations_in_range:
                places = Place.objects.filter(location=distance)
                for place in places:
                    place_dict = vars(place)
                    place_dict['labels'] = place.labels()
                    if Rating.objects.filter(place=place).exists():
                        place_dict['rated'] = True
                    close_places.append(place_dict)

        context = {
            'search_form': search_near_places_form,
            'email': request.user.email,
            'email_splitted': request.user.email.split('@')[0],
            'close_places': close_places
        }

    return render(request, 'places.html', context)


def my_places(request):
    """
    Visualizzazione dei luoghi del profilo utente, per ciacun contesto:
    La view consente la visualizzazione dei luoghi appartenenti al proprio profilo utente, cioè i luoghi selezionati per
    ciascun contesto (in questo caso i 6 contesti generati dalle combinazioni di Mood e Companionship).
    """

    context = {}
    my_places = []

    if request.user.is_authenticated:

        for mood in Mood.choices():
            context_places = {'mood': mood[0]}
            for companionship in Companionship.choices():
                context_places['companionship'] = companionship[0]
                context_ratings = Rating.objects.filter(user=request.user.profile, mood=mood[0], companionship=companionship[0])
                places = []
                for rating in context_ratings:
                    place = Place.objects.get(placeId=rating.place.placeId)
                    places.append(place)
                context_places['places'] = places
                my_places.append(copy.deepcopy(context_places))

        context = {
            'user_places_per_context': my_places,
            'email': request.user.email,
            'email_splitted': request.user.email.split('@')[0],
        }

    return render(request, 'my_places.html', context)


def place_details(request, place_id):
    """
    Visualizzazione dei dettagli di un luogo:
    La view consente di visualizzare i dettagli di un luogo ed eventualmente aggiungerlo al proprio profilo utente. In
    questa prima versione del sistema l'aggiunta del luogo al proprio profilo utente, specificando Mood e Companionship, è
    possibile solo se non è stato aggiunto in precedenza con qualche altro contesto. Tuttavia, questo non vieta che la
    procedura descritta nel seguente metodo possa essere impostata per aggiungere il luogo ad un contesto nonostante sia
    stato già aggiunto in altri contesti (ad esempio, un utente che preferisce un luogo sia nel contesto Joyful e
    WithFriends, sia nel contesto Angry e WithFriends).
    Quando un utente decide di aggiungere un luogo al proprio profilo sotto un contesto specifico, è necessario fornire tale
    informazione anche al modello di LightFM. In tal caso non è necessario ricalcolare il modello, ma è sufficiente
    fornire la relazione aggiuntiva (ID UTENTE - ID LUOGO). Il metodo responsabile di questa operazione è add_rating del
    modulo lightfm_manager.
    L'ID utente utilizzato da LightFM, e quindi passato al metodo add_rating, è una stringa che si costituisce
    delle seguenti componenti: (ID utente in Django incrementato di 100) + ID mood + ID companionship. Ad esempio, se l'id
    utente in django è 4, l'ID mood è 2 e l'ID companionship è 1 allora la stringa rappresentante l'utente è: 10421. L'id
    utente di django viene sommato a 100 in quanto gli utenti da 1 a 100 sono già presenti nel dataset di LightFM (vedi
    data/users.csv e ratings_train.csv).
    Inoltre, la seguente view fornisce anche informazioni su eventuali eventi che si svolgeranno nel luogo in questione.
    """

    context = {}
    if request.user.is_authenticated:

        search_rec_form = AddRatingForm(request.POST or None)
        initial_mood = (Mood.joyful.name, Mood.joyful.value)
        search_rec_form.fields['mood'].initial = initial_mood

        place = Place.objects.get(placeId=place_id)
        labels = place.labels().split(',')
        if not labels[-1].strip():
            labels.pop()
        place_ratings = []  # A place could be rated in several contexts (PROBABLY IN A FUTURE DEVELOPMENT)
        ratings = Rating.objects.filter(user=request.user.profile, place=place)

        # In this release a place can be rated only in one context. So, if the place is already rated, form is not given
        if ratings:
            for rate in ratings:
                place_rate = {'mood': rate.mood, 'companionship': rate.companionship}
                place_ratings.append(place_rate)
        else:
            context['form'] = search_rec_form

        events = Event.objects.filter(place=place, date_from__gte=datetime.today().date())

        if search_rec_form.is_valid():
            mood = int(search_rec_form.cleaned_data.get('mood'))
            companionship = int(search_rec_form.cleaned_data.get('companionship'))
            lightfm_user_id = constant.DJANGO_USER_ID_BASE_START_LIGHTFM + request.user.id
            contextual_lightfm_user_id = str(lightfm_user_id) + str(mood) + str(companionship)
            rating = Rating(user=request.user.profile,
                            mood=Mood(mood).name,
                            companionship=Companionship(companionship).name,
                            place=place,
                            rating=constant.DEFAULT_RATING)
            rating.save()
            place_ratings.append(rating)
            lightfm_manager.add_rating(int(contextual_lightfm_user_id), place_id, rating.rating)

        context = {
            'place': place,
            'labels': labels,
            'events': events,
            'form': search_rec_form,
            'ratings': place_ratings,
            'email': request.user.email,
            'email_splitted': request.user.email.split('@')[0],
        }

    return render(request, 'place.html', context)


def event_details(request, event_id):
    """
    Visualizzazione dei dettagli su un evento:
    La view consente di visualizzare i dettagli di un evento, come il nome, la location, le etichette ed informazioni varie.
    """

    context = {}
    if request.user.is_authenticated:

        event = Event.objects.get(eventId=event_id)

        context = {
            'event': event,
            'email': request.user.email,
            'email_splitted': request.user.email.split('@')[0],
        }

    return render(request, 'event.html', context)


def user_profile(request):
    """
    Visualizzazione del profilo utente:
    La view consente di visualizzare il proprio profilo utente ed eventualmente effettuare modifiche. All'interno del
    relativo template è stato inserito il button "Link to Myrror", che potrebbe essere utile in futuro per prelevare le
    informazioni sul profilo utente utilizzando le api di Myrror.
    """

    context = {
        'email': request.user.email,
        'email_splitted': request.user.email.split('@')[0],
    }

    if request.user.is_authenticated:

        instance = Profile.objects.get(user=request.user)
        full_profile_form = FullProfileForm(request.POST or None, instance=instance)
        context['form'] = full_profile_form

        if full_profile_form.is_valid():
            location = full_profile_form.cleaned_data.get('location')
            location_found = Comune.objects.filter(nome__iexact=location)

            profession = full_profile_form.cleaned_data.get('profession')
            birth_date = full_profile_form.cleaned_data.get('birth_date')
            bio = full_profile_form.cleaned_data.get('bio')

            profile = Profile.objects.get(user=request.user)
            profile.location = location_found.first().nome
            profile.profession = profession
            profile.birth_date = birth_date
            profile.bio = bio
            profile.save()
            context['data_updated'] = True
        else:
            context['data_updated'] = False

    return render(request, 'profile.html', context)
