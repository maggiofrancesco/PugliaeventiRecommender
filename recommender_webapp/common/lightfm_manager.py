import csv

from pugliaeventi import constant


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


def find_recommendations(user, mood, companionship):
    pass
