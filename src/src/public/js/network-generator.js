import { Point } from "./point.js";
import { Rect } from "./rect.js";
import { Node } from "./node.js";
import { Edge } from "./edge.js";
import { Network } from "./network.js";

export class NetworkGenerator{
    
    constructor(){}

    //Parse a string containing network information and create a Network instance from it 
    generateNetworkFromString(networkRepr){
        var newNetwork = new Network();

        var network = JSON.parse(networkRepr);

        //Parse Node Data
        if(network["nodes"]){
            var nodesData = network["nodes"];
            for(var i = 0; i < nodesData.length; i++){
                var index = 0;
                if(network["nodeclusters"]){
                    index = network["nodeclusters"][i]
                }
                //Creating new Node
                newNetwork.nodes.push(new Node(index,nodesData[i][0],nodesData[i][1]));
            }
        }

        //Parse Edge Data
        if(network["edges"]){
            var edgesData = network["edges"];
            edgesData.forEach((edgeData)=>{
                //Creating new Edge between existing nodes
                newNetwork.edges.push(new Edge(newNetwork.nodes[edgeData[0]],newNetwork.nodes[edgeData[1]]));
            });
        }

        return newNetwork;
    }

    // -------- Network Generation in JavaScript - UNUSED
    //Generate random network
    generateNetwork(nodeCnt,edgeCnt,xStart,xEnd,yStart,yEnd,closerSamplingIterations=40){
        var newNetwork = new Network();

        var nodes = [];
        var edges = [];
        var xRange = xEnd - xStart;
        var yRange = yEnd - yStart;

        var dataRect = new Rect(xStart,yStart,xRange,yRange);

        //Create Nodes at random Positions
        for(var i = 0; i < nodeCnt; i++){
            var centerx = dataRect.x + Math.random() * dataRect.w;
            var centery = dataRect.y + Math.random() * dataRect.h;
            nodes.push(new Node(i,centerx,centery));
        }
        
        //Apply Cell Grid to Nodes and Remove some Nodes from low density cells
        nodes = this.filterNodesByCellDensity(20,20,3,0.3,nodes,dataRect);
        nodeCnt = nodes.length;

        //Generate edge pairs and optionally look randomly for closer Connections
        var closerSamplingIterations = 40;
        var connIndexPair = [];
        for(var i = 0; i < edgeCnt; i++){
            connIndexPair = this.randomSampleConnCandidatesIndexes(closerSamplingIterations,nodes)
            
            edges.push(new Edge(nodes[connIndexPair[0]],nodes[connIndexPair[1]]));
        }

        newNetwork.nodes = nodes;
        newNetwork.edges = edges;
        return newNetwork;
    }
    randomSampleConnCandidatesIndexes(samplingIterations,nodes){
        var edgeCandidates = [];
        var indexVector = this.getIndexVector(samplingIterations,nodes.length);
        //console.log(indexVector);
        var center1 = new Point(0,0);
        var center2 = new Point(0,0);
        var distance = 0;
        var indexPair = [];
        for(var x = 0; x < samplingIterations; x++){
            indexPair = indexVector[x];//this.getIndexPair(nodeCnt);
            center1 = nodes[indexPair[0]].center;
            center2 = nodes[indexPair[1]].center;
            distance = Math.sqrt(Math.pow(center1.x-center2.x,2)+Math.pow(center1.y-center2.y,2))
            edgeCandidates.push([distance,indexPair]);
        }
        edgeCandidates = edgeCandidates.sort((a,b)=>{ return a[0] - b[0] });

        var selectedPairIndexPair = edgeCandidates[0][1];
        return [selectedPairIndexPair[0],selectedPairIndexPair[1]];
    }
    //Helper Functions
    findFreeIndex(index,maxindex){
        if(index < maxindex){
            return index + 1;
        }
        else if(index > 0){
            return index - 1;
        }
        return -1;
    }
    getIndexPair(indexCnt){
        var index1 = Math.floor((Math.random() - 0.000001) * indexCnt);
        var index2 = Math.floor((Math.random() - 0.000001) * indexCnt);
        if(index1 === index2){
            index2 = this.findFreeIndex(index2,indexCnt-1);
        }
        return [index1,index2];
    }
    getIndexVector(elcnt,indexCnt,index1){
        //console.log("Call getIndexVector")
        var indexVector = [];
        if(elcnt === 0)
            return [];

        if(!index1){
            index1 = Math.floor((Math.random() - 0.000001) * indexCnt);
        }
        var index2 = Math.floor((Math.random() - 0.000001) * indexCnt);
        if(index1 === index2){
            index2 = this.findFreeIndex(index2,indexCnt-1);
        }
        indexVector.push([index1,index2]);
        return indexVector.concat(this.getIndexVector(elcnt-1,indexCnt,index1))
    }
    //Lucky nodes are saved from filtering (with a chance)
    filterNodesByCellDensity(xCells,yCells,minDensity,luckyNodeChance,nodes,dataRect){
        //Remove Nodes from low density cells
        //var xBins = 20;
        //var yBins = 20;
        var cellW = dataRect.w/xCells;
        var cellH = dataRect.h/yCells;
        var chessboard = new Array(xCells);
        for(var x = 0; x < xCells; x++){
            chessboard[x] = new Array(yCells);

            for(var y = 0; y < yCells; y++){
                chessboard[x][y] = [0,[]]
            }
        }
        for(var i = 0; i < nodes.length; i++){
            var center = nodes[i].center;
            var xCellIndex = Math.floor((center.x - dataRect.x)/cellW);
            var yCellIndex = Math.floor((center.y - dataRect.y)/cellH);
            chessboard[xCellIndex][yCellIndex][0]++;
            chessboard[xCellIndex][yCellIndex][1].push(nodes[i])
        }
        var newNodeList = [];
        //var luckyNodeChance = 0.2;
        for(var x = 0; x < xCells; x++){
            for(var y = 0; y < yCells; y++){
                if(chessboard[x][y][0] > minDensity){
                    chessboard[x][y][1].forEach((node)=>{
                        newNodeList.push(node);
                    })
                }
                else{
                    chessboard[x][y][1].forEach((node)=>{
                        if(Math.random() < luckyNodeChance){
                            newNodeList.push(node);
                        }
                    })
                }
            }
        }

        return newNodeList;
    }

    // !-------- Network Generation in JavaScript - UNUSED
}