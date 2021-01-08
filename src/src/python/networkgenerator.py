import random
import numpy as np
import math
import os
import re

class NetworkGenerator:
    """A Genrator for generating new random networks"""

    def genClusterNodes(self,numCluster,numPoints,windowSize=100,bounds=[0,900,0,900]):
        """Generates normally distributed clusters of nodes

        :param numCluster: (int) Amount of clusters centers to be generated/chosen
        :param numPoints: (int) Amount of node centers (nodes) to be generated
        :param windowSize: (int) Data range around cluster (radius) center in which cluster nodes are generated
        :param bounds: (int[4]) [startx,endx,starty,endy] bounds of target data region in which the clusters are to be generated

        :return: allpoints, allLabels np.array((numPoints,2)), (np.array((numPoints,1),dtype=int)) Genrated points positions as vector and 
        corresponding cluster ids as label vector
        """

        ranges = np.array([bounds[1] - bounds[0],bounds[3] - bounds[2]])
        starts = np.array([bounds[0],bounds[2]])
        
        partition = (0.1 + np.abs(np.random.rand(numCluster,1))) / numCluster
        factor = 1 / np.sum(partition)
        #Percent of nodes per partition
        partition = partition * factor

        #Create Random Cluster centers in defined value range
        clusterCenters = starts + np.random.rand(numCluster,2) * ranges

        allpoints = None
        allLabels = None

        cnt = 0
        for part, center in zip(partition,clusterCenters):
            pointsPerPartition = int(part * numPoints)

            sprayangle = 1

            #Random angles from origin for each point of partition
            angle = np.random.rand(pointsPerPartition,1)* sprayangle * 2 * math.pi
            #print(angle)

            #Length of displacement vectors based on windowSize
            length = np.random.normal(size=(pointsPerPartition, 1)) * (windowSize/2)
            #print(length)

            normPoints = np.zeros((pointsPerPartition,2))

            #Calculate displacement degree in each direction
            normPoints[:,0] = np.cos(angle)[:,0]
            normPoints[:,1] = np.sin(angle)[:,0]

            #Calculate point postitions
            points = normPoints * length + center

            labels = np.ones((pointsPerPartition)) * cnt

            if(allpoints is None):
                allpoints = points
                allLabels = labels
            else:
                allpoints = np.concatenate((allpoints, points), axis=0)
                allLabels = np.concatenate((allLabels, labels), axis=0)

            cnt += 1

        #print(allpoints)
        return allpoints, allLabels.astype(int)

    def generateNetwork(self,nodeCnt,edgeCnt,xStart,xEnd,yStart,yEnd,closerSamplingIterations=30,clusterCenters=4):
        """Generate Network with random nodes and connections with normal distribution node positions

        :param nodeCnt: (int) Amount of nodes to be generated
        :param edgeCnt: (int) Amount of edges to be generated
        :param xStart,xEnd,yStart,yEnd: (int) Bounds of the data space for generation
        :param closerSamplingIterations: (int) Amount of other (possibly closer)edgeconnections to consider when selecting edge
        :param clusterCenters: (int) Amount of clusters centers to be generated
        :param bounds: (int[4]) [startx,endx,starty,endy] bounds of target data region in which the clusters are to be generated

        :return: nework ({"nodes":[],"edges":[],"nodeclusters":[]}) lists of nodes, edgeconnection indices and nodecluster ids
        """
        network = {
            "nodes":[],
            "edges":[],
            "nodeclusters":[]
        }

        xRange = xEnd - xStart
        yRange = yEnd - yStart

        dataRect = {"x":xStart,"y":yStart,"w":xRange,"h":yRange}

        nodePositions, network["nodeclusters"] = self.genClusterNodes(clusterCenters,nodeCnt,windowSize=500,bounds=[xStart,xEnd,yStart,yEnd])
        network["nodeclusters"] = network["nodeclusters"].tolist()

        for pos in nodePositions:
            network["nodes"].append([int(pos[0]),int(pos[1])])

        nodeCnt = nodePositions.shape[0]

        edgesCnt = 0

        connectedNodesIndexes = np.ones(nodeCnt) * (-1)
        selEnds = np.zeros(closerSamplingIterations)
        endindex = 0
        numbers = nodeCnt - 1
        for i in range(0,nodeCnt):
            leftprob = i/numbers
            #rightprob = (numbers - i)/numbers
            #roll = abs(random.random()) * 0.9999999
            rolls = np.random.rand(closerSamplingIterations) * 0.9999999

            leftvalues = (np.abs(np.random.rand(closerSamplingIterations)) * (i-1)).astype(int)
            rightvalues = ((i+1) + np.abs(np.random.rand(closerSamplingIterations) * (numbers - i))).astype(int)
            selEnds = np.where(rolls < leftprob, leftvalues, rightvalues)

            powermat = np.power(nodePositions[selEnds] - nodePositions[i],2)
            #print(powermat)
            summat = np.sum(powermat,axis=1)
            #print(summat)
            lengths = np.sqrt(summat)
            #minIndex = np.argmin(lengths)
            minIndex = np.argsort(lengths)
            #print(minIndex)
            #print("REAL: " + str(np.argmin(lengths)))
            selectedIndex = selEnds[minIndex[0]]
            selMinIndex = 1
            while connectedNodesIndexes[selectedIndex] == i and selMinIndex < minIndex.shape[0]:
                #print("Selecting other")
                selectedIndex = selEnds[minIndex[selMinIndex]]
                selMinIndex += 1

            #VERY low likelyhood of happening if closerAmount = 10 (so multiedges allowed in rare cases)
            #if(selMinIndex == minIndex.shape[0]):
            #    print("Out of candidates")

            connectedNodesIndexes[selectedIndex] = i
            connectedNodesIndexes[i] = selectedIndex

            #print(selEnds)

            network["edges"].append([i,int(selectedIndex)])

        return network


    def readDatasetToNP(self,name):
        
        dirname = os.path.dirname(__file__)
        dirPath = "data"
        edgesPath  = os.path.join(dirname,dirPath,name + "_edges.txt")
        nodesPath  = os.path.join(dirname,dirPath,name + "_nodes.txt")

        edgesToRead = -1
        edgeList = []
        #edgesNp = np.array([])
        with open(edgesPath, 'r') as edgesFile:

            line = edgesFile.readline()
            edgecnt = 1
            while edgecnt <= edgesToRead or edgesToRead == -1 and line:

                splitLine = re.split(r'\t+| +', line)

                #np.append(edgesNp,[splitLine[0],splitLine[1]],axis=0)
                edgeList.append([int(splitLine[0]),int(splitLine[1])])

                line = edgesFile.readline()
                edgecnt += 1

        edgesNp = np.asarray(edgeList)
        #np.random.shuffle(edgesNp)
        #print(edgesNp)
        #edgesSlice = edgesNp[0:100]
        #print(edgesSlice)

        nodesToRead = -1
        nodesList = []
        #nodesNp = np.array([])
        with open(nodesPath, 'r') as nodesFile:

            line = nodesFile.readline()
            nodecnt = 1
            while nodecnt <= nodesToRead or nodesToRead == -1 and line:

                splitLine = re.split(r'\t+| +', line)

                if(splitLine and len(splitLine) > 3):
                    #np.append(nodesNp,[splitLine[0],splitLine[2],splitLine[3]])
                    nodesList.append([int(splitLine[0]),float(splitLine[2]),float(splitLine[3])])
                elif(splitLine and len(splitLine) > 2):
                    nodesList.append([int(splitLine[0]),float(splitLine[1]),float(splitLine[2])])
                else:
                    print("Fail parsing Line: ")
                    print(line)
                    print("LineCnt: " + str(nodecnt))

                line = nodesFile.readline()
                nodecnt += 1

        nodesNp = np.asarray(nodesList)
        #nodeSlice = nodesNp[0:100]
        #print(nodeSlice)
        return edgesNp, nodesNp

    def firstLoginAsNode(self,nodesNp):

        lastIndex = 0
        newNodesList = []
        for row in nodesNp:
            #print(row[0])
            if(int(row[0]) != lastIndex) and row[1] != 0.0 and row[2] != 0.0:
                #print("found row")
                #matchIndex += 1
                lastIndex = int(row[0])
                newNodesList.append(row)

        return np.asarray(newNodesList)

    def selectNetRecursive(self,startEdges,newEdges,origEdges,connsCnt,maxNodes):
        if(len(newEdges) >= maxNodes):
            return

        for edge in startEdges:
            newEdges.append(edge)
            if(len(newEdges) >= maxNodes):
                return

            selEdgeRows = origEdges[origEdges[:,0] == edge[0]]
            newStartEdges = selEdgeRows[0:connsCnt]
            self.selectNetRecursive(newStartEdges,newEdges,origEdges,connsCnt,maxNodes)
            #print(selEdgeRows)


    def extractSubnet(self,edgesNp,nodesNp):
        np.random.shuffle(edgesNp)

        startPointCnt = 4
        maxConnectionsPerNode = 4
        maxNodes = 40

        newEdges = []
        startEdges = edgesNp[0:startPointCnt]
        edgesNp = edgesNp[startPointCnt:]
        print(len(startEdges))
        self.selectNetRecursive(startEdges,newEdges,edgesNp,maxConnectionsPerNode,maxNodes)
        print(newEdges)
        print(len(newEdges))

    def extractSubnet2(self,edgesNp,nodesNp):
        np.random.shuffle(nodesNp)
        startNodes = nodesNp[0:5]

        newNodes = []
        newEdges = []
        #for i in range(0,3):
        for node in startNodes:
            newNodes.append(node.tolist())
            connections = edgesNp[edgesNp[:,0] == node[0]]
            for edge in connections:
                newEdges.append(edge.tolist())
                endNode = nodesNp[nodesNp[:,0] == edge[1]]
                newNodes.append(endNode.tolist())

        print("newNodes Length: " + str(len(newNodes)))
        print(newNodes)
        print("newEdges Length: " + str(len(newEdges)))
        print(newEdges)

    def createNewDataset(self,name,edgesNp,nodesNp):
        
        dirname = os.path.dirname(__file__)
        dirPath = "data"
        edgesPath  = os.path.join(dirname,dirPath,name + "_edges.txt")
        nodesPath  = os.path.join(dirname,dirPath,name + "_nodes.txt")

        #nodesNp = self.firstLoginAsNode(nodesNp)
        #print(nodesNp)
        self.extractSubnet2(edgesNp,nodesNp)

        with open(edgesPath, 'w') as edgesFile:
            for row in edgesNp:
                edgesFile.write(str(int(row[0])) + " " + str(int(row[1])) + "\n")

        with open(nodesPath, 'w') as nodesFile:
            for row in nodesNp:
                nodesFile.write(str(int(row[0])) + " " + str(row[1]) + " " + str(row[2]) + "\n")

    def readDataset(self):

        network = {
            "nodes":[],
            "edges":[]
        }
        edgesNp,nodesNP = self.readDatasetToNP("clean")
        self.createNewDataset("clean",edgesNp,nodesNP)
        #edgesNp,nodesNP = self.readDatasetToNP()
        #network["nodes"] = nodesNP.toList()
        #network["edges"] = edgesNp.toList()

        return network
