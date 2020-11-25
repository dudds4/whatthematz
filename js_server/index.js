
/* can potentially simplify to 
var io = require('socket.io')();

Since nginx should be serving HTML anyways?
 * */
var app = require('express')();
var http = require('http').createServer(app);
var io = require('socket.io')(http);
var src = require('src');

app.get('/', (req, res) => {
  res.sendFile(__dirname + '/index.html');
});


function disconnect_handler() {
    console.log("User disconnected.");
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
    socket.on("new_user", _to_handler(socket, src.on_new_user));

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


