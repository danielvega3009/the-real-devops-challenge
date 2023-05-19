from os import environ

from bson import json_util
from bson.objectid import ObjectId
from flask import Flask, jsonify, abort
from flask_pymongo import PyMongo

from src.mongoflask  import MongoJSONEncoder, ObjectIdConverter, find_restaurants

app = Flask(__name__)
#app.config["MONGO_URI"] = "mongodb://localhost:27017/restaurant"
app.config["MONGO_URI"] = environ.get("MONGO_URI")
app.json_encoder = MongoJSONEncoder
app.url_map.converters["objectid"] = ObjectIdConverter
mongo = PyMongo(app)


@app.route("/api/v1/restaurant")
def restaurants():
    restaurants = find_restaurants(mongo)
    print(restaurants)
    return jsonify(restaurants)


@app.route("/api/v1/restaurant/<id>")
def restaurant(id):
    restaurant = mongo.db.restaurant.find_one({"_id": ObjectId(id)})
    if restaurant is None:
        abort(204)
    return jsonify(restaurant)

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=False, port=8080)
