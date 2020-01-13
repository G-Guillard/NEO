from flask import Flask, render_template, send_file, request
from pymongo import MongoClient
from bson import Code
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from sklearn.cluster import KMeans


#Flask constructor
app = Flask(__name__)

#Connect to Mongo client and DB
client = MongoClient()
db = client.nasadb
coll = db.neo
collname = "neo" # Near Earth Objects


def get_keys(collection, numeric=False):
    """Get all documents keys, or only numerical keys"""

    if numeric:
        map = Code("function() { for (var key in this) { if (typeof(this[key]) == 'number') emit(key, null); } }")
    else:
        map = Code("function() { for (var key in this) { emit(key, null); } }")
    reduce = Code("function(key, stuff) { return null; }")

    result = db[collection].map_reduce(map, reduce, collection + "_keys")

    return result.distinct("_id")


def get_features(f1, f2=''):
    """Get features from Mongo DB"""

    cursor = coll.find()

    if f2:
        return pd.DataFrame(list(cursor), columns=[f1, f2])
    else:
        return pd.DataFrame(list(cursor), columns=[f1])


@app.route('/')
def index():
    """Index page contains links to plots of single distributions"""

    items = [key for key in get_keys(collname, numeric=True)]

    return render_template('index.html', items = items)


@app.route('/plots/1D/')
@app.route('/plots/1D/<string:feature>/')
def plot_distribution(feature=''):
    """Plot distribution of a feature"""

    if not feature:
        return render_template('error.html', code=400), 400
    if not feature in get_keys(collname):
        return render_template('error.html', code=404, key=feature), 404

    df = get_features(feature)
    df.hist(feature)

    img = BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)

    return send_file(img, mimetype='image/png')


@app.route('/plots/2D/')
@app.route('/plots/2D/', methods=['POST'])
@app.route('/plots/2D/<string:feature1>/')
@app.route('/plots/2D/<string:feature1>/<string:feature2>/')
def plot2d(feature1='', feature2=''):
    """Plot 2D distributions of two features"""

    if request.method == 'POST':
        feature1 = request.form['x']
        feature2 = request.form['y']

    if not feature1 or not feature2:
        return render_template('error.html', code=400), 400
    if not feature1 in get_keys(collname):
        return render_template('error.html', code=404, key=feature1), 404
    if not feature2 in get_keys(collname):
        return render_template('error.html', code=404, key=feature2), 404

    df = get_features(feature1, feature2)
    plot = df.plot.scatter(feature2, feature1)

    img = BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)

    return send_file(img, mimetype='image/png')


@app.route('/classify/kmeans/')
@app.route('/classify/kmeans/<int:n_clusters>/')
def classify(n_clusters=2):
    """Unsupervised classification attempt"""

    cursor = coll.find()
    df = pd.DataFrame(list(cursor), columns=[
        'Absolute Magnitude',
        'Est Dia in M(min)',
        'Est Dia in M(max)',
        'Relative Velocity km per hr',
#        'Miss Dist (Astronomical)',
        'Minimum Orbit Intersection',
        'Jupiter Tisserand Invariant',
        'Epoch Osculation',
        'Eccentricity',
        'Semi Major Axis',
        'Inclination',
        'Asc Node Longitude',
        'Orbital Period',
        'Perihelion Distance',
        'Perihelion Arg',
        'Aphelion Dist',
        'Perihelion Time',
        'Mean Anomaly',
        'Mean Motion'
    ])
    normalized_df = (df - df.mean()) / df.std()
    normalized_df = normalized_df.dropna()

    pred = KMeans(n_clusters=n_clusters).fit(normalized_df)

    return "Clusters centers (k=" + str(n_clusters) + ") : " + str(pred.cluster_centers_)


