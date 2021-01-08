import { NetworkDrawer } from "./network-drawer.js";
import { ViewPort } from "./viewport.js"
import { Point } from "./point.js";
import { Lens } from "./lens.js";
import { Network } from "./network.js";
import { NetworkGenerator } from "./network-generator.js";

//var devMode = true;
//if(devMode){
//}

window.onload = function(){
    console.log("Document loaded")
    var canvas = document.getElementById('canvas');
    var viewport = new ViewPort();
    var networkDrawer = new NetworkDrawer(canvas,viewport);
    var networkGenerator = new NetworkGenerator();
    //var generatedNetwork = networkGenerator.generateNetwork(1000,1500,0,900,0,900);
    //networkDrawer.drawNetwork(generatedNetwork);
    var lens = new Lens(new Point(0,0),400);

    // -------------- Setup Sliders
    var magFSlider = document.getElementById("magFactorSlider");
    var magElem = document.getElementById("magValue");
    magElem.innerHTML = magFSlider.value/10;
    var magValue = magFSlider.value/10;
    magFSlider.oninput = function() {
        magElem.innerHTML = this.value/10;
        Lens.m = this.value/10
        magValue = this.value/10
    }
    var radiusSlider = document.getElementById("radiusSlider");
    var radiusElem = document.getElementById("radiusValue");
    radiusElem.innerHTML = radiusSlider.value;
    var radiusValue = radiusSlider.value
    radiusSlider.oninput = function() {
        radiusElem.innerHTML = this.value;
        lens.setRadius(this.value)
        radiusValue = this.value
    }
    var mixSlider = document.getElementById("mixSlider");
    var mixValue = document.getElementById("mixValue");
    mixValue.innerHTML = mixSlider.value/100;
    mixSlider.oninput = function() {
        mixValue.innerHTML = this.value/100;
        Lens.origMixFactor = this.value/100
    }
    var nodeCntSlider = document.getElementById("nodeCntSlider");
    var nodeCntElem = document.getElementById("nodeCntValue");
    nodeCntElem.innerHTML = nodeCntSlider.value;
    var nodeCntValue = nodeCntSlider.value
    nodeCntSlider.oninput = function() {
        nodeCntElem.innerHTML = this.value;
        nodeCntValue = this.value
    }
    var centersCntSlider = document.getElementById("centersCntSlider");
    var centersCntElem = document.getElementById("centersCntValue");
    centersCntElem.innerHTML = centersCntSlider.value;
    var centersCntValue = centersCntSlider.value
    centersCntSlider.oninput = function() {
        centersCntElem.innerHTML = this.value;
        centersCntValue = this.value
    }

    // -------------- Setup Buttons
    var jsFisheye = true;
    var jsfisheyeButton = document.getElementById('jsfisheye');
    var pyfisheyeButton = document.getElementById('pyfisheye');
    var structurefisheyeButton = document.getElementById('structurefisheye');
    var genNetworkButton = document.getElementById('genNetworkButton');
    jsfisheyeButton.onclick = function(){
        pyFisheye = false;
        jsFisheye = true;
        structureFisheye = false
        console.log("jsfisheye mode enabled")
        pyfisheyeButton.className = ""
        jsfisheyeButton.className = "active"
        structurefisheyeButton.className = ""
    }
    var pyFisheye = false;
    pyfisheyeButton.onclick = function(){
        pyFisheye = true;
        jsFisheye = false;
        structureFisheye = false;
        pyfisheyeButton.className = "active"
        jsfisheyeButton.className = ""
        structurefisheyeButton.className = ""
        console.log("fisheye approx mode enabled")
    }
    var structureFisheye = false;
    structurefisheyeButton.onclick = function(){
        pyFisheye = false;
        jsFisheye = false;
        structureFisheye = true
        pyfisheyeButton.className = ""
        jsfisheyeButton.className = ""
        structurefisheyeButton.className = "active"
        console.log("structurefisheye mode enabled")
    }

    // -------------- Canvas Size Management

    function redraw(){
        //console.log("redrawing22")
        var parentBounds = canvas.parentElement.getBoundingClientRect();

        canvas.width  = parentBounds.width;
        canvas.height = parentBounds.height;
        //canvas.width  = canvas.parentElement.innerWidth;
        //canvas.height = canvas.parentElement.innerHeight;
        viewport.resizeScreenRect(canvas.width,canvas.height)
        networkDrawer.drawCachedNetwork();
    }

    window.onresize = function(){
        redraw();
    }

    // -------------- Local Canvas Event Handling
    
    var lastPoint = new Point(0,0);
    var dragging = false;
    var panning = false;
    canvas.addEventListener('mousemove', e => {

        
        if(panning){
            //console.log("mousemove");
            var shift = new Point(lastPoint.x-e.offsetX,lastPoint.y-e.offsetY);
            lastPoint = new Point(e.offsetX,e.offsetY);
            viewport.moveScreen(shift);
            redraw();
        }
        else if(jsFisheye){
            var currentScreenPoint = new Point(e.offsetX,e.offsetY);
            var dataPointerPos = viewport.screenPointToDataPoint(currentScreenPoint);
            lens.setCenter(dataPointerPos);
        }
        redraw();
    });
    canvas.addEventListener('mousedown', e => {
        //console.log("mousedown");
        lastPoint = new Point(e.offsetX,e.offsetY);

        if (e && (e.which == 3 || e.button == 2 )) {
            panning = true;
        }
        if (e && (e.which == 2 || e.button == 4 )) {
            panning = true;
        }

        if(!panning && jsFisheye){
            //dragging = true;
            var dataPointerPos = viewport.screenPointToDataPoint(lastPoint);
            lens.setCenter(dataPointerPos);
            //lens.setCenter(new Point(500,500));
            viewport.applyLens(lens);
            redraw();
        }
    });
    
    canvas.addEventListener('mouseup', e => {
        //console.log("mouseup");
        //x = e.offsetX;
        //y = e.offsetY;
        panning = false;
        if(jsFisheye){
            viewport.removeLens(lens);
            redraw();
        }
    });
    canvas.addEventListener('contextmenu', e => {
        e.preventDefault();
    });

    // -------------- Sending Events to Python Server

    const socket = io('http://localhost:3000/');
    socket.on('connect',function(){
        console.log("Connected to server socket");

        var network = null;

        socket.on('create',(data)=>{
            console.log("Create: data received from server: ")// + data)
            //console.log(data);
            network = networkGenerator.generateNetworkFromString(data);
            networkDrawer.drawNetwork(network);
            redraw();
        });
        socket.on('fupdate',(data)=>{
            console.log("FUpdate: data received from server: ")// + data)
            var newNetwork = networkGenerator.generateNetworkFromString(data);
            networkDrawer.animateToNetwork(newNetwork,1000)
            //networkDrawer.drawNetwork(network);
            //redraw();
        });
        socket.on('update',(data)=>{
            console.log("Update: data received from server ")// + data)
            //console.log(data);
            var dataJSON = JSON.parse(data);
            for(var i = 0; i < dataJSON["indices"].length; i++){
                var index = dataJSON["indices"][i]
                var newPos = dataJSON["nodes"][i]
                //console.log("Index: " + index)
                //console.log("Oldpos: " + JSON.stringify(network.nodes[index].center))
                //console.log("NewPos: " + newPos)
                network.nodes[index].center.x = newPos[0]
                network.nodes[index].center.y = newPos[1]
            }
            //networkDrawer.drawNetwork(network);
            redraw();
        });

        var panblock = false
        canvas.addEventListener('mousedown', e => {
            if(!jsFisheye){
                if (e && (e.which == 3 || e.button == 2 ) || e && (e.which == 2 || e.button == 4 )) {
                    panblock = true;
                }
                else{
                    var currentScreenPoint = new Point(e.offsetX,e.offsetY);
                    var dataPointerPos = viewport.screenPointToDataPoint(currentScreenPoint);
                    //socket.emit('message',dataPointerPos.x + "," + dataPointerPos.y + "\n")
                    if(pyFisheye){
                        socket.emit('fishdown',dataPointerPos.x + "," + dataPointerPos.y + "," + radiusValue + "," + magValue + "\n")
                    }
                    else if(structureFisheye){
                        socket.emit('strucdown',dataPointerPos.x + "," + dataPointerPos.y + "," + radiusValue + "," + magValue + "\n")
                    }
                }
            }
        });
        canvas.addEventListener('mouseup', e => {
            if(!jsFisheye){
                var currentScreenPoint = new Point(e.offsetX,e.offsetY);
                var dataPointerPos = viewport.screenPointToDataPoint(currentScreenPoint);
                //socket.emit('message',dataPointerPos.x + "," + dataPointerPos.y + "\n")
                console.log("Send up Event")
                socket.emit('up',dataPointerPos.x + "," + dataPointerPos.y + "\n")
            }
        });

        genNetworkButton.onclick = function(){
            var genRequest = nodeCntValue + "," + centersCntValue + "\n"
            console.log('generate ' + genRequest)
            socket.emit('generate',genRequest)
        };

        /*canvas.addEventListener('mousemove', e => {
            var currentScreenPoint = new Point(e.offsetX,e.offsetY);
            var dataPointerPos = viewport.screenPointToDataPoint(currentScreenPoint);
            //socket.emit('message',dataPointerPos.x + "," + dataPointerPos.y + "\n")
            socket.emit('move',dataPointerPos.x + "," + dataPointerPos.y + "\n")
        });*/
    });
    socket.on('disconnect', function(){
        window.location.reload(false); 
    });

}