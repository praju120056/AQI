# backend/database.py
import pymongo
from datetime import datetime
from .config import MONGO_URI

try:
    client = pymongo.MongoClient(MONGO_URI)
    db = client["aqi_project_db"]
    aqi_collection = db["aqi_data"]
    client.server_info()
    print(f"Connected to MongoDB. Using database: {db.name}")
except Exception as e:
    print(f"An unknown error occurred during DB initialization: {e}")
    exit(1)

# Ensure indexes to speed queries (safe to call on every startup)
try:
    aqi_collection.create_index([("timestamp", pymongo.DESCENDING)])
    aqi_collection.create_index([("source", pymongo.ASCENDING), ("timestamp", pymongo.DESCENDING)])
except Exception as e:
    print("Warning: could not create indexes:", e)

def save_aqi_record(record_data):
    """
    Saves a single AQI record (a Python dict) to the database.
    """
    try:
        record_data['timestamp'] = datetime.utcnow()
        aqi_collection.insert_one(record_data)
        print(f"Record saved for source: {record_data.get('source')}")
        return True
    except Exception as e:
        print(f"Error saving record to MongoDB: {e}")
        return False

def get_all_aqi_records(limit=100):
    """
    Fetches the latest 'limit' records from ALL sources.
    """
    try:
        records = aqi_collection.find({}, {"_id": 0}).sort("timestamp", pymongo.DESCENDING).limit(limit)
        return list(records)
    except Exception as e:
        print(f"Error fetching all records from MongoDB: {e}")
        return []

def get_latest_aqi_records(source, limit=100):
    """
    Fetches the latest 'limit' records for a specific 'source'.
    """
    try:
        records = aqi_collection.find({"source": source}, {"_id": 0}).sort("timestamp", pymongo.DESCENDING).limit(limit)
        return list(records)
    except Exception as e:
        print(f"Error fetching records from MongoDB: {e}")
        return []
