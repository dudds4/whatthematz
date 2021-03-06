import os
from datetime import datetime

from flask import Flask, redirect, url_for, request, render_template
from pymongo import MongoClient

DEBUG = True
app = Flask(__name__)

# I think this is the default port for mongodb
client = MongoClient(os.environ['DB_PORT_27017_TCP_ADDR'], 27017)
db = client.tododb

def SederData(
    name, isActive=False, participants=None, roomCode=None,
    city=None, matzahXY=None, creationTime=None):

    return {
        'name': name,
        'isActive': isActive,
        'participants': participants or [],
        'roomCode': roomCode or -1,
        'city': city or '',
        'matzahXY': matzahXY or (0,0),
        'creationTime': creationTime or datetime.now()
    }

if DEBUG:
    names = ['jonas', 'david', 'daniel', 'allison']
    rooms = [123, 321, 222, 666]
    for name, room in zip(names, rooms):
        db.seders.insert_one(SederData(
            name=f"{name}'s seder",
            isActive=False,
            participants=[n for n in names if n != name],
            roomCode=room,
            city='toronto',
            matzahXY=(10, 10),
        ))


PROJECT_PATH = '/usr/src/app'

@app.route('/')
def todo():

    _items = db.tododb.find()
    items = [item for item in _items]

    print('hitting here.')
    template_path = os.path.join(PROJECT_PATH, 'templates/todo.html')
    # template_path = 'templates/todo.html'
    print(template_path)

    try:
        with open(template_path, 'r') as fin:
            print('success')
            print(fin.readlines())
    except Exception as exc:
        print('failure', exc)

    return render_template('todo.html', items=items)


@app.route('/new', methods=['POST'])
def new():

    item_doc = {
        'name': request.form['name'],
        'description': request.form['description']
    }
    db.tododb.insert_one(item_doc)

    return redirect(url_for('todo'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=DEBUG)