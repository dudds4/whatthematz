
/* can potentially simplify to 
var io = require('socket.io')();

Since nginx should be serving HTML anyways?
 * */
var app = require('express')();
var http = require('http').createServer(app);
var io = require('socket.io')(http);
import { v4 as uuidv4 } from 'uuid';

app.get('/', (req, res) => {
  res.sendFile(__dirname + '/index.html');
});

function generateRandomInt(lower, upper) {
    /* lower: int, lower bound inclusive
     * upper: int, upper bound exclusive
     * */
    return Math.floor(Math.random() * (upper - lower) + lower);
}

function generatePlayerList(huntId, db) {
    // TODO: hook up to db
    return [{
            'uuid': str("123"),
            'name': "test nickname",
            'score': 0,
            'avatar': 0,
        }];
}

function disconnect_handler() {
    console.log("User disconnected.");
};

function on_new_user(socket, data) {
    var username = data['username'];
    var room = data['room'];
    var sederId = data['seder_id'];
    var huntId = data['hunt_id'];

    // add the user to the room. 
    // Emit a message to others in the room
    socket.join(room);

    // generate the user data
    user_uuid = uuidv4();
    avatar_idx = generateRandomInt(0, 10);

    // TODO: insert user document to database
    user_document_id = 0;

    // TODO: update hunt
    // db.hunts.update( huntId, push: {participants: user_document_id})

    // TODO: add interface for database
    player_list = generatePlayerList(huntId, null)
    if player_list == null:
        return ({"ok": False}, status.HTTP_400_BAD_REQUEST)

    // Notify room of the new player
    socket.to(room).emit(
        "player_list", 
        {"player_list": player_list}
    );
};

function _to_handler(socket, func) {
    /* Wraps the function, 
     * so it effectively is called with the socket as well.
     * */
    var handler = function(data) {
        return func(socket, data);
    };
    return handler
};


io.on('connection', (socket) => {
    console.log('User connected.');

    socket.on("disconnect", disconnect_handler);
    socket.on("new_user", _to_handler(socket, on_new_user));

    socket.on("chat", (msg) => {
        console.log("message received");
        console.log(msg);
        socket.broadcast.emit("chat", msg);

    });

    // io.emit("player_joined", {
    //     nickname: "My nickname",
    //     logo: 1,
    // });

});


http.listen(3000, () => {
  console.log('listening on *:3000');
});


