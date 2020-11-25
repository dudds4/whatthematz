var uuid = require('uuid');

function generateRandomInt(lower, upper) {
    /* lower: int, lower bound inclusive
     * upper: int, upper bound exclusive
     * */
    return Math.floor(Math.random() * (upper - lower) + lower);
}

function generatePlayerList(huntId, db) {
    // TODO: hook up to db
    return [{
            'uuid': "123",
            'name': "test nickname",
            'score': 0,
            'avatar': 0,
        }];
}

function on_new_user(socket, data) {
    var username = data['username'];
    var room = data['room'];
    var sederId = data['seder_id'];
    var huntId = data['hunt_id'];

    // add the user to the room. 
    // Emit a message to others in the room
    socket.join(room);

    // generate the user data
    var user_uuid = uuid.v4();
    var avatar_idx = generateRandomInt(0, 10);

    // TODO: insert user document to database
    var user_document_id = 0;

    // TODO: update hunt
    // db.hunts.update( huntId, push: {participants: user_document_id})

    // TODO: add interface for database
    var player_list = generatePlayerList(huntId, null)

    if(player_list == null) {
        return;
        // return ({"ok": False}, status.HTTP_400_BAD_REQUEST)
    }

    // Notify room of the new player
    socket.to(room).emit(
        "player_list", 
        {"player_list": player_list}
    );
}

exports.on_new_user = on_new_user
