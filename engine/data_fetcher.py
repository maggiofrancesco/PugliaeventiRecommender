import itertools
import numpy as np
import scipy.sparse as sp


def _read_raw_data():
    """
    Return the raw lines of the train and test files.
    """

    ratings = open('/home/francesco/PycharmProjects/RecommenderSystem/pugliaeventi/data/ratings.csv', 'rb')
    items = open('/home/francesco/PycharmProjects/RecommenderSystem/pugliaeventi/data/items.csv', 'rb')
    users = open('/home/francesco/PycharmProjects/RecommenderSystem/pugliaeventi/data/users.csv', 'rb')
    labels_item = open('/home/francesco/PycharmProjects/RecommenderSystem/pugliaeventi/data/labels_item.csv', 'rb')
    labels_user = open('/home/francesco/PycharmProjects/RecommenderSystem/pugliaeventi/data/labels_user.csv', 'rb')

    return (ratings.read().decode().split('\n'),
            items.read().decode().split('\n'),
            users.read().decode().split('\n'),
            labels_item.read().decode(errors='ignore').split('\n'),
            labels_user.read().decode(errors='ignore').split('\n'))


def _parse(data):

    for line in data:

        if not line:
            continue

        uid, iid, rating = [int(x) for x in line.split(',')]

        # Subtract one from ids to shift
        # to zero-based indexing
        yield uid - 1, iid - 1, rating


def _get_dimensions(train_data, test_data):

    uids = set()
    iids = set()

    if test_data is not None:
        data = itertools.chain(train_data, test_data)
    else:
        data = train_data

    for uid, iid, _ in data:
        uids.add(uid)
        iids.add(iid)

    rows = max(uids) + 1
    cols = max(iids) + 1

    return rows, cols


def _build_interaction_matrix(rows, cols, data, min_rating):

    mat = sp.lil_matrix((rows, cols), dtype=np.int32)

    for uid, iid, rating in data:
        if rating >= min_rating:
            mat[uid, iid] = rating

    return mat.tocoo()


def _parse_item_metadata(num_items, item_metadata_raw, item_tags_raw, num_users, user_metadata_raw, user_tags_raw):

    item_tags = []
    user_tags = []

    for line in item_tags_raw:
        if line:
            tid, tag = line.split(',')
            item_tags.append('tag:{}'.format(tag))

    for line in user_tags_raw:
        if line:
            tid, tag = line.split(',')
            user_tags.append('tag:{}'.format(tag))

    iid_feature_labels = np.empty(num_items, dtype=np.object)
    item_tag_feature_labels = np.array(item_tags)

    uid_feature_labels = np.empty(num_users, dtype=np.object)
    user_tag_feature_labels = np.array(user_tags)

    iid_features = sp.identity(num_items,
                              format='csr',
                              dtype=np.float32)
    item_tag_features = sp.lil_matrix((num_items, len(item_tags)),
                                   dtype=np.float32)

    uid_features = sp.identity(num_users,
                               format='csr',
                               dtype=np.float32)
    user_tag_features = sp.lil_matrix((num_users, len(user_tags)),
                                      dtype=np.float32)

    for line in item_metadata_raw:

        if not line:
            continue

        splt = line.split(',')

        # Zero-based indexing
        iid = int(splt[0]) - 1
        name = splt[1]

        iid_feature_labels[iid] = name

        item_tags = [idx for idx, val in
                       enumerate(splt[3:])
                       if int(val) > 0]

        for tid in item_tags:
            item_tag_features[iid, tid] = 1.0

    for line in user_metadata_raw:

        if not line:
            continue

        splt = line.split(',')

        # Zero-based indexing
        uid = int(splt[0]) - 1
        user_city = splt[1]

        uid_feature_labels[uid] = "{0}.{1}".format("username", user_city)

        user_tags = [idx for idx, val in
                       enumerate(splt[2:])
                       if int(val) > 0]

        for tid in user_tags:
            user_tag_features[uid, tid] = 1.0

    return (iid_features, iid_feature_labels, item_tag_features.tocsr(), item_tag_feature_labels,
            uid_features, uid_feature_labels, user_tag_features.tocsr(), user_tag_feature_labels)


def fetch_pugliaeventi(indicator_features=True, tag_features=False, min_rating=0.0):
    """
    Fetch the `Movielens 100k dataset <http://grouplens.org/datasets/movielens/100k/>`_.

    The dataset contains 100,000 interactions from 1000 users on 1700 movies,
    and is exhaustively described in its
    `README <http://files.grouplens.org/datasets/movielens/ml-100k-README.txt>`_.

    Parameters
    ----------

    data_home: path, optional
        Path to the directory in which the downloaded data should be placed.
        Defaults to ``~/lightfm_data/``.
    indicator_features: bool, optional
        Use an [n_items, n_items] identity matrix for item features. When True with genre_features,
        indicator and genre features are concatenated into a single feature matrix of shape
        [n_items, n_items + n_genres].
    tag_features: bool, optional
        Use a [n_items, n_genres] matrix for item features. When True with item_indicator_features,
        indicator and genre features are concatenated into a single feature matrix of shape
        [n_items, n_items + n_genres].
    min_rating: float, optional
        Minimum rating to include in the interaction matrix.
    download_if_missing: bool, optional
        Download the data if not present. Raises an IOError if False and data is missing.

    Notes
    -----

    The return value is a dictionary containing the following keys:

    Returns
    -------

    train: sp.coo_matrix of shape [n_users, n_items]
         Contains training set interactions.
    test: sp.coo_matrix of shape [n_users, n_items]
         Contains testing set interactions.
    item_features: sp.csr_matrix of shape [n_items, n_item_features]
         Contains item features.
    item_feature_labels: np.array of strings of shape [n_item_features,]
         Labels of item features.
    item_labels: np.array of strings of shape [n_items,]
         Items' titles.
    """

    if not (indicator_features or tag_features):
        raise ValueError('At least one of item_indicator_features '
                         'or genre_features must be True')

    # Load raw data
    (ratings, items, users, labels_item, labels_user) = _read_raw_data()

    # Figure out the dimensions
    num_users, num_items = _get_dimensions(_parse(ratings), None)

    # Load train interactions
    train = _build_interaction_matrix(num_users,
                                      num_items,
                                      _parse(ratings),
                                      min_rating)
    # Load test interactions
    """test = _build_interaction_matrix(num_users,
                                     num_items,
                                     _parse(test_raw),
                                     min_rating)"""

    # assert train.shape == test.shape

    # Load metadata features
    (iid_features, iid_feature_labels, item_tag_features_matrix, item_tag_feature_labels,
     uid_features, uid_feature_labels, user_tag_features_matrix, user_tag_feature_labels
     ) = _parse_item_metadata(num_items, items, labels_item, num_users, users, labels_user)

    assert iid_features.shape == (num_items, len(iid_feature_labels))
    assert item_tag_features_matrix.shape == (num_items, len(item_tag_feature_labels))

    assert uid_features.shape == (num_users, len(uid_feature_labels))
    assert user_tag_features_matrix.shape == (num_users, len(user_tag_feature_labels))

    if indicator_features and not tag_features:
        item_features = iid_features
        item_feature_labels = iid_feature_labels
        user_features = uid_features
        user_feature_labels = uid_feature_labels
    elif tag_features and not indicator_features:
        item_features = item_tag_features_matrix
        item_feature_labels = item_tag_feature_labels
        user_features = user_tag_features_matrix
        user_feature_labels = user_tag_feature_labels
    else:
        item_features = sp.hstack([iid_features, item_tag_features_matrix]).tocsr()
        item_feature_labels = np.concatenate((iid_feature_labels,
                                         item_tag_feature_labels))
        user_features = sp.hstack([uid_features, user_tag_features_matrix]).tocsr()
        user_feature_labels = np.concatenate((uid_feature_labels,
                                              user_tag_feature_labels))

    data = {'train': train,
            #'test': test,
            'item_features': item_features,
            'user_features': user_features,
            'item_feature_labels': item_feature_labels,
            'item_labels': iid_feature_labels,
            'user_feature_labels': user_feature_labels,
            'user_labels': uid_feature_labels}

    return data
