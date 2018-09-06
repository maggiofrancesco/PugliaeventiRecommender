import copy

from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect

# Create your views here.
from django.views.decorators.csrf import csrf_protect

from recommender_webapp.common import lightfm_manager, constant
from recommender_webapp.forms import ProfileForm, UserRegisterForm, SearchNearPlacesForm, DistanceRange, \
    SearchRecommendationForm, FullProfileForm
from recommender_webapp.models import Comune, Distanza, Place, Mood, Companionship, Rating, User, Profile


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
    logout(request)
    return redirect('/')


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


def profile_configuration(request):
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

        if len(user_ratings) == (constant.RATINGS_PER_CONTEXT_CONF * constant.CONTEXTS):
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
            distances_in_range = Distanza.objects.filter(cittaA=user_location, distanza__lte=constant.KM_RANGE_CONFIGURATION).order_by('distanza')

            user_location_places = Place.objects.filter(location=user_location)
            for place in user_location_places:
                place_dict = vars(place)
                place_dict['labels'] = place.labels()
                rated_place = Rating.objects.filter(place=place, user=request.user.profile)
                if rated_place:
                    place_dict['rated'] = True
                    rated_places.append(place_dict)
                else:
                    close_places.append(place_dict)

            for distance in distances_in_range:
                places = Place.objects.filter(location=distance.cittaB)
                for place in places:
                    place_dict = vars(place)
                    place_dict['labels'] = place.labels()
                    rated_place = Rating.objects.filter(place=place)
                    if rated_place:
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
    context = {}
    rated_places = []
    close_places = []

    if request.user.is_authenticated:

        search_near_places_form = SearchNearPlacesForm(request.POST or None)
        initial_km_range = (DistanceRange.km5.name, DistanceRange.km5.value)
        search_near_places_form.fields['km_range'].initial = initial_km_range

        if search_near_places_form.is_valid():
            km_range = search_near_places_form.cleaned_data.get('km_range')
            user_location = request.user.profile.location
            distances_in_range = Distanza.objects.filter(cittaA=user_location, distanza__lte=km_range).order_by('distanza')

            user_location_places = Place.objects.filter(location=user_location)
            for place in user_location_places:
                place_dict = vars(place)
                place_dict['labels'] = place.labels()
                rated_place = Rating.objects.filter(place=place, user=request.user.profile)
                if rated_place:
                    place_dict['rated'] = True
                    rated_places.append(place_dict)
                else:
                    close_places.append(place_dict)

            for distance in distances_in_range:
                places = Place.objects.filter(location=distance.cittaB)
                for place in places:
                    place_dict = vars(place)
                    place_dict['labels'] = place.labels()
                    rated_place = Rating.objects.filter(place=place)
                    if rated_place:
                        place_dict['rated'] = True
                        rated_places.append(place_dict)
                    else:
                        close_places.append(place_dict)

        context = {
            'search_form': search_near_places_form,
            'email': request.user.email,
            'email_splitted': request.user.email.split('@')[0],
            'close_places': close_places
        }

    return render(request, 'places.html', context)


def my_places(request):
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
    context = {}
    if request.user.is_authenticated:

        search_rec_form = SearchRecommendationForm(request.POST or None)
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
            'form': search_rec_form,
            'ratings': place_ratings,
            'email': request.user.email,
            'email_splitted': request.user.email.split('@')[0],
        }

    return render(request, 'place.html', context)


def user_profile(request):

    context = {
        'email': request.user.email,
        'email_splitted': request.user.email.split('@')[0],
    }

    if request.user.is_authenticated:

        instance = Profile.objects.get(user=request.user)
        full_profile_form = FullProfileForm(request.POST or None, instance=instance)
        context['form'] = full_profile_form
        # initial_mood = (Mood.joyful.name, Mood.joyful.value)
        # search_rec_form.fields['mood'].initial = initial_mood

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
