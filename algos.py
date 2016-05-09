from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import rethinkdb as r
import datetime

def kmeans(data, n_features, true_k, init, n_init, max_iter, tol, precompute_distance,
           verbose, random_state, copy_x, n_jobs):
    result = []
    vectorizer = TfidfVectorizer(stop_words='english')
    X = vectorizer.fit_transform(data)

    model = KMeans(n_clusters=true_k, init=init, n_init=n_init, max_iter=max_iter, tol=tol,
                   precompute_distances=precompute_distance, verbose=verbose,
                   random_state=random_state, copy_x=copy_x, n_jobs=n_jobs)
    model.fit(X)
    order_centroids = model.cluster_centers_.argsort()[:, ::-1]
    terms = vectorizer.get_feature_names()
    for i in range(true_k):
        for ind in order_centroids[i, :n_features]:
            result.append(' %s' % terms[ind])
    return result


def kmeans_alt(data, ids):
    result = []
    true_k = 5
    vectorizer = TfidfVectorizer(stop_words='english')
    X = vectorizer.fit_transform(data)

    model = KMeans(n_clusters=true_k, init='k-means++', max_iter=100, n_init=1)

    # one result json per run
    jsn = {}    # result cluster json with params, features and docs
    jsn['id'] = str(datetime.datetime.now())    # set ID
    jsn['config'] = model.get_params()  # set CONFIG/ PARAMS
    jsn['data'] = []    # init DATA Array

    model.fit_predict(X)
    predictions = (model.predict(X))
    predict_map = {}    # init dict, collect all articleIds per cluster
    i = 0
    for i in range(len(predictions)):
        if(predict_map.has_key(predictions[i])):
            predict_map[predictions[i]].append(ids[i])  # append articleId to dict
        else:
            predict_map[predictions[i]] = []    # create new array for articleIds
    order_centroids = model.cluster_centers_.argsort()[:, ::-1]
    terms = vectorizer.get_feature_names()
    for i in range(true_k):
        jsn_tmp = {}    # temp json for each cluster
        ary_tmp_feat = []   # init temp array of features
        ary_tmp_docs = []   # init temp array of docs/id
        for ind in order_centroids[i, :3]:
            ary_tmp_feat.append(' %s' % terms[ind])  # append features
            result.append(' %s' % terms[ind])
        jsn_tmp['features'] = ary_tmp_feat   # set array of features
        jsn_tmp['articleIds'] = predict_map[i]  # set array of docs
        jsn['data'].append(jsn_tmp) # write jsn_tmp to jsn['data']
    print('json')
    print(jsn)

    c = r.connect()
    writeResult = r.db("themis").table("results").insert(jsn).run(c)

    return result
