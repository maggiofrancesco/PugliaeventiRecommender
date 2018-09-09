from engine.lightfm_data_fetcher import fetch_pugliaeventi
from engine.lightfm_data_fetcher import _build_interaction_matrix, _read_item_data, _parse_item_metadata
from lightfm.evaluation import auc_score, precision_at_k, recall_at_k
from lightfm import LightFM
import numpy as np
import os.path
import pickle


NUM_THREADS = 2
NUM_COMPONENTS = 30
NUM_EPOCHS = 50
ITEM_ALPHA = 1e-6

MODEL_CHECKPOINT_PATH = "data/model_checkpoint.pickle"
script_dir = os.path.dirname(__file__)


def find_recommendations(user, model, data):
    """
    Ricerca di raccomandazioni utili per un utente specifico:
    Il seguente metodo consente di ricercare raccomandazioni per un utente specifico. Il metodo predict del modello di
    LightFM restituisce la lista degli ID dei luoghi, che successivamente viene ordinata in maniera decrescente (dal
    luogo maggiormente raccomandato a quello meno raccomandato)
    """

    # number of users and places in training data
    n_users, n_items = data['train'].shape

    # places the user already rated
    # known_positives = data['item_labels'][data['train'].tocsr()[user].indices]

    scores = model.predict(user,
                           np.arange(n_items),
                           item_features=data['item_features'])

    items_ordered = np.argsort(-scores)

    """
    # rank them in order of most liked to least
    top_items = data['item_labels'][items_ordered]

    print("User %s" % user)
    print("     Known positives:")

    for x in known_positives[:10]:
        print("         %s" % x)

    print("     Recommended:")

    for x in top_items[:10]:
        print("         %s" % x)
    """

    return items_ordered


def add_rating_to_model(max_user_id, max_item_id, user_id, item_id, rating):
    """
    Aggiunta di un nuovo rating al modello:
    Il seguente metodo consente di aggiungere un nuovo rating al modello. In tal caso, considerato che l'utente esiste
    già, non è necessario apprendere nuovamente il modello. Infatti, è sufficiente utilizzare il metodo fit_partial del
    modello di LightFM per poter aggiungere il rating ad un utente esistente.
    Il modello viene caricato in memoria utilizzando il checkpoint salvato in formato .pickle. Successivamente, viene
    costruita una matrice delle interazioni il cui shape è pari a max_user_id x max_item_id e contiene la nuova
    interazione che si vuole aggiungere al modello. Il metodo fit_partial viene chiamato passando la matrice delle
    interazioni creata, le features degli item, il numero di epochs da applicare per l'apprendimento e il numero di
    threads da impiegare.
    """

    if os.path.isfile(os.path.join(script_dir, MODEL_CHECKPOINT_PATH)):
        with open(os.path.join(script_dir, MODEL_CHECKPOINT_PATH), 'rb') as fle:
            model = pickle.load(fle)

        interactions = _build_interaction_matrix(max_user_id, max_item_id, [(user_id - 1, item_id - 1, rating)], 0)
        items, labels_item = _read_item_data()
        (iid_features, iid_feature_labels, item_features, item_tag_feature_labels
         ) = _parse_item_metadata(max_item_id, items, labels_item)

        model.fit_partial(
            interactions,
            item_features=item_features,
            epochs=NUM_EPOCHS,
            num_threads=NUM_THREADS)

        with open(os.path.join(script_dir, MODEL_CHECKPOINT_PATH), 'wb') as fle:
            pickle.dump(model, fle, protocol=pickle.HIGHEST_PROTOCOL)


def learn_model(force_model_creation=False):
    """
    Apprendimento del modello LightFM:
    Il seguente metodo consente di caricare (se presente in formato .pickle) oppure apprendere il modello LightFM.
    L'apprendimento del modello avviene con il metodo fit del modello di LightFM, passandogli il dataset contenente le
    interazioni tra utenti e item (luoghi in questo caso), le features dei luoghi, il numero di epochs da applicare con
    l'apprendimento e il numero di threads da impiegare.
    In caso di apprendimento di un modello, i dati da impiegare vengono caricati utilizzando il metodo
    fetch_pugliaeventi del modulo lightfm_data_featcher, in cui i dati vengono caricati dai file .csv presenti nel
    folder engine/data e vengono strutturati in un formato utile per la creazione del modello in LightFM.
    """

    data = fetch_pugliaeventi(min_rating=0.0, indicator_features=False, tag_features=True)

    if os.path.isfile(os.path.join(script_dir, MODEL_CHECKPOINT_PATH)) and not force_model_creation:
        with open(os.path.join(script_dir, MODEL_CHECKPOINT_PATH), 'rb') as fle:
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

        # create model Weighted Approximate-Rank Pairwise
        model = LightFM(loss='warp', item_alpha=ITEM_ALPHA, no_components=NUM_COMPONENTS)

        # train model
        model.fit(
            data['train'],
            item_features=item_features,
            epochs=NUM_EPOCHS,
            num_threads=NUM_THREADS)

        with open(os.path.join(script_dir, MODEL_CHECKPOINT_PATH), 'wb') as fle:
            pickle.dump(model, fle, protocol=pickle.HIGHEST_PROTOCOL)

        # Don't forget the pass in the item features again!
        train_precision = precision_at_k(model, data['train'], k=10, item_features=item_features).mean()
        train_recall = recall_at_k(model, data['train'], k=10, item_features=item_features).mean()
        train_auc = auc_score(model, data['train'], item_features=item_features, num_threads=NUM_THREADS).mean()

        print('Precision: train %.2f.' % (train_precision,))
        print('Recall: train %.2f.' % (train_recall,))
        print('AUC: train %.2f.' % (train_auc,))

    return model, data
