import pymongo
import pprint
import pickle

myclient = pymongo.MongoClient("mongodb://localhost:27017/")

mydb = myclient["jones2"]
mycol = mydb["vendors"]

entire_db = list()

for post in mycol.find():
    entire_db.append(post)

print(len(entire_db))

pickle_out = open("businesses.pickle", "wb")
pickle.dump(entire_db, pickle_out)
pickle_out.close()
