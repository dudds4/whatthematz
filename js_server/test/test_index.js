const assert = require('assert');
const src = require('../src');


class MockEmitter {
    constructor(room) {this.room=room;}
    emit(data, ...args) {
        console.log("Room: " + this.room + ":: " + String(data));
    }
}

class MockSocket {
    constructor() {}
    join(room) { console.log("Joined room: " + room); }
    to(room) { return new MockEmitter(room); }
}


describe('index.js tests', () => {
    it('should add a new user', () => {
        src.on_new_user( new MockSocket(), {
            'username': "test",
            'room': "test",
            'sederId': "test",
            'huntId': "test",
        });
    });
});

