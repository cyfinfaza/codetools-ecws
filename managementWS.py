import asyncio
import websockets
import json
import random
import string
import uuid
from http import HTTPStatus
from urllib.parse import urlparse
import concurrent.futures
from dotenv import load_dotenv
from os import environ
import pymongo
from bcolors import bcolors

# Configuration
EMPLOYEE_PATH = '/runner'
CUSTOMER_PATH = '/runcode'
EXECUTOR_MAX_WORKERS = 25

class EC_ConnectionGroup:
	EMPLOYEE = 0
	CUSTOMER = 1
	class Connection:
		def __init__(self, connectionType, websocket):
			self.type = connectionType
			self.ws = websocket
	def __init__(self):
		self.employees = set()
		self.customers = set()
	def add(self, connection: Connection):
		if connection.type == EC_ConnectionGroup.EMPLOYEE:
			self.employees.add(connection)
		else:
			self.customers.add(connection)
	def remove(self, connection: Connection):
		if connection in self.customers: self.customers.remove(connection)
		if connection in self.employees: self.employees.remove(connection)
	def allEmployeeWS(self):
		for employee in self.employees:
			yield employee.ws
	def allCustomerWS(self):
		for customer in self.customers:
			yield customer.ws
	def allWS(self):
		for employee in self.employees:
			yield employee.ws
		for customer in self.customers:
			yield customer.ws

class EC_JobManager:
	class Job:
		def __init__(self, customer:EC_ConnectionGroup.Connection, meta={}):
			self.id = str(uuid.uuid4())
			self.customer = customer
			self.employee = None
			self.meta = meta
	def __init__(self, connectionGroup:EC_ConnectionGroup):
		self.connectionGroup = connectionGroup
		self.jobs = set()
	def provision(self, jobToProvision:Job):
		workCount = {connection:0 for connection in self.connectionGroup.employees}
		for jobID in self.jobs:
			job = self.jobs[jobID]
			if job.employee != None:
				if job.employee in workCount:
					workCount[job.employee] += 1
		leastWork = None
		for employee in workCount:
			if leastWork == None:
				leastWork = (employee, workCount[employee])
			else:
				if leastWork[1] > workCount[employee]:
					leastWork = (employee, workCount[employee])
		self.jobs.add(jobToProvision)
		jobToProvision.employee = employee
	def complete(self, jobToRemove:Job):
		self.jobs.remove(jobToRemove)

def initiateJob(job:EC_JobManager.Job):
	# Query the database, get the job, set the requires pre-completion action flag
	# Send the job to the employee
	pass

def completeJob(job:EC_JobManager.Job, employeeResponse):
	# Verify the requires pre-completion action flag, potentially write to the database
	# Send the response to the customer
	pass

# Load IP Allow List
allowedIPs = list(line.strip() for line in open("managementWS_allowedIPs.txt", "r").readlines())
print(f'Allwed IPs: {allowedIPs}')

# Load MongoDB
load_dotenv()
MONGODB_CONNECTION_STRING = environ.get('MONGODB_CONNECTION_STRING')
client = pymongo.MongoClient(MONGODB_CONNECTION_STRING)
db = client['codetools']
users = db['users']
codes = db['codes']
content = db['content']

# Connection and Job Management
connectionGroup = EC_ConnectionGroup()
jobManager = EC_JobManager(connectionGroup)

# Set up thread pool executor (to avoid locking the asyncio thread / main thread with DB queries)
executor = concurrent.futures.ThreadPoolExecutor(max_workers=EXECUTOR_MAX_WORKERS)

# Override process_request to perform validation
async def initial(path, request_headers):
	remoteIP = request_headers['Remote-IP']
	print(f'[{remoteIP}] {path}', end=" ")
	pathonly = urlparse(path).path
	if pathonly not in [EMPLOYEE_PATH, CUSTOMER_PATH]:
		print(f"{bcolors.WARNING}INVALID PATH{bcolors.ENDC}")
		return HTTPStatus.NOT_FOUND, [('server', 'managementWS_ipauth')], "Invalid Path".encode('UTF-8')
	if (remoteIP in allowedIPs and pathonly==EMPLOYEE_PATH) or path==CUSTOMER_PATH:
		print(f"{bcolors.OKGREEN}IPAUTH GRANTED{bcolors.ENDC}")
		return None
	else:
		print(f"{bcolors.FAIL}IPAUTH REJECTED{bcolors.ENDC}")
		return HTTPStatus.UNAUTHORIZED, [('server', 'managementWS_ipauth')], "Access Denied".encode('UTF-8')

# Process WebSocket connections
async def server(websocket, path):
	pathonly = urlparse(path).path
	if pathonly == EMPLOYEE_PATH:
		CONNECTION_TYPE = EC_ConnectionGroup.EMPLOYEE
	else:
		CONNECTION_TYPE = EC_ConnectionGroup.CUSTOMER
	connection = EC_ConnectionGroup.Connection(CONNECTION_TYPE, websocket)
	connectionGroup.add(connection)
	print("ADD INDIVIDUAL "+str(id(websocket)))
	# for conn in connectionGroup.allWS():
	# 	await conn.send(json.dumps({'type': 'rxGroupUpdate', 'viewers':len(connected)}))
	try:
		# print(f'Connected users: {len(connected)}')
		async for message in websocket:
			print(str(message))
			# with open(make_umid(), 'wb') as file:
			# 	file.write(message)
			# ((await ws.send(message)) for ws in connected)
			# (await ws.send(message) for ws in connected if ws != websocket)
			for conn in (conn for conn in connectionGroup.allWS() if conn != websocket):
				await conn.send(message)
			# await conn.send("recieved")
		print("END INDIVIDUAL LOGIC LOOP "+str(id(websocket)))
	except Exception as e:
		print(f"Exception {e}")
	finally:
		print("DELETE INDIVIDUAL "+str(id(websocket)))
		connectionGroup.remove(connection)
		# print(f'Connected users: {len(connected)}')
		# for conn in connected:
		# 	await conn.send(json.dumps({'type': 'rxGroupUpdate', 'viewers':len(connected)}))

# Start WebSocket server
try:
	start_server = websockets.serve(server, "0.0.0.0", 5000, process_request=initial)
	asyncio.get_event_loop().run_until_complete(start_server)
	asyncio.get_event_loop().run_forever()
except KeyboardInterrupt or SystemExit:
	try:
		print("Exiting...")
		# Do whatever you need to do before exiting (not needed atm)
	except KeyboardInterrupt or SystemExit:
		print("Exiting regardless.")