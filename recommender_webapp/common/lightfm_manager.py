import csv

from recommender_webapp.common import constant
from engine import lightfm_pugliaeventi
from recommender_webapp.models import Place


def add_user(user_id, user_location,  user_contexts, data):
    lightfm_user_id = constant.DJANGO_USER_ID_BASE_START_LIGHTFM + user_id
    for user_context in user_contexts:
        contextual_lightfm_user_id = str(lightfm_user_id) + str(user_context.get('mood').value) + str(user_context.get('companionship').value)

        # Add user (SPLIT) to users.csv
        with open(r'engine/data/users.csv', 'a') as f:
            writer = csv.writer(f)
            writer.writerow([contextual_lightfm_user_id, user_location, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

        contextual_ratings = data.filter(mood=user_context.get('mood').name, companionship=user_context.get('companionship').name)

        # Add ratings to ratings.csv
        with open(r'engine/data/ratings_train.csv', 'a') as f:
            writer = csv.writer(f)
            for rating in contextual_ratings:
                writer.writerow([contextual_lightfm_user_id, rating.place.placeId, rating.rating])

    # LightFM model recreation - NEW USER SIGN UP-> NEW MODEL
    lightfm_pugliaeventi.learn_model(force_model_creation=True)


def add_rating(contextual_lightfm_user_id, place_id, rating):
    # Add rating to ratings.csv
    with open(r'engine/data/ratings_train.csv', 'a') as f:
        writer = csv.writer(f)
        writer.writerow([contextual_lightfm_user_id, place_id, rating])

    max_user_id = 0
    max_item_id = 0
    # I need the max user ID and the max item ID
    with open(r'engine/data/users.csv') as csvfile:
        for row in reversed(list(csv.reader(csvfile, delimiter=','))):
            max_user_id = int(row[0])
            break
    with open(r'engine/data/items.csv') as csvfile:
        for row in reversed(list(csv.reader(csvfile, delimiter=','))):
            max_item_id = int(row[0])
            break

    # Add new rating to LightFM model
    lightfm_pugliaeventi.add_rating_to_model(max_user_id, max_item_id, contextual_lightfm_user_id, place_id, rating)


def find_recommendations(user):
    recommended_places = []
    user = int(user) - 1   # LightFM uses a zero-based indexing
    model, data = lightfm_pugliaeventi.learn_model()
    recommendations = lightfm_pugliaeventi.find_recommendations(user, model, data)
    places_to_show = recommendations[:constant.NUM_RECOMMENDATIONS]
    for place in places_to_show:
        place_id = place + 1  # Because the LightFM zero-based indexing
        place = Place.objects.get(placeId=place_id)
        recommended_places.append(place)

    return recommended_places
