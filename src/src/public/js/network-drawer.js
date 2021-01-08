
//import { Node } from "node.js";
//import { Edge } from "edge.js";
import { Point } from "./point.js";
import { Network } from "./network.js";
import { ViewPort } from "./viewport.js";

//Class managing and executing network draw calls (Draws edges as lines and nodes as circles)
//Draws to HTML5 canvas
export class NetworkDrawer{

	constructor(canvas,viewport){
		this.network = new Network();
		this.canvas = canvas;
		this.context = canvas.getContext('2d');
		this.viewport = viewport;

		//Default Parameters for drawing
		this.defaultNodeSize = 8
		this.defaultNodeBorder = 2
		this.defaultEdgeThickness = 1
		this.defaultEdgeColor = "black"
		this.animationrefreshrate = 30

		//Default NodeColors for different clusters
		this.nodeClusterFillColors = [
			"lightblue",
			"red",
			"lightgreen",
			"orange",
			"lightgray",
			"lightviolet",
			"cyan"
		]
		this.nodeClusterStrokeColors = [
			"blue",
			"darkred",
			"green",
			"darkorange",
			"gray",
			"violet",
			"blue"
		]
		for(var i = 0; i < 20; i++){
			var rgb1 = (Math.floor(Math.abs(Math.random())*255)).toString(16) + (Math.floor(Math.abs(Math.random())*255)).toString(16) + (Math.floor(Math.abs(Math.random())*255)).toString(16)
			var rgb2 =  (Math.floor(Math.abs(Math.random())*180)).toString(16) + (Math.floor(Math.abs(Math.random())*180)).toString(16) + (Math.floor(Math.abs(Math.random())*180)).toString(16)
			this.nodeClusterFillColors.push(rgb1)
			this.nodeClusterFillColors.push(rgb2)
		}
	}

	//Redraw Stored Network
	drawCachedNetwork(){
		this.drawNetwork(this.network);
	}

	//Draw Network data to canvas using Viewport data to screen distortion - and store drawn network
	drawNetwork(network){

		this.context.clearRect(0, 0, this.canvas.width, this.canvas.height);

		this.network = network;
		var startAnchor = new Point(0,0);
		var endAnchor = new Point(0,0);

		//Draw edges as lines to canvas
		this.context.strokeStyle = this.defaultEdgeColor;
		this.context.lineWidth = this.defaultEdgeThickness;
		this.network.edges.forEach((edge) => {
			startAnchor = edge.getStartAnchor();
			endAnchor = edge.getEndAnchor();

			var startPix = this.viewport.dataPointToScreenPoint(startAnchor);
			var endPix = this.viewport.dataPointToScreenPoint(endAnchor);
			this.context.beginPath();
			this.context.moveTo(startPix.x, startPix.y);
			this.context.lineTo(endPix.x, endPix.y);
			this.context.stroke();
		});

		//Draw nodes as circles with borders to canvas
		var center = new Point(0,0);
		this.context.lineWidth = this.defaultNodeBorder;
		this.network.nodes.forEach((node) => {
			center = node.center;

			var centerPix = this.viewport.dataPointToScreenPoint(center);
			var bounds = this.viewport.scaleDataPointToScreenPoint(new Point(this.defaultNodeSize,this.defaultNodeSize),center);

			this.context.beginPath();
			if(node.index < this.nodeClusterFillColors.length){
				this.context.fillStyle = this.nodeClusterFillColors[node.index];
				this.context.strokeStyle = this.nodeClusterStrokeColors[node.index];
			}
			else{
				this.context.fillStyle = "lightblue";
				this.context.strokeStyle = "blue";
			}
			this.context.arc(centerPix.x, centerPix.y, bounds.x/2, 0, 2 * Math.PI, false);
			this.context.fill();
			
			this.context.stroke();
		});
	}

	//Animate network from last node positions to new node position
	animateToNetwork(newNetwork,timeMsec){
		var self = this;
		var nodeDiffs =  []

		for(var i = 0; i < self.network.nodes.length; i++){
			var x = newNetwork.nodes[i].center.x - self.network.nodes[i].center.x
			var y = newNetwork.nodes[i].center.y - self.network.nodes[i].center.y
			nodeDiffs.push([x,y])
		}
		
		var timeout = timeMsec/this.animationrefreshrate

		var timePassed = 0
		//var timeFactor = timePassed / timeMsec
		var timeoutFraction = timeout/timeMsec

		//Setup drawing in refreshrate intervals
		var animationInterval = setInterval(function(){
			console.log("Call Interval")
			for(var i = 0; i < self.network.nodes.length; i++){
				self.network.nodes[i].center.x += timeoutFraction * nodeDiffs[i][0]
				self.network.nodes[i].center.y += timeoutFraction * nodeDiffs[i][1]
			}
			self.drawCachedNetwork()

			timePassed += timeout
			if(timePassed >=timeMsec){
				clearInterval(animationInterval)
			}

		},timeout)
		
		
	}
}

