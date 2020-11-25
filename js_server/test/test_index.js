const assert = require('assert');
const index_mod = require('../index');


class MockEmitter {
    constructor(room) {this.room=room;}
    emit(data, ...args) {
        console.log("Room: " + this.room + ":: " + str(data));
    }
}

class MockSocket {
    constructor() {}
    to(room) { return MockEmitter(room); }
}


describe('index.js tests', () => {
    it('should add a new user', () => {
        index_mod.on_new_user(MockSocket(), {
            'username': "test",
            'room': "test",
            'sederId': "test",
            'huntId': "test",
        });
    });
});

