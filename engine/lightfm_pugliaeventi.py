from engine.data_fetcher import fetch_pugliaeventi
from lightfm.evaluation import auc_score
from lightfm import LightFM
import numpy as np
import os.path
import pickle


# Set the number of threads; you can increase this
# if you have more physical cores available.


NUM_THREADS = 2
NUM_COMPONENTS = 30
NUM_EPOCHS = 3
ITEM_ALPHA = 1e-6

MODEL_CHECKPOINT_PATH = "data/model_checkpoint.pickle"


def sample_reccomendation(model, data, user_ids):

    # number of users and places in training data
    n_users, n_items = data['train'].shape

    # generate reccomendations for each user we input
    for user_id in user_ids:

        # places they already rated
        known_positives = data['item_labels'][data['train'].tocsr()[user_id].indices]

        # movies our model predicts they will like

        scores = model.predict(user_id,
                               np.arange(n_items),
                               item_features=data['item_features'],
                               user_features=data['user_features'])
        # rank them in order of most liked to least
        top_items = data['item_labels'][np.argsort(-scores)]

        print("User %s" % user_id)
        print("     Known positives:")

        for x in known_positives[:10]:
            print("         %s" % x)

        print("     Recommended:")

        for x in top_items[:10]:
            print("         %s" % x)

    # Don't forget the pass in the item features again!
    train_auc = auc_score(model,
                          data['train'],
                          item_features=data['item_features'],
                          user_features=data['user_features'],
                          num_threads=NUM_THREADS).mean()
    print('\nHybrid training set AUC: %s' % train_auc)


if __name__ == "__main__":

    data = fetch_pugliaeventi(min_rating=0.0, indicator_features=True, tag_features=True)

    if os.path.isfile(MODEL_CHECKPOINT_PATH):
        with open(MODEL_CHECKPOINT_PATH, 'rb') as fle:
            model = pickle.load(fle)
    else:
        print(repr(data['train']))
        item_features = data['item_features']
        item_tag_labels = data['item_feature_labels']
        print('\nThere are %s distinct tags, with values like %s.\n'
              % (item_features.shape[1], item_tag_labels[-3:].tolist()))

        user_features = data['user_features']
        user_tag_labels = data['user_feature_labels']
        print('\nThere are %s distinct tags, with values like %s.\n'
              % (user_features.shape[1], user_tag_labels[-3:].tolist()))

        # create model
        model = LightFM(loss='warp')
        # item_alpha=ITEM_ALPHA,
        # no_components=NUM_COMPONENTS)    # Weighted Approximate-Rank Pairwise

        # train model
        model.fit(
            data['train'],
            item_features=item_features,
            user_features=user_features,
            epochs=NUM_EPOCHS,
            num_threads=NUM_THREADS)

        with open(MODEL_CHECKPOINT_PATH, 'wb') as fle:
            pickle.dump(model, fle, protocol=pickle.HIGHEST_PROTOCOL)

    sample_reccomendation(model, data, [110, 111, 120, 121, 130, 131])
