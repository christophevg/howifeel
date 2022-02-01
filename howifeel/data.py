import os
from pymongo import MongoClient

DB       = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/howifeel")
mongo    = MongoClient(DB)
database = DB.split("/")[-1]
if "?" in database: database = database.split("?")[0]

db       = mongo[database]
