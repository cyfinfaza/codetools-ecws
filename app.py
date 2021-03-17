from pymongo.common import validate
from array import typecodes
from datetime import datetime, time, timedelta, timezone, tzinfo
from types import MethodDescriptorType
from flask import Flask, render_template, request, redirect, session, url_for, Response
from flask_hashing import Hashing
from flask_moment import Moment
from flask_cors import CORS
import uuid
import pymongo
import random
import string
import time
import urllib.parse
import user_agents
import requests
import json
from jrunner5.python.jrunner5 import JRunner5Client, reqres_pb2
from dotenv import load_dotenv
from os import environ
from keyMakeSignCheck.KeyManagement import Signee

load_dotenv()
RECAPTCHA_SECRET = environ.get('RECAPTCHA_SECRET')
RECAPTCHA_SITEKEY = environ.get('RECAPTCHA_SITEKEY')
MONGODB_CONNECTION_STRING = environ.get('MONGODB_CONNECTION_STRING')

signee = Signee(open('keys.json', 'r'))

jrunnerClient = JRunner5Client("127.0.0.1", 5791)

APP_NAME = "CodeTools"

client = pymongo.MongoClient(MONGODB_CONNECTION_STRING)
db = client['codetools']
users = db['users']
codes = db['codes']
content = db['content']

app = Flask(__name__)
hashing = Hashing(app)
moment = Moment(app)
cors = CORS(app)
app.secret_key = "blah blah blah"
app.config["TEMPLATES_AUTO_RELOAD"] = True

DEFAULT_CODE = """public int myMethod(int a) {
	return a + 1;
}"""
DEFAULT_SOLUTION = """public int solution(int a) {
	return a + 1;
}"""
DEFAULT_STARTER_CODE = """public int myMethod(int a) {

}"""


def make_linkID():
    return ''.join(random.choice(string.ascii_letters+string.digits) for x in range(12))


def make_ID(num):
    return ''.join(random.choice(string.ascii_letters+string.digits) for x in range(num))


def make_salt():
    return ''.join(random.choice(string.ascii_letters+string.digits) for x in range(16))


def make_sess_key():
    return ''.join(random.choice(string.ascii_letters+string.digits) for x in range(64))


def username_button(session):
    if validate(session):
        return session['username']
    else:
        return ""


def validate(session):
    if 'username' in session:
        data = users.find_one({'username': session['username']})
        if data != None:
            if 'sessionID' in session:
                try:
                    sessionIDs = [i['id'] for i in data['sessions']]
                    index = sessionIDs.index(session['sessionID'])
                    if hashing.check_value(data['sessions'][index]['hash'], session['sessionKey'], data['sessions'][index]['salt']):
                        return True
                    else:
                        return False
                except:
                    return False
            else:
                return False
        else:
            return False
    else:
        return False


def error_json(error):
    return Response(json.dumps({'status': 'error', 'error': error}), mimetype="application/json")


def warn_json(warning):
    return Response(json.dumps({'status': 'warn', 'warning': warning}), mimetype="application/json")


def success_json(data=None):
    if data:
        return Response(json.dumps({'status': 'success', 'data': data}), mimetype="application/json")
    else:
        return Response(json.dumps({'status': 'success'}), mimetype="application/json")

# def permissionCleanse(values):
# 	clean = True
# 	for value in values:
# 		if type(value) == dict:

# 		elif value[0] == '#':
# 			values.pop(value)


@app.template_filter('iso8601')
def astime(unixtime):
    return datetime.fromtimestamp(float(unixtime), tz=timezone.utc)
    # return datetime.now()


@app.template_filter('duration')
def astimedelta(duration):
    return str(timedelta(seconds=round(duration)))


@app.template_filter('appname')
def appname():
    return APP_NAME


# @app.route('/selfcrash')
# def selfCrash():
# 	return str(0/0)

@app.route("/")
def homepage():
    if 'intent' in session:
        session.pop('intent')
    return render_template("index.html", username=username_button(session))


@app.route("/testeditor")
def editorTest():
    if validate(session):
        userData = users.find_one({'username': session['username']})
        userCode = content.find_one(
            {'owner': userData['_id'], 'type': 'editor_standalone'})
        if userCode == None:
            linkID = make_linkID()
            content.insert_one({
                '_id': str(uuid.uuid4()),
                'type': 'editor_standalone',
                'name': 'testeditor',
                'title': 'Test Editor',
                'owner': userData['_id'],
                'created': float(time.time()),
                'modified': float(time.time()),
                'args_mutable': [],
                'visibility': 'private',
                'linkID': linkID,
                'description': 'This is the description. Visit the Description tab to edit it.',
                'code': DEFAULT_CODE
            })
        else:
            linkID = userCode['linkID']
        return redirect('/'+linkID)
    else:
        session['intent'] = "/testeditor"
        return redirect("/signin")


@app.route("/getcode")
def getCode():
    if validate(session):
        userData = users.find_one({'username': session['username']})
        userCode = codes.find_one({'owner': userData['_id']})
        return userCode['content']
    else:
        return "session invalid"


@app.route('/contentset', methods=['POST'])
def contentSet():
    print(request.json)
    try:
        setRequest = request.json
    except:
        return error_json("JSON parse error")
    towrite = {}
    if "contentID" not in setRequest:
        return error_json('Did not specify contentID')
    contentBefore = content.find_one({'_id': setRequest['contentID']})
    if not contentBefore:
        return error_json("Content not found")
    if not validate(session):
        return error_json("Invalid session")
    userData = users.find_one({'username': session['username']})
    owner = contentBefore['owner'] == userData['_id']
    # extraWarn = None
    if 'code' in setRequest and owner:
        towrite['code'] = setRequest['code']
        towrite['modified'] = float(time.time())
    if 'args_mutable' in setRequest and owner:
        if type(setRequest['args_mutable']) == list:
            towrite['args_mutable'] = setRequest['args_mutable']
            towrite['modified'] = float(time.time())
    if 'description' in setRequest and owner:
        # if type(setRequest['description']) == string:
        towrite['description'] = setRequest['description']
        towrite['modified'] = float(time.time())
    if contentBefore['type'] == 'challenge':
        if 'instructions' in setRequest and owner:
            setRequest['instructions'] = setRequest['instructions'].replace(
                "<safe>", "")
            setRequest['instructions'] = setRequest['instructions'].replace(
                "</safe>", "")
            towrite['instructions'] = setRequest['instructions']
            towrite['modified'] = float(time.time())
        if 'starterCode' in setRequest and owner:
            towrite['starterCode'] = setRequest['starterCode']
            towrite['modified'] = float(time.time())
    if contentBefore['type'] in ['challenge', 'editor_standalone']:
        if 'title' in setRequest and owner:
            towrite['title'] = setRequest['title']
        if 'timeout' in setRequest and owner and type(setRequest['timeout']) == int:
            towrite['timeout'] = setRequest['timeout']

        towrite['modified'] = float(time.time())

    if not towrite:
        if owner:
            return warn_json("Did not write anything, maybe formatted wrong")
        else:
            return warn_json("Did not write anything, maybe formatted wrong, fyi: you do not own this content")
    else:
        content.update_one({'_id': setRequest['contentID']}, {'$set': towrite})
        return json.dumps({'status': 'success', 'modified': [key for key in towrite]})


@app.route('/contentget')
def contentGet():
    try:
        contentID = request.args['id']
    except:
        return error_json("Could not read id")
    userContent = content.find_one({'_id': contentID})
    if not userContent:
        return error_json("Content not found")
    if not validate(session):
        return error_json("Invalid session")
    userData = users.find_one({'username': session['username']})
    owner = userContent['owner'] == userData['_id']
    signature = signee.sign(userContent['_id'])
    userContent['id_sig'] = signature
    if userContent['type'] == 'challenge' and not owner:
        ALLOWED_CHALLENGE_FIELDS = ['_id', 'title',
                                    'description', 'owner', 'modified']
        return success_json({key: userContent[key] for key in userContent if key in ALLOWED_CHALLENGE_FIELDS})
    if owner:
        return success_json(userContent)
    else:
        return error_json("You do not have permission to get this content.")


@app.route('/newchallenge')
def newChallenge():
    if validate(session):
        userData = users.find_one({'username': session['username']})
        userCode = content.find_one(
            {'owner': userData['_id'], 'type': 'challenge'})
        if userCode == None:
            linkID = make_linkID()
            content.insert_one({
                '_id': str(uuid.uuid4()),
                'type': 'challenge',
                'name': 'testchallenge',
                'title': 'Title?',
                'owner': userData['_id'],
                'created': float(time.time()),
                'modified': float(time.time()),
                'args_mutable': [],
                'visibility': 'private',
                'linkID': linkID,
                'description': 'This is the description. Visit the Description tab to edit it.',
                'code': DEFAULT_SOLUTION,
                'starterCode': DEFAULT_STARTER_CODE
            })
        else:
            linkID = userCode['linkID']
        return redirect('/'+linkID)
    else:
        session['intent'] = "/newchallenge"
        return redirect("/signin")


@app.route('/contentpermission')
def contentPermission():
    try:
        contentID = request.args['id']
    except:
        return error_json("Could not read id")
    userContent = content.find_one({'_id': contentID})
    if not userContent:
        return error_json("Content not found")
    if validate(session):
        userData = users.find_one({'username': session['username']})
        if userContent['owner'] == userData['_id']:
            return success_json({'owner': True})
    if userContent['visibility']:
        return success_json({'owner': False, 'visibility': userContent['visibility']})
    else:
        return success_json({'owner': False, 'visibility': 'none'})


@app.route("/setcode", methods=['POST'])
def setCode():
    if validate(session):
        userData = users.find_one({'username': session['username']})
        userCode = codes.update_one({'owner': userData['_id']}, {
                                    '$set': {'content': request.json['code']}})
        return json.dumps({'type': 'ok'})
    else:
        return "session invalid"


@app.route("/runcode")
def runCode():
    contentID = request.args['id']
    userContent = content.find_one({'_id': contentID})
    print(userContent)
    argIDs = []
    args = []
    if 'args_mutable' in userContent:
        for arg in userContent['args_mutable']:
            if arg['arg'] != "":
                argIDs.append(arg['id'])
                args.append(arg['arg'])
    if 'args_immutable' in userContent:
        for arg in userContent['args_immutable']:
            if arg['arg'] != "":
                argIDs.append(arg['id'])
                args.append(arg['arg'])
    if len(args) == 0:
        return success_json({'run': 'success', 'outputs': []})
    code = userContent['code']
    print(code)
    solutionMethod = DEFAULT_SOLUTION
    timeout = 15
    if userContent['type'] == 'editor_challenge':
        assocChallenge = content.find_one(
            {'_id': userContent['assocChallenge']})
        solutionMethod = assocChallenge['code']
        if 'timeout' in assocChallenge:
            timeout = assocChallenge['timeout']
    toRun = "myMethod"
    if userContent['type'] == 'challenge':
        toRun = "solution"
        if 'timeout' in userContent:
            timeout = userContent['timeout']

    response = jrunnerClient.send_java(
        code, toRun, solutionMethod, args, timeout=timeout)
    print(response)
    output = []
    if response.overallResultType != reqres_pb2.Response.RunResultType.CompilerError:
        for i in range(len(argIDs)):
            output.append({
                'id': argIDs[i],
                'output': response.results[i].methodOutput,
                'type': reqres_pb2.OutputResultType.Name(response.results[i].methodOutputType),
                'match': response.results[i].match,
            })
    if response.overallResultType == reqres_pb2.Response.RunResultType.Success:
        return success_json({'run': 'success', 'outputs': output})
    if response.overallResultType == reqres_pb2.Response.RunResultType.CompilerError:
        try:
            formattedError = response.results[0].methodOutput.replace(
                "\\n", "<br>").replace("\\r", "")
            SEARCH = "JavaWrappedClass.java"
            formattedError = formattedError[formattedError.index(
                SEARCH)+len(SEARCH)+4:]
        except:
            formattedError = response.results[0].methodOutput.replace(
                "\\n", "<br>").replace("\\r", "")
        return success_json({'run': 'compilerError', 'error': formattedError})
    if response.overallResultType == reqres_pb2.Response.RunResultType.RuntimeError:
        return success_json({'run': 'runtimeError', 'outputs': output})
    return error_json("Unexpected jrunner5 output")
    # return success_json(output)


@app.route("/signin", methods=['GET', 'POST'])
def signin():
    if request.method == 'GET':
        if 'username' in session:
            return render_template("signin.html", nowuser=session['username'], nowpass="", nowerrors="")
        else:
            return render_template("signin.html", nowuser="", nowpass="", nowerrors="")
    if request.method == 'POST':
        data = users.find_one({'username': request.form['username']})
        if data == None:
            return render_template("signin.html", nowuser=request.form['username'], nowpass=request.form['password'], nowerrors="User not found.")
        if hashing.check_value(data['password_hash'], request.form['password'], salt=data['password_salt']):
            newSessionID = str(uuid.uuid4())
            newSessionKey = make_sess_key()
            newSessionSalt = make_salt()
            print(data['_id'])
            users.update_one({'_id': data['_id']}, {'$addToSet': {'sessions': {
                'id': newSessionID,
                'hash': hashing.hash_value(newSessionKey, salt=newSessionSalt),
                'salt': newSessionSalt,
                'time': str(time.time()),
                'userAgent': str(request.user_agent)
            }}})
            session['username'] = data['username']
            session['sessionID'] = newSessionID
            session['sessionKey'] = newSessionKey
            session['api'] = False
            if 'intent' in session:
                return redirect(session.pop('intent'))
            else:
                return redirect("/")
        else:
            return render_template("signin.html", nowuser=request.form['username'], nowpass=request.form['password'], nowerrors="Wrong password.")


@app.route("/api/signin", methods=['POST'])
def apiSignin():
    if request.method == 'POST':
        data = users.find_one({'username': request.form['username']})
        if data == None:
            return render_template("signin.html", nowuser=request.form['username'], nowpass=request.form['password'], nowerrors="User not found.")
        if hashing.check_value(data['password_hash'], request.form['password'], salt=data['password_salt']):
            newSessionID = str(uuid.uuid4())
            newSessionKey = make_sess_key()
            newSessionSalt = make_salt()
            print(data['_id'])
            users.update_one({'_id': data['_id']}, {'$addToSet': {'sessions': {
                'id': newSessionID,
                'hash': hashing.hash_value(newSessionKey, salt=newSessionSalt),
                'salt': newSessionSalt,
                'time': str(time.time()),
                'userAgent': str(request.user_agent)
            }}})
            session['username'] = data['username']
            session['sessionID'] = newSessionID
            session['sessionKey'] = newSessionKey
            session['api'] = True
            return json.dumps({'type': 'success'})
        else:
            return json.dumps({'type': 'failed'})


@app.route('/signout')
def signout():
    try:
        users.update_one({'username': session['username']}, {
            '$pull': {'sessions': {'id': session['sessionID']}}})
        session.pop('sessionID')
        session.pop('sessionKey')
    except:
        return "there was an error signing out"
    return redirect("/")


@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template("signup.html", sitekey=RECAPTCHA_SITEKEY)
    if request.method == 'POST':
        # print(request.form)
        recaptcha_reponse = json.loads(requests.post('https://www.google.com/recaptcha/api/siteverify', {
            'secret': RECAPTCHA_SECRET, 'response': request.form['g-recaptcha-response']}).text)
        print(recaptcha_reponse)
        if recaptcha_reponse['success']:
            if len(request.form['username']) > 2 and len(request.form['password']) > 7:
                data = users.find_one({'username': request.form['username']})
                if data == None:
                    some_salt = make_salt()
                    actualname = request.form['username']
                    if request.form['actualname'] != "":
                        actualname = request.form['actualname']
                    users.insert_one({
                        '_id': str(uuid.uuid4()),
                        'username': request.form['username'],
                        'actualname': actualname,
                        'password_hash': hashing.hash_value(request.form['password'], salt=some_salt),
                        'password_salt': some_salt,
                        'sessions': []
                    })
                else:
                    return render_template("signup.html", nowuser=request.form['username'], nowname=request.form['actualname'], nowpass=request.form['password'], nowerrors="User already exists. Try signing in.", sitekey=RECAPTCHA_SITEKEY)
            else:
                return render_template("signup.html", nowuser=request.form['username'], nowname=request.form['actualname'], nowpass=request.form['password'], nowerrors="Minimum length: Username: 3 characters; Password: 8 characters", sitekey=RECAPTCHA_SITEKEY)
        else:
            return render_template("signup.html", nowuser=request.form['username'], nowname=request.form['actualname'], nowpass=request.form['password'], nowerrors="ReCaptcha verification error occurred. Ensure you are not a robot.", sitekey=RECAPTCHA_SITEKEY)
        return render_template('messageandredirect.html', messageTitle="Account created.", redirectDescription="You will now be redirected to sign in to your new account.", countdownFrom="5", redirectTo="/signin")


@app.route('/sessions')
def listSessions():
    if validate(session):
        data = users.find_one({'username': session['username']})
        return '<br>'.join(f'<a href="/sessions/kill/{i["id"]}">(kill)</a> {i["time"]} {i["userAgent"]}' for i in data['sessions'])
    else:
        session['intent'] = "/sessions"
        return redirect("/signin")


@app.route('/fetchsession')
def fetchAuth():
    if validate(session):
        sessID_sig = signee.sign(session['sessionID'])
        return success_json({**session, 'sessionID_sig': sessID_sig})
    else:
        return error_json('Invalid Session')


@app.route('/sessions/kill/<sessionID>')
def killSession(sessionID):
    if validate(session):
        try:
            users.update_one({'username': session['username']}, {
                '$pull': {'sessions': {'id': sessionID}}})
            return redirect('/account')
        except:
            return "failed"
    else:
        session['intent'] = "/sessions/kill/"+sessionID
        return redirect("/signin")


@app.route("/changepassword", methods=['GET', 'POST'])
def changePassword():
    if validate(session):
        if request.method == 'GET':
            return render_template("changepassword.html", username=session['username'])
        if request.method == 'POST':
            data = users.find_one({'username': session['username']})
            if hashing.check_value(data['password_hash'], request.form['oldpass'], salt=data['password_salt']):
                if len(request.form['newpass']) > 7:
                    some_salt = make_salt()
                    users.update_one({'username': session['username']}, {'$set': {
                        'password_hash': hashing.hash_value(request.form['newpass'], salt=some_salt),
                        'password_salt': some_salt,
                    }})
                    return render_template('messageandredirect.html', messageTitle="Password changed.", redirectDescription="Returning to the My Account page...", countdownFrom="3", redirectTo="/account")
                else:
                    return render_template("changepassword.html", username=session['username'], nowerrors="New password must be 8 or more characters.")
            else:
                return render_template("changepassword.html", username=session['username'], nowerrors="Wrong password.")
    else:
        session['intent'] = '/changepassword'
        return redirect("/signin")


@app.route("/deleteaccount", methods=['GET', 'POST'])
def deleteAccount():
    if validate(session):
        if request.method == 'GET':
            return render_template("deleteaccount.html", username=session['username'])
        if request.method == 'POST':
            data = users.find_one({'username': session['username']})
            if hashing.check_value(data['password_hash'], request.form['password'], salt=data['password_salt']):
                users.delete_one({'username': session['username']})
                return render_template('messageandredirect.html', messageTitle="Account Deleted.", redirectDescription="Good riddance.", countdownFrom="5", redirectTo="/")
            else:
                return render_template("changepassword.html", username=session['username'], nowerrors="Wrong password.")
    else:
        session['intent'] = '/deleteaccount'
        return redirect("/signin")


@app.route("/changeactualname", methods=['GET', 'POST'])
def changeActualName():
    if validate(session):
        userData = users.find_one({'username': session['username']})
        if request.method == 'GET':
            return render_template("changeactualname.html", username=session['username'], currentName=userData['actualname'])
        if request.method == 'POST':
            if len(request.form['newname']) > 0:
                users.update_one({'username': session['username']}, {
                    '$set': {'actualname': request.form['newname']}})
            else:
                return render_template("changeactualname.html", username=session['username'], currentName=userData['actualname'], nowerrors="Name must be at least one character.")
        return redirect('/account')
    else:
        session['intent'] = '/changepassword'
        return redirect("/signin")


@app.route('/account')
def account():
    if validate(session):
        accountData = users.find_one({'username': session['username']})
        for sess in accountData['sessions']:
            if sess['id'] == session['sessionID']:
                sess['current'] = True
            userAgent = user_agents.parse(sess['userAgent'])
            sess['readableUserAgent'] = userAgent.browser.family + \
                " on " + userAgent.os.family
        accountData['sessions'] = sorted(
            accountData['sessions'], key=lambda k: k['time'], reverse=True)
        if not 'actualname' in accountData:
            users.update_one({'username': accountData['username']}, {
                '$set': {'actualname': accountData['username']}})
            accountData = users.find_one({'username': session['username']})
        return render_template('myaccount.html', user=accountData, username=session['username'])
    else:
        session['intent'] = '/account'
        return redirect('/signin')


@app.route("/<linkID>")
def getContent(linkID):
    contentData = content.find_one({'linkID': linkID})
    if contentData == None:
        return "Not found."
    if validate(session):
        userData = users.find_one({'username': session['username']})
        pageName = "Challenge"
        if contentData['type'] == 'challenge':
            pageName = contentData['name']+": editing challenge"
        if contentData['type'] == 'editor_standalone':
            pageName = contentData['name']+": editing"
        if contentData['owner'] == userData['_id']:
            return render_template('challenge.html', username=session['username'], myContentID=contentData['_id'], editorType=contentData['type'], pageName=pageName)
        elif contentData['type'] == 'challenge':
            editorChallenge = content.find_one(
                {'owner': userData['_id'], 'type': 'editor_challenge', 'assocChallenge': contentData['_id']})
            if not editorChallenge:
                contentID = str(uuid.uuid4())
                args_immutable = [{'id': arg['id'], 'arg':arg['arg'],
                                   'match':False} for arg in contentData['args_mutable']]
                content.insert_one({
                    '_id': contentID,
                    'type': 'editor_challenge',
                    'owner': userData['_id'],
                    'assocChallenge': contentData['_id'],
                    'created': float(time.time()),
                    'modified': float(time.time()),
                    'args_mutable': [],
                    'args_immutable': args_immutable,
                    'code': contentData['starterCode']
                })
            else:
                contentID = editorChallenge['_id']
            return render_template('challenge.html', username=session['username'], myContentID=contentID, editorType='editor_challenge', pageName="Challenge")
        else:
            return "You do not have permission to view this content."
    else:
        session['intent'] = '/'+linkID
        return redirect('/signin')


@app.route('/react')
def editorv2():
    return render_template('react-editor.html')


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=False)
