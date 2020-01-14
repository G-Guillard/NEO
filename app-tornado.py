import os
from tornado.web import Application, RequestHandler
from tornado.ioloop import IOLoop
from pymongo import MongoClient
from bson import Code
import pandas as pd
from plotly.utils import PlotlyJSONEncoder
import plotly.graph_objects as go
import plotly.express as px
import json
from sklearn.cluster import KMeans


#Connect to Mongo client and DB
client = MongoClient('db', 27017)
db = client.nasadb
coll = db.neo
collname = "neo" # Near Earth Objects


def get_keys(collection, numeric=False):
    """Get all documents keys, or only numerical keys"""

    if numeric:
        mapper = Code("function() { for (var key in this) { if (typeof(this[key]) == 'number') emit(key, null); } }")
    else:
        mapper = Code("function() { for (var key in this) { emit(key, null); } }")
    reducer = Code("function(key, stuff) { return null; }")

    result = db[collection].map_reduce(mapper, reducer, collection + "_keys")

    return result.distinct("_id")


def get_features(f1, f2=''):
    """Get features from Mongo DB"""

    cursor = coll.find()

    if f2:
        return pd.DataFrame(list(cursor), columns=[f1, f2])
    else:
        return pd.DataFrame(list(cursor), columns=[f1])


class Index(RequestHandler):
    def get(self):
        """Index page contains links to plots of single distributions"""

        items = [key for key in get_keys(collname, numeric=True)]

        self.render('templates/index-tornado.html', items = items)


class Plot1D(RequestHandler):
    def get(self, feature):
        """Plot distribution of a feature"""

        if not feature:
            self.set_status(400)
            return self.render('templates/error-tornado.html', code=400)
        else:
            feature = feature.split("/")[0]
        if not feature in get_keys(collname):
            self.set_status(404)
            return self.render('templates/error-tornado.html', code=404, key=feature)

        df = get_features(feature)

        fig = go.Figure(data=[go.Histogram(x=df[feature])])
        graphJSON = json.dumps(fig, cls=PlotlyJSONEncoder)

        return self.render('templates/plot-tornado.html', plot=json.dumps(graphJSON))


class Plot2D(RequestHandler):
    def get(self, query=''):
        """GET request for 2D plot"""
        features = query.split("/")
        if features[0] and features[1]:
            self.plot(features[0], features[1])
        else:
            self.set_status(400)
            return self.render('templates/error-tornado.html', code=400)

    def post(self):
        """POST request for 2D plot"""
        feature1 = self.get_argument('x')
        feature2 = self.get_argument('y')
        if feature1 and feature2:
            self.plot(feature1, feature2)
        else:
            self.set_status(400)
            return self.render('templates/error-tornado.html', code=400)

    def plot(self, feature1, feature2):
        """Plot 2D distributions of two features"""

        if not feature1 in get_keys(collname):
            self.set_status(404)
            return self.render('templates/error-tornado.html', code=404, key=feature1)
        if not feature2 in get_keys(collname):
            self.set_status(404)
            return self.render('templates/error-tornado.html', code=404, key=feature2)

        df = get_features(feature1, feature2)

        fig = px.scatter(df, x=feature1, y=feature2)
        graphJSON = json.dumps(fig, cls=PlotlyJSONEncoder)

        return self.render('templates/plot-tornado.html', plot=json.dumps(graphJSON))


class KMeansClassifier(RequestHandler):
    def get(self, n_clusters=2):
        """Unsupervised classification attempt"""

        # Default argument value doesn't work, set to ''
        if not n_clusters:
            n_clusters = 2

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

        pred = KMeans(n_clusters=int(n_clusters)).fit_predict(normalized_df)
        df["pred"] = pred

        fig = px.scatter(df, x="Mean Anomaly", y="Eccentricity", color="pred")
        graphJSON = json.dumps(fig, cls=PlotlyJSONEncoder)

        return self.render('templates/plot-tornado.html', plot=json.dumps(graphJSON))


# Launch the app
if __name__ == "__main__":
    app = Application([
        ('/',Index),
        (r'/plots/1D/(.*)',Plot1D),
        (r'/plots/2D/',Plot2D),
        (r'/plots/2D/(.*)',Plot2D),
        (r'/classify/kmeans/(.*)',KMeansClassifier)
        ])
    app.listen(5000)
    IOLoop.current().start()
