import express from 'express';
import exphbs from 'express-handlebars';
import http from 'http';
import path from 'path';
import socketio from 'socket.io';
import { PyCaller } from './models/pycaller';

const app = express();
let server: http.Server = http.createServer(app);
const sockethandler: socketio.Server = socketio(server);

const port = 3000;

const pyCaller = new PyCaller();
//Path to the python script doing the data processing 
const pythonPath = path.join(__dirname, "/python/pythoncommunicator.py");

app.engine("handlebars", exphbs({defaultLayout: "main"}));
app.set("view engine", "handlebars");

app.use(express.static(path.join(__dirname, "/public")));

app.get("/", function(req, res) {
    res.render("content", {});
});

app.get("/home", function(req, res) {
    res.render("projects", {});
});

server.listen(port, function() {
    console.log("express-handlebars server listening on: " + port);
});

//Relay messages coming from javascript client to python process and vice versa
sockethandler.on("connection", (socket) => {
    console.log("client connected!");

    //Call callback and send back message to client, if new message from python process received
    const callback = (data: any) => {
        var splitData = data.split(" ");
        if(splitData && splitData.length > 1){
            //console.log("sending back: " + splitData[0] + " message")
            socket.emit(splitData[0], splitData[1]);
        }
        else{
            socket.emit("data", data);
        }
    };
    //Start python process and initialize input and ouput reading/processing
    pyCaller.init(pythonPath, callback)
    .then(() => {
        console.log("Script finished");
    })
    .catch((err) => {
        console.log("Error in python script: " + err);
    });
    //Socket Middleware to relay any message coming to this server socket from client to the python script process
    socket.use((socket,next) => {
        pyCaller.sendMessage(socket[0] + " " + socket[1]);
    })
});
