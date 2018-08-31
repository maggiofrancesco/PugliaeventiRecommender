from lightfm.cross_validation import random_train_test_split

from engine.data_fetcher import fetch_pugliaeventi
from lightfm.evaluation import auc_score, precision_at_k, recall_at_k
from lightfm import LightFM
import numpy as np
import os.path
import pickle


# Set the number of threads; you can increase this
# if you have more physical cores available.


NUM_THREADS = 2
NUM_COMPONENTS = 30
NUM_EPOCHS = 50
ITEM_ALPHA = 1e-6

MODEL_CHECKPOINT_PATH = "data/model_checkpoint.pickle"


def sample_recommendation(model, data, user_ids):

    # number of users and places in training data
    n_users, n_items = data['train'].shape

    # generate recommendations for each user we input
    for user_id in user_ids:

        # places they already rated
        known_positives = data['item_labels'][data['train'].tocsr()[user_id].indices]

        # movies our model predicts they will like

        scores = model.predict(user_id,
                               np.arange(n_items),
                               item_features=data['item_features'])

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
                          num_threads=NUM_THREADS).mean()
    test_auc = auc_score(model,
                         data['test'],
                         item_features=data['item_features'],
                         num_threads=NUM_THREADS).mean()

    print('\nHybrid training set AUC: %s' % train_auc)
    print('\nHybrid testing set AUC: %s' % test_auc)


if __name__ == "__main__":

    data = fetch_pugliaeventi(min_rating=0.0, indicator_features=False, tag_features=True)

    # (train, test) = random_train_test_split(data['train'], test_percentage=0.2)

    if os.path.isfile(MODEL_CHECKPOINT_PATH):
        with open(MODEL_CHECKPOINT_PATH, 'rb') as fle:
            model = pickle.load(fle)
    else:
        print("Train details\n: ")
        print(repr(data['train']))
        print("\nTest details\n: ")
        print(repr(data['test']))

        item_features = data['item_features']
        item_tag_labels = data['item_feature_labels']
        print('\nThere are %s distinct tags, with values like %s.\n'
              % (item_features.shape[1], item_tag_labels[-3:].tolist()))

        user_features = data['user_features']
        user_tag_labels = data['user_feature_labels']
        print('\nThere are %s distinct tags, with values like %s.\n'
              % (user_features.shape[1], user_tag_labels[-3:].tolist()))

        # create model Weighted Approximate-Rank Pairwise
        model = LightFM(loss='warp', item_alpha=ITEM_ALPHA, no_components=NUM_COMPONENTS)

        # train model
        model.fit(
            data['train'],
            item_features=item_features,
            epochs=NUM_EPOCHS,
            num_threads=NUM_THREADS)

        #with open(MODEL_CHECKPOINT_PATH, 'wb') as fle:
        #    pickle.dump(model, fle, protocol=pickle.HIGHEST_PROTOCOL)

        train_precision = precision_at_k(model, data['train'], k=10, item_features=item_features).mean()
        test_precision = precision_at_k(model, data['test'], k=10, train_interactions=data['train'],
                                        item_features=item_features).mean()

        train_recall = recall_at_k(model, data['train'], k=10, item_features=item_features).mean()
        test_recall = recall_at_k(model, data['test'], k=10, train_interactions=data['train'],
                                  item_features=item_features).mean()

        train_auc = auc_score(model, data['train'], item_features=item_features).mean()
        test_auc = auc_score(model, data['test'], train_interactions=data['train'], item_features=item_features).mean()

        print('Precision: train %.2f, test %.2f.' % (train_precision, test_precision))
        print('Recall: train %.2f, test %.2f.' % (train_recall, test_recall))
        print('AUC: train %.2f, test %.2f.' % (train_auc, test_auc))

    sample_recommendation(model, data, [110, 111, 120, 121, 130, 131, 1031, 2031, 3231])
