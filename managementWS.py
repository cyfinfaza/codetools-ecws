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
from websockets.server import WebSocketServerProtocol
from bcolors import bcolors
from keyMakeSignCheck.KeyManagement import Signee
import time
import requests
from flask_hashing import Hashing as hashing
import jrunner5.python.reqres_pb2 as reqres_pb2

hasher = hashing()

# Configuration
EMPLOYEE_PATH = '/ecws/runner'
CUSTOMER_PATH = '/ecws/runcode'
EXECUTOR_MAX_WORKERS = 5


class EC_ConnectionGroup:
    EMPLOYEE = 0
    CUSTOMER = 1

    class Connection:
        def __init__(self, connectionType, websocket: WebSocketServerProtocol):
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
        if connection in self.customers:
            self.customers.remove(connection)
        if connection in self.employees:
            self.employees.remove(connection)

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
        def __init__(self, customer: EC_ConnectionGroup.Connection, meta={}):
            self.id = str(uuid.uuid4())
            self.customer: EC_ConnectionGroup.Connection = customer
            self.employee: EC_ConnectionGroup.Connection = None
            self.meta = meta

    def __init__(self, connectionGroup: EC_ConnectionGroup):
        self.connectionGroup = connectionGroup
        self.jobs = set()

    def jobsByID(self):
        return {job.id: job for job in self.jobs}

    def provision(self, jobToProvision: Job):
        if len(self.connectionGroup.employees) < 1:
            return False
        workCount = {
            connection: 0 for connection in self.connectionGroup.employees}
        for jobID in self.jobsByID():
            job = self.jobsByID()[jobID]
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
        return True

    def complete(self, jobToRemove: Job):
        self.jobs.remove(jobToRemove)


class WS_SendObject:
    def __init__(self, ws: WebSocketServerProtocol, message: str):
        self.ws = ws
        self.message = message


# Load IP Allow List
allowedIPs = list(line.strip() for line in open(
    "managementWS_allowedIPs.txt", "r").readlines())
print(f'Allwed IPs: {allowedIPs}')

# Load authenticity checker signee
signee = Signee(open('keys.json', 'r'))

# Load MongoDB
load_dotenv()
MONGODB_CONNECTION_STRING = environ.get('MONGODB_CONNECTION_STRING')
client = pymongo.MongoClient(MONGODB_CONNECTION_STRING)
db = client['codetools']
users = db['users']
codes = db['codes']
content = db['content']

# Validator


def getUserID(session):
    if 'username' in session:
        data = users.find_one({'username': session['username']})
        if data != None:
            if 'sessionID' in session:
                # try:
                sessionIDs = [i['id'] for i in data['sessions']]
                index = sessionIDs.index(session['sessionID'])
                # if bytes(data['sessions'][index]['hash'], "UTF-8") == hashlib.sha256(bytes(session['sessionKey']+data['sessions'][index]['salt'], "UTF-8")).digest():
                if hasher.check_value(data['sessions'][index]['hash'], session['sessionKey'], data['sessions'][index]['salt']):
                    return data['_id']
                else:
                    print("verif err 1")
                    return None
                # except Exception as e:
                #     print(f"verif err {e}")
                #     return None
            else:
                print("verif err 3")
                return None
        else:
            print("verif err 4")
            return None
    else:
        print("verif err 5")
        return None


def getRun(contentID):
    runContent = content.find_one({'_id': contentID})
    code = runContent['code']
    args = []
    argIDs = []
    for arg in runContent['args_mutable']:
        args.append(arg['arg'])
        argIDs.append(arg['id'])
    if 'args_immutable' in runContent:
        for arg in runContent['args_immutable']:
            args.append(arg['arg'])
            argIDs.append(arg['id'])
    return {'code': code, 'args': args, 'argIDs': argIDs}


def generateRequestBinary(job: EC_JobManager.Job):
    request = reqres_pb2.Request()
    request.id = job.id
    request.inputMethod = job.meta['code']
    request.inputMethodName = "myMethod"
    request.solutionMethod = """public int solution(int a) {
    return a + 1;
}"""
    request.inputs.extend(job.meta['args'])
    return request.SerializeToString()


# Connection and Job Management
connectionGroup = EC_ConnectionGroup()
jobManager = EC_JobManager(connectionGroup)

# Set up thread pool executor (to avoid locking the asyncio thread / main thread with DB queries)
executor = concurrent.futures.ThreadPoolExecutor(
    max_workers=EXECUTOR_MAX_WORKERS)

# Responses


def json_statusUpdate(message):
    return json.dumps({'type': 'statusUpdate', 'status': message})


def json_error(message):
    return json.dumps({'type': 'error', 'error': message})


# Allow sending outside main event loop
loop = asyncio.get_event_loop()
sendQueue = asyncio.Queue()


async def asyncSendWorker(queue=sendQueue):
    while True:
        try:
            tosend = await queue.get()
            print("something is happening")
            await tosend[0].send(tosend[1])
            queue.task_done()
        except:
            await asyncio.sleep(1)
        # print("heartbeat")
        # await asyncio.sleep(1)


async def send(ws: WebSocketServerProtocol, message: str):
    print("the new thing happened")
    await ws.send(message)


def initiateJob(job: EC_JobManager.Job):
    # Query the database, get the job, set the requires pre-completion action flag
    # Send the job to the employee
    # sendQueue.put_nowait((job.customer.ws, json_statusUpdate("jobInitiating")))
    print('job initiating')
    # asyncio.run_coroutine_threadsafe(job.customer.ws.send("something, anytihng"), loop)
    # requests.get('https://google.com/')
    time.sleep(0.5)
    # sendQueue.put_nowait((job.customer.ws, json_statusUpdate("jobSubmitted")))
    print('job submitted')
    pass


def completeJob(job: EC_JobManager.Job, employeeResponse):
    # Verify the requires pre-completion action flag, potentially write to the database
    # Send the response to the customer
    pass

# Override process_request to perform validation


async def initial(path, request_headers):
    remoteIP = request_headers['Remote-IP']
    print(f'[{remoteIP}] {path}', end=" ")
    pathonly = urlparse(path).path
    if pathonly not in [EMPLOYEE_PATH, CUSTOMER_PATH]:
        print(f"{bcolors.WARNING}INVALID PATH{bcolors.ENDC}")
        return HTTPStatus.NOT_FOUND, [('server', 'managementWS_ipauth')], "Invalid Path".encode('UTF-8')
    if (remoteIP in allowedIPs and pathonly == EMPLOYEE_PATH) or path == CUSTOMER_PATH:
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
    try:
        if connection.type == EC_ConnectionGroup.CUSTOMER:
            async for message in websocket:
                await websocket.send(json_statusUpdate("Request Recieved"))
                messageContent = str(message)
                try:
                    runRequest = json.loads(messageContent)
                except:
                    await websocket.send(json_error("E01 msg corrupt"))
                    continue
                if not all(key in runRequest for key in ['contentID', 'id_sig', 'auth']):
                    await websocket.send(json_error("E02: msg 1+ key missing"))
                    continue
                if not all(key in runRequest['auth'] for key in ['sessionID', 'sessionKey', 'sessionID_sig']):
                    await websocket.send(json_error("E03: auth 1+ key missing"))
                    continue
                if not signee.verify(runRequest['contentID'], runRequest['id_sig']):
                    await websocket.send(json_error("E04: id_sig fail"))
                    continue
                if not signee.verify(runRequest['auth']['sessionID'], runRequest['auth']['sessionID_sig']):
                    await websocket.send(json_error("E05: sessionID_sig fail"))
                    continue
                userID = await loop.run_in_executor(executor, getUserID, runRequest['auth'])
                if not userID:
                    await websocket.send(json_error("E06: sess verif fail"))
                    continue
                await websocket.send(json_statusUpdate("Job initiating..."))
                runMeta = await loop.run_in_executor(executor, getRun, runRequest['contentID'])
                runJob = EC_JobManager.Job(
                    connection, {'id': runRequest['contentID'], **runMeta})
                if not jobManager.provision(runJob):
                    await websocket.send(json_error("E07: No runner nodes"))
                    continue
                requestBinary = generateRequestBinary(runJob)
                await runJob.employee.ws.send(requestBinary)
                await websocket.send(json_statusUpdate("Job in progress..."))
                print(str(message))
                # for conn in (conn for conn in connectionGroup.allWS() if conn != websocket):
                # 	await conn.send(message)
        elif connection.type == EC_ConnectionGroup.EMPLOYEE:
            async for message in websocket:
                response = reqres_pb2.Response()
                response.ParseFromString(message)
                print(str(response))
                job: EC_JobManager.Job = jobManager.jobsByID()[response.id]
                resultsMerged = []
                for i in range(len(response.results)):
                    resultsMerged.append(
                        {'id': job.meta['argIDs'][i], 'output': response.results[i].methodOutput, 'match': response.results[i].match})
                await job.customer.ws.send(json.dumps({'type': 'jobComplete', 'data': resultsMerged}))
                # for conn in (conn for conn in connectionGroup.allWS() if conn != websocket):
                #     await conn.send(message)
        print("END INDIVIDUAL LOGIC LOOP "+str(id(websocket)))
    except Exception as e:
        print(f"Exception {e}")
    finally:
        print("DELETE INDIVIDUAL "+str(id(websocket)))
        connectionGroup.remove(connection)

# Start WebSocket server
try:
    start_server = websockets.serve(
        server, "0.0.0.0", 5600, process_request=initial, compression=None)
    # loop.run_until_complete(asyncio.gather((start_server, asyncSendWorker())))
    loop.run_until_complete(start_server)
    loop.run_forever()
except KeyboardInterrupt or SystemExit:
    try:
        print("Exiting...")
        # Do whatever you need to do before exiting (not needed atm)
    except KeyboardInterrupt or SystemExit:
        print("Exiting regardless.")
