#pylint:disable=invalid-name
#pylint:disable=line-too-long
#pylint:disable=missing-module-docstring
#pylint:disable=missing-function-docstring
#pylint:disable=missing-class-docstring
#pylint:disable=import-error,fixme,bad-whitespace,trailing-whitespace,too-many-arguments
#pylint:disable=unused-import

from copy import deepcopy
import time
import os
import io
from datetime import datetime, timedelta
import random
import string
import json
from enum import Enum

import PIL
from profanityfilter import ProfanityFilter
from flask import Flask, redirect, url_for, request, render_template, jsonify, send_file
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_api import status
from pymongo import MongoClient, ReturnDocument
from bson.objectid import ObjectId

from imaging import getRandomHide, getCityImage, getMatzahImage

DEBUG = False
DEFAULT_WIN_COUNT = 0
CITIES = [
    'Toronto',
    'Montreal',
    'Tel Aviv',
    'Amsterdam',
    'New York City',
    'Los Angeles',
    'Kiev',
    'Vancouver',
    'Berlin',
    'Prague',
    'Florence',
    'Warsaw',
    'Jerusalem',
    'Chicago',
    'Philadelphia',
    'Buenos Aires',
    'London',
    'Paris',
    'Melbourne'
]

img_cache = dict()
def get_img_cached(imageId):

    # decompose the imageId, paths etc
    city, hideImgIdx = imageId
    city = city.lower().replace(" ", "_")
    folderPath = os.path.join('cities', city, 'img')
    imgPath = os.path.join(folderPath, f'{city}_hidden{hideImgIdx}.jpg')

    # imgPath is the key into the cache
    if imgPath in img_cache:
        return img_cache[imgPath]

    # figure out the coords
    txtPath = os.path.join(folderPath, 'matza_xy.txt')
    with open(txtPath, 'r') as file:
        lines = file.readlines()

    numHides = len(lines)
    if hideImgIdx >= numHides:
        # if there is no image for this idx, then forget it
        return None
    coords = lines[hideImgIdx].split(',')
    x = int(coords[0])
    y = int(coords[1])
    w, h = getMatzahImage().size
    img = PIL.Image.open(imgPath)

    imgByteArr = io.BytesIO()
    img.save(imgByteArr, format='PNG')
    imgByteArr = imgByteArr.getvalue()

    rect = (x, y, w, h)
    W, H = img.size
    percentRect = (x/W, y/H, w/W, h/H)

    result = (imgByteArr, rect, percentRect)
    # store into the cache since its not there already
    img_cache[imgPath] = result
    return result

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
#  async_mode='eventlet'
socket = SocketIO(app, cors_allowed_origins="*")

L_ROOMCODES = 4

# I think this is the default port for mongodb
client = MongoClient(os.environ['DB_PORT_27017_TCP_ADDR'], 27017)
db = client.tododb

SEDER_NAME = 'sederName'

def SederData(
        sederName, roomCode='', huntIds=None,
        creationTime=None, members=None):

    assert sederName
    roomCode = str(roomCode)
    if roomCode:
        assert len(roomCode) == L_ROOMCODES

    return {
        SEDER_NAME: sederName,
        'roomCode': roomCode,
        'huntIds': huntIds or [],
        'creationTime': creationTime or datetime.now(),
        # 'huntQueue': [],
        # a list of UIDs to the users table
        'members': members or list(),
        'unusedCities': CITIES,
        'usedCities': [],
    }

def HuntData(
        sederId, roomCode, isActive=False, participants=None,
        city=None, imageId=None, winners=None,
        creationTime=None, startTime=None, isFinished=False):
    
    return {
        'sederId': sederId,
        'roomCode': roomCode,
        'isActive': isActive,
        # a list of Unique Ids (nicknames stored in Seder)
        'participants': participants or [],
        'city': city or '',
        'imageId': imageId,
        'winners': winners or [],
        'creationTime': creationTime or datetime.now(),
        'startTime': startTime,
        'isFinished': isFinished,
    }

# MEMBERS idxs of components
M_NICKNAME = 'nickname'
M_SCORE = 'score'
M_AVATAR = 'avatar'

def User(nickname, score, avatar):
    return {
        M_NICKNAME: nickname,
        M_SCORE: score,
        M_AVATAR: avatar,
    }

def ImageData(imgOrBytes, rect):

    assert isinstance(imgOrBytes, PIL.Image.Image)
    imgByteArr = io.BytesIO()
    imgOrBytes.save(imgByteArr, format='PNG')
    imgByteArr = imgByteArr.getvalue()

    W, H = imgOrBytes.size
    x, y, w, h = rect
    percentRect = (x/W, y/H, w/W, h/H)
    return {
        'imgBytes': imgByteArr,
        'rect': rect,
        'percentRect': percentRect,
    }

def getRandomImageForHunt(city):
    
    city = city.lower().replace(" ", "_")
    folderPath = os.path.join('cities', city, 'img')
    txtPath = os.path.join(folderPath, 'matza_xy.txt')
    
    with open(txtPath, 'r') as file:
        lines = file.readlines()
        numHides = len(lines)
    hideImgIdx = random.randint(0, numHides-1)

    coords = lines[hideImgIdx].split(',')
    x = int(coords[0])
    y = int(coords[1])

    imgPath = os.path.join(folderPath, f'{city}_hidden{hideImgIdx}.jpg')
    img = PIL.Image.open(imgPath)

    w, h = getMatzahImage().size
    return img, (x,y,w,h)

def setupHunt(huntId, city=None):
    """Sets up the hunt by generating the image based
    on params and storing it in DB.

    If city and matzahXY are None, generates a random image
    Stores the result in the images DB
    Returns the UID in the images DB for convenience?
    """

    # by default generate a random hunt
    if not city:
        city = CITIES[random.randint(0,len(CITIES)-1)] if not DEBUG else 'Toronto'

    folderPath = os.path.join('cities', city.lower().replace(' ', '_'), 'img')
    txtPath = os.path.join(folderPath, 'matza_xy.txt')

    with open(txtPath, 'r') as fin:
        lines = fin.readlines()
    numImages = len(lines)
    hiddenImageIdx = random.randint(0, numImages-1)
    imageId = (city, hiddenImageIdx)

    db.hunts.update_one({'_id': huntId}, {'$set': {'city': city, 'imageId': imageId}})
    return imageId

if False and __name__ == '__main__' and DEBUG:
    names = ['jonas', 'david', 'daniel', 'allison']
    rooms = ['ADCD', 'DCBA', 'AAAA', 'BBBB']
    idxs = range(len(names))

    db.seders.delete_many({})
    db.hunts.delete_many({})
    db.users.delete_many({})

    userIds = []
    for i, name in enumerate(names):
        _uid = db.users.insert_one(User(name, 0, i))
        userIds.append(_uid)

    for i, name, _room in zip(idxs, names, rooms):
        _startTime = datetime.now() if i == 2 else None

        # create a seder
        _seder_result = db.seders.insert_one(SederData(
            sederName=f"{name}'s seder",
            roomCode=_room,
            huntIds=[],
            members=[],
            # members=userIds if i == 1 else None,
        ))
        # create the hunt
        seder_uid = _seder_result.inserted_id
        huntResult = db.hunts.insert_one(HuntData(
            sederId=seder_uid,
            roomCode=_room,
            isActive=True,
            city='toronto',
            startTime=_startTime,
        ))
        updated_fields = {'huntIds': [huntResult.inserted_id]}
        db.seders.update_one(
            filter={'_id': seder_uid},
            update={'$set': updated_fields},
        )

        setupHunt(huntResult.inserted_id)

        # print(name, _room, _seder_result.inserted_id, huntResult.inserted_id)


PROJECT_PATH = '/usr/src/app'

def parseIdArg(idArg):
    try:
        result = ObjectId(idArg)
    except:
        result = None
    return result

def getHuntById(huntId):
    if isinstance(huntId, str):
        huntId = parseIdArg(huntId)

    if not huntId or not isinstance(huntId, ObjectId):
        return None

    return db.hunts.find_one({'_id': huntId})

def badResponse(bad='Bad args'):
    error = f'Whoops! {bad}.'
    response = {'Error': error}
    # print(response)
    error_result = (response, status.HTTP_400_BAD_REQUEST)
    return error_result

def goodResponse(result):
    if not isinstance(result, dict):
        result = {'result': result}

    for k, v in result.items():
        if isinstance(v, ObjectId):
            result[k] = str(v)

    return (result, status.HTTP_200_OK)

class BEVENTS(Enum):
    USER_JOINED = 1
    USER_LEFT = 2


@socket.on('connect')
def on_connect():
    print('User connected')


@socket.on('new_user')
def on_new_user(data):
    clientId = request.sid
    username = data['username']
    room = data['room']
    sederId = data['seder_id']
    huntId = data['hunt_id']

    # print(f'User {username} just joined room {room}')

    join_room(room)
    emit('message', {'message': f'User {username} just joined room {room}'}, room=room)

    sederData = getSederDataByRoomCode(room)

    # Check that the seder exists
    if sederData is None:
        # TODO: Error handling
        return ({"ok": False}, status.HTTP_400_BAD_REQUEST)

    avatar = random.randint(0,9)
    user_uuid = db.users.insert_one(User(username, 0, avatar)).inserted_id
    str_uid = str(user_uuid)
    data.update({'uid': str_uid})

    # db.seders.update_one({"_id": sederId}, {"$push": {'members': str_uid}})
    db.hunts.update_one({"_id": huntId}, { "$push": {"participants": str_uid}})  

    player_list = generatePlayerList(huntId)
    if player_list is None:
        return ({"ok": False}, status.HTTP_400_BAD_REQUEST)

    emit('player_list', {'n': len(player_list), 'player_list': player_list}, room=room)
    return ({"ok": True}, status.HTTP_200_OK)

@socket.on('trigger_hunt_socket')
def on_trigger_hunt(data):
    if not 'huntId' in data:
        return badResponse('No huntId passed')

    huntId = ObjectId(data['huntId'])

    # 1. Get the hunt and update it
    huntStart = datetime.utcnow()
 # + timedelta(seconds=5)
    hunt = db.hunts.find_one_and_update(
        {'_id': huntId},
        {'$set': {'isActive': True, 'startTime': huntStart}},
        return_document=ReturnDocument.AFTER,
    )

    if hunt is None:
        response = {'ok': False, 'message': 'Hunt not found'}
        return (response, status.HTTP_400_BAD_REQUEST)

    roomCode = hunt['roomCode']
    emit('start_time_update', {'startTime': huntStart.isoformat() + '+00:00'}, room=roomCode)

    response = {'ok': True}
    return (response, status.HTTP_200_OK)

def createHuntInSeder(sederData):
    sederId = sederData['_id']
    roomCode = sederData['roomCode']

    # get the last hunt from DB if not given to us
    # if not currentHuntData and sederData['huntIds']:
    #     lastHuntId = sederData['huntIds'][-1]
    #     currentHuntData = db.hunts.find_one({"_id": lastHuntId})

    # create players from previous and queued
    # prevPlayers = []
    # if currentHuntData:
    #     prevPlayers = currentHuntData['participants']
    # participants = prevPlayers + list(queuedPlayers)
    participants = []

    # create the new hunt and add it to the seder
    insertData = HuntData(sederId=sederId, roomCode=roomCode, participants=participants)
    newHuntId = db.hunts.insert_one(insertData).inserted_id
    db.seders.update_one({'_id': sederId}, { "$push": {"huntIds": newHuntId}})

    return newHuntId


def updateCitiesInSeder(sederData, huntId):
    unusedCities = sederData['unusedCities']
    usedCities = sederData['usedCities']

    # Reset the lists if the cities have been exhausted
    if len(unusedCities) == 0:
        unusedCities = CITIES
        usedCities = []

    city = unusedCities.pop(random.randint(0,len(unusedCities)-1)) # Remove city from the unused list
    usedCities.append(city) # Add city to the used list
    db.seders.update_one(
        {'_id': sederData['_id']},
        {
            '$pull': {'unusedCities': city},
            '$push': {'usedCities': city},
        }
    )
    return city

@socket.on('trigger_win')
def trigger_win(data):

    if 'huntId' not in data or 'userId' not in data:
        return badResponse('Bad args.')

    huntId = ObjectId(data['huntId'])
    userId = ObjectId(data['userId'])

    hunt = db.hunts.find_one_and_update(
        {'_id': huntId},
        {
            '$set': {'isFinished': True}, 
            '$push': {'winners': str(userId)}
        },
        return_document=ReturnDocument.BEFORE,
    )

    sederId = hunt['sederId']

    # update the player only if they were the first to finish
    if not hunt['isFinished']:
        db.users.update_one(
            {'_id': userId},
            {'$inc': {M_SCORE: 1}}
        )
        sederData = db.seders.find_one({"_id": hunt['sederId']})
        # create a new hunt!
        # print('creating a new hunt in the seder')
        newHuntId = createHuntInSeder(sederData)
        city = updateCitiesInSeder(sederData, newHuntId)
        setupHunt(newHuntId, city)
    else:
        # print('finding latest hunt id a new hunt in the seder')
        newHunt = db.hunts.find({"sederId": sederId}).sort([("$natural",-1)]).limit(1)[0]
        newHuntId = newHunt['_id']

    # returned winners list is from BEFORE, so we manually add here userid
    winners_list = hunt['winners'] + [str(userId)]
    roomCode = hunt['roomCode']

    # fill out winners list (effectively a join)
    winner_list_ids = [ObjectId(x) for x in winners_list]

    winner_docs = db.users.find({
        '_id': { '$in': winner_list_ids }
    })

    def _foo(doc):
        return {
            '_id': str(doc['_id']),
            M_NICKNAME: str(doc[M_NICKNAME]),
            M_SCORE: doc[M_SCORE],
            M_AVATAR: doc[M_AVATAR],
        }

    winners = list(_foo(doc) for doc in winner_docs)
    # emit that the winners list is updated
    response = {
        'winnerList': winners,
        'newHuntId': str(newHuntId),
    }

    emit('winners_list_update', response, room=roomCode)
    return (response, status.HTTP_200_OK)


@socket.on('join_hunt')
def join_hunt(data):

    if 'huntId' not in data or 'userId' not in data:
        return badResponse('Bad args.')

    huntId = ObjectId(data['huntId'])
    userId = ObjectId(data['userId'])

    hunt = db.hunts.find_one_and_update(
        {'_id': huntId},
        {
            '$push': {'participants': str(userId)}
        },
        return_document=ReturnDocument.AFTER,
    )

    participants = generatePlayerList(huntId)

    response = {
        'n': len(participants),
        'player_list': participants,
        'ok': True,
    }

    roomCode = hunt['roomCode']
    emit('player_list', response, room=roomCode)
    return (response, status.HTTP_200_OK)



@socket.on('unloading')
def on_disconnect(data):

    if 'sederId' not in data or not data['sederId']:
        return

    sederId = ObjectId(data['sederId'])
    # cant trust the hunt id from the lookup since it is out of date
    hunt = db.hunts.find({"sederId": sederId}).sort([("$natural",-1)]).limit(1)[0]
    huntId = hunt['_id']
    room = hunt['roomCode']
    uid = ObjectId(data['userId'])
    # db.seders.update_one({'_id': ObjectId(sederId)}, {"$pull": {'members': str(uid)}})
    db.hunts.update_one({'_id': ObjectId(huntId)}, { "$pull": {"participants": str(uid)}})

    player_list = generatePlayerList(huntId)
    if player_list is None:
        emit('player_list', {'n': 0, 'player_list': []}, room=room)
        return

    emit('player_list', {'n': len(player_list), 'player_list': player_list}, room=room)
    return

# @socket.on('leave')
# def on_leave(data):
#     username = data['username']
#     room = data['room']
#     leave_room(room)
#     emit(username + ' has left the room.', room=room)

@app.route('/api/get_seder_details', methods=['GET'])
def getSederDetails():
    sederId = parseIdArg(request.args.get('sederId'))
    # userId is optional!
    userId = parseIdArg(request.args.get('userId'))

    if not sederId:
        return badResponse('Bad args.')
    sederData = db.seders.find_one({"_id": sederId})
    if not sederData:
        return badResponse('No seder with given id')

    currentHuntId = db.hunts.find({"sederId": sederId}).sort([("$natural",-1)]).limit(1)[0]
    huntData = getHuntById(currentHuntId)
    isHuntActive = huntData['isActive']

    response = {'currentHuntId': currentHuntId, 'isHuntActive': isHuntActive}

    if userId:
        participants = huntData['participants']
        response['isUserInHunt'] = userId in participants

    return goodResponse(response)

def generatePlayerList(huntId):
    hunt = getHuntById(huntId)
    if not hunt:
        return None

    # sederId = hunt['sederId']
    # if isinstance(sederId, str):
    #     sederId = ObjectId(sederId)

    players = hunt['participants']
    # sederData = db.seders.find_one({"_id": sederId})
    # members = sederData['members']

    # convert our data format into a dictionary
    def _foo(pid):
        # helper that just reformats the db result
        uuid = ObjectId(pid)
        l = db.users.find_one({'_id': uuid})
        return {
            'uuid': str(uuid),
            'name': l[M_NICKNAME],
            'score': l[M_SCORE],
            'avatar': l[M_AVATAR],
        }

    result = [_foo(pid) for pid in players]
    return result

@app.route('/api/get_player_list', methods=['GET'])
def getPlayerList():
    # get parameters and sanitize
    huntId = request.args.get('huntId')
    playerList = generatePlayerList(huntId)

    if playerList is None:
        return badResponse('Bad args')

    return goodResponse(playerList)

@app.route('/api/hunt_start_time', methods=['GET'])
def huntStartTime():
    # get parameters and sanitize
    huntId = request.args.get('huntId')
    hunt = getHuntById(huntId)
    startTime = hunt['startTime'] if hunt else None

    if not hunt:
        return badResponse('Bad args')
    if not startTime:
        return badResponse('Invalid Hunt, hunt has no city associated')

    return goodResponse(startTime.isoformat())

def getJsonPath(city):
    x = city.lower().replace(' ', '_')
    return os.path.join('cities', x, x + '.json')

@app.route('/api/get_hints', methods=['GET'])
def getHints():
    # get parameters and sanitize
    huntId = request.args.get('huntId')
    hunt = getHuntById(huntId)
    city = hunt['city'] if hunt else ''

    if not hunt:
        return badResponse('Bad args')

    if not city:
        return badResponse('Invalid Hunt, hunt has no city associated')

    # open the json
    fpath = getJsonPath(city)
    if os.path.exists(fpath) and os.path.isfile(fpath):
        with open(fpath) as f:
            data = json.load(f)
        hints = data['hardHints'] + data['mediumHints'] + data['easyHints']
        return goodResponse(hints)

    # return bad if no json found
    return badResponse('Invalid Resource, city JSON not found')

@app.route('/api/check_location', methods=['GET'])
def checkLocation():
    """User hits this endpoint when they click on a location.

    The result is whether the location is found or not
    Also any additional info needed for the follow up GET
    in the event that they are correct"""

    # get parameters and sanitize
    huntIdArg = request.args.get('huntId')
    locationName = request.args.get('locationName')
    hunt = getHuntById(huntIdArg)

    if not hunt or not locationName:
        return badResponse('Bad args')

    # if the hunt doesn't exist or hasn't started return a 400
    if not hunt['isActive']:
        return badResponse('Invalid hunt!')

    # check if they got the right one
    if hunt['city'].lower() == locationName.lower():
        # image_id = hunt['imageId']
        response = {
            'found': True,
            # 'image_id': image_id,
        }
    else:
        response = {
            'found': False,
            # 'image_id': -1,
        }

    return goodResponse(response)

@app.route('/api/get_image', methods=['GET'])
def getImage():

    huntIdArg = request.args.get('huntId')
    hunt = getHuntById(huntIdArg)
    # returnsRect = bool(request.args.get('getRect'))

    if not hunt:
        return badResponse('Invalid Hunt')

    if not hunt['imageId']:
        return badResponse('Hunt has no image associated')

    imageId = hunt['imageId']
    imgBytes, _, _ = get_img_cached(imageId)

    if not imgBytes:
        return badResponse('Could not find image in DB')

    return send_file(
        io.BytesIO(imgBytes),
        mimetype='image/jpg',
    )

@app.route('/api/get_bounding_box', methods=['GET'])
def getBoundingBox():

    huntIdArg = request.args.get('huntId')
    hunt = getHuntById(huntIdArg)
    # returnsRect = bool(request.args.get('getRect'))

    if not hunt:
        return badResponse('Invalid Hunt')

    if not hunt['imageId']:
        return badResponse('Hunt has no image associated')

    imageId = hunt['imageId']
    _, rect, percentRect = get_img_cached(imageId)

    if not rect or not percentRect:
        return badResponse('Could not find image in DB')

    return goodResponse({'boundingBox': percentRect, 'originalBox': rect})

def getSederDataByRoomCode(roomCode):
    # TODO: Get most recent seder with roomCode
    return db.seders.find_one({"roomCode": roomCode})

@app.route('/api/join_seder', methods=['POST'])
def joinSeder():

    # Get data from the HTTP request
    roomCode = request.args.get('roomCode')
    nickname = request.args.get('nickname')
    optUserId = request.args.get('userId', None)

    if nickname is None:
        response = {'ok': False, 'message': 'You need a nickname homie'}
        return (response, status.HTTP_400_BAD_REQUEST)

    # Grab the seder document that matches the roomcode
    sederData = getSederDataByRoomCode(roomCode)

    # Check that the seder exists
    if sederData is None:
        return badResponse('Seder not found!')
    
    # Mazel tov, it exists. Now get the unique mongo id (i.e. _id)
    sederId = sederData['_id']

    # Find a hunt in the database that corresponds to the seder that is being joined AND is the most recent.
    # @Jonas are you sure this works as expected? Sorting after the limit statement?
    # currentHunt = db.hunts.find({"sederId": sederId}).limit(1).sort([("$natural",-1)])[0]
    currentHunt = db.hunts.find({"sederId": sederId}).sort([("$natural",-1)]).limit(1)[0]
    # Get unique mongo _id of the hunt
    currentHuntId = currentHunt['_id']

    # generate a new user
    avatar = random.randint(0,9)

    if not optUserId:
        user_uuid = db.users.insert_one(User(nickname, 0, avatar)).inserted_id
    else:
        user_uuid = ObjectId(optUserId)

    # Check to see if the hunt has started
    # if currentHunt['isActive']:
    #     # If the hunt has started, user is not allowed to join. Add them to the hunt queue.
    #     sederUpdates = {"$push": {"huntQueue": user_uuid, 'members': user_uuid}}
    #     sederData = db.seders.find_one_and_update({"_id": sederId}, sederUpdates, return_document=ReturnDocument.AFTER)
    #     print(sederData)
    #     response = {
    #         'queued': True,
    #         'huntId': str(currentHuntId),
    #         'sederId': str(sederId),
    #         SEDER_NAME: sederData[SEDER_NAME],
    #         'userId': str(user_uuid)
    #     }
    #     # response = db.seders.find_one({"_id": sederId})

    # else:
    if True: #pylint:disable=using-constant-test
        # Hunt hasn't started yet, add them as a participant in the hunt
        # print(sederData['members'])
        str_uid = str(user_uuid)
        # db.seders.update_one({"_id": sederId}, {"$push": {'members': str_uid}})

        hunt = db.hunts.find_one_and_update(
            {'_id': currentHuntId},
            { "$push": {"participants": str_uid}},
            return_document=ReturnDocument.AFTER,
        )
        isActive = hunt['isActive']

        # db.hunts.find_update_one({"_id": currentHuntId}, )
        response = {
            'isActive': isActive,
            'huntId': str(currentHuntId),
            'sederId': str(sederId),
            SEDER_NAME: sederData[SEDER_NAME],
            'userId': str(user_uuid)
        }

    return (response, status.HTTP_200_OK)

@app.route('/api/trigger_hunt', methods=['PUT'])
def triggerHunt():
    """ 
    Owner of seder clicks start hunt

    Input: hunt_id
    Returns: 
    """

    # get parameters and sanitize
    huntIdArg = request.args.get('huntId')
    huntId = parseIdArg(huntIdArg)

    if not huntId:
        return badResponse('Bad Args')

    # 1. Get the hunt and update it
    huntStart = datetime.now() + timedelta(seconds=10)
    hunt = db.hunts.find_one_and_update(
        {'_id': huntId},
        {'$set': {'isActive': True, 'startTime': huntStart}},
        return_document=ReturnDocument.AFTER,
    )

    if hunt is None:
        response = {'ok': False, 'message': 'Hunt not found'}
        return (response, status.HTTP_400_BAD_REQUEST)

    roomCode = hunt['roomCode']
    emit('start_time_update', {'startTime': huntStart}, room=roomCode)

    response = {'ok:': True, 'participants': hunt['participants']}
    return (response, status.HTTP_200_OK)


@app.route('/api/create_seder', methods=['POST'])
def createSeder():
    sederName = request.args.get(SEDER_NAME)
    nickname = request.args.get("nickname")

    if( (sederName is None) or (nickname is None) ):
        response = {'Error': "Whoops! Bad args"}
        return (response, status.HTTP_400_BAD_REQUEST)

    # Create a user
    avatar = random.randint(0,9)
    userId = db.users.insert_one(User(nickname, 0, avatar)).inserted_id
    baseUsers = [str(userId)]

    # Create a seder
    roomCode = getRoomCode()
    insertSederData = SederData(sederName=sederName, roomCode=roomCode, members=baseUsers)
    insertionResult = db.seders.insert_one(insertSederData)
    sederId = insertionResult.inserted_id
    

    remainingCities = deepcopy(CITIES)
    city = remainingCities.pop(random.randint(0, len(remainingCities)-1))

    # Create a hunt and update seders to include the hunt
    insertHuntData = HuntData(sederId=sederId, roomCode=roomCode, participants=baseUsers, city=city)
    newHuntId = db.hunts.insert_one(insertHuntData).inserted_id

    # newHuntId = createHuntInSeder(insertionResult)
    setupHunt(newHuntId, city)
    db.seders.update_one({'_id': sederId}, {"$push": {"huntIds": str(newHuntId)} })
    
    response = {
        'sederId': sederId,
        SEDER_NAME: sederName,
        'roomCode': roomCode,
        'huntId': newHuntId,
        'userId': userId,
    }
    return goodResponse(response)

def getRoomCode(stringLength = 4):
    pf = ProfanityFilter()
    letters = string.ascii_uppercase
    roomCode =  ''.join(random.choice(letters) for i in range(stringLength))
    # need to check also whether the room code is already being used
    while pf.is_profane(roomCode) or db.seders.count_documents({'roomCode': roomCode}) > 0:
        roomCode =  ''.join(random.choice(letters) for i in range(stringLength))
    return roomCode

@app.route('/api/get_cities', methods=['GET'])
def getCities():
    # returns: list of tuples, each tuple contains (city name, lat, lon)
    cities = []
    for city in CITIES:
        fpath = getJsonPath(city)
        # print(fpath)
        if os.path.exists(fpath) and os.path.isfile(fpath):
            with open(fpath) as f:
                data = json.load(f)
            lat = data['latitude']
            lon = data['longitude']
            cityLatLon = (city, lat, lon)
            cities.append(cityLatLon)
        # else:
            # return bad if no json found
            # return badResponse('Invalid Resource, city JSON not found')
    return goodResponse(cities)

# @app.route('/get_hunts', methods=['GET'])
# def getHunts():
#     hunts = db.hunts.find({})
#     huntList = []
#     for hunt in hunts:
#         huntList.append(hunt)
#     return str(huntList)

# @app.route('/get_seders', methods=['GET'])
# def getSeders():
#     seders = db.seders.find({})
#     sederList = []
#     for seder in seders:
#         sederList.append(seder)
#     return str(sederList)

if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=False, threaded=True)
    socket.run(app, debug=False)
