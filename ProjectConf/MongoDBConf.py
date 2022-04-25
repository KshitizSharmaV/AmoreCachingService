# Mongo Client
from pymongo import MongoClient
mongoClient = MongoClient('localhost', 27017)

amoreCacheDBName= "AmoreCacheDB"
# You won't be able to see Collection/DB in system without inserting a document
amoreCacheDB = mongoClient[amoreCacheDBName]
    
    
