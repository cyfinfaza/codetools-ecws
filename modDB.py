from os import environ
from dotenv.main import load_dotenv
import pymongo
from concurrent.futures import ThreadPoolExecutor, as_completed
import uuid
import random

load_dotenv()
MONGODB_CONNECTION_STRING = environ.get('MONGODB_CONNECTION_STRING')
client = pymongo.MongoClient(MONGODB_CONNECTION_STRING)
db = client['test']
testColl = db['test']
# users = db['users']
# codes = db['codes']
# content = db['content']

cursorAll = testColl.find({})
count = cursorAll.count()
print(f"{count} documents found")

# EXECUTOR_MAX_WORKERS = 1
# executor = ThreadPoolExecutor(max_workers=EXECUTOR_MAX_WORKERS)
# broken = 0
# def addRandomValue(i):
# 	global broken
# 	u = cursorAll[i]
# 	broken += 1
# 	return None

# executuor_futures = (executor.submit(addRandomValue(i)) for i in range(count))

# done = 0
# for _ in as_completed(executuor_futures):
# 	print("\r"+str(done))
# print(broken)
done = 0
for entry in cursorAll:
	testColl.update_one({'_id':entry['_id']}, {'$set':{'randomval':random.randint(0,65535)}})
	done+=1
	print(str(int((done/count)*100))+"% complete", end="\r")
print()

# toAdd = list([{'_id':str(uuid.uuid4()), 'content':'somecontent'} for _ in range(100)])
# testColl.insert_many(toAdd)