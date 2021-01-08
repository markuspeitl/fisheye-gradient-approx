import numpy as np

class NetworkOptimizer:
    """ Optimizes network positions using custom gradient descent"""
    def __init__(self):
        """Sets default variable settings"""
        self.gradFactor = 2.0
        self.velocityFactor = 1.4
        self.magnificationFactor = 4.0
        self.optimizeToFisheye = False
        self.startAtFisheye = False
        self.structuralConstraintsEnabled = True
        self.overlapPreventionEnabled = True
        self.crossingMaximEnabled = False

        self.useOriginalAsLossRef = False
        self.structuralweight = 1.0
        self.readabilityweight = 3.0
        self.lossThreshold = 1
        self.network = None

    def initOptimization(self,network,focalPoint,radius):
        """Initializes optimization variables and initial gradient states, initial node positions and initial edge connections
        like: Gradient momentum, Terms to be minimized at node level, Edge connection Positions of original layout, 
        Edge connection Positions before and after performing an optimization step, Edge connection Positions of the fisheye target layout
        
        :param network: {"nodes"=[],"edges"=[]} Network to be optimized/approximated
        :param focalPoint: [int,int] focal point of target fisheye distortion
        :param radius: (int) radius of fisheye distortion boundary
        """

        self.radius = radius
        self.focalPoint = focalPoint

        self.fisheyePositions = self.calcFisheyePositions(network["nodes"],self.focalPoint,self.radius)
        #print(self.fisheyePositions)

        self.nodes = np.asarray(network["nodes"])
        self.edgeConns = np.asarray(network["edges"])

        self.edgesCnt = self.edgeConns.shape[0]
        self.nodeCnt = self.nodes.shape[0]

        # -------- Variable Initializations
        self.grad = (np.random.randint(0,2,size=(self.nodeCnt,2)) * 2) - 1
        #gradient direcations and initial values
        self.grad = self.grad * self.gradFactor
        #Gradient momentum
        self.gradvelocity = np.ones((self.nodeCnt,2))

        #Terms to be minimized at node level
        self.nodeLoss = np.zeros((self.nodeCnt,2))

        #Edge connection Positions of original layout
        self.origLConnPositions = np.zeros((self.edgesCnt,2))
        self.origRConnPositions = np.zeros((self.edgesCnt,2))

        #Edge connection Positions before and after performing an optimization step
        self.lastConnPositions = [np.zeros((self.edgesCnt,2)),np.zeros((self.edgesCnt,2))]
        self.lastNodePositions = np.zeros((self.nodeCnt,2))
        self.newNodePositions = np.zeros((self.nodeCnt,2))

        #Edge connection Positions of the fisheye target layout
        self.lFisheyeConnPositions = np.zeros((self.edgesCnt,2))
        self.rFisheyeConnPositions = np.zeros((self.edgesCnt,2))
        # -----------------------------------------------

        # -------- Setting initial Values
        cnt = 0
        for edge in self.edgeConns:
            startNodeId = int(edge[0])
            startNode = self.nodes[startNodeId]
            self.origLConnPositions[cnt,:] = startNode
            self.lFisheyeConnPositions[cnt,:] = self.fisheyePositions[startNodeId]
            cnt += 1

        cnt = 0
        for edge in self.edgeConns:
            endNodeId = int(edge[1])
            endNode = self.nodes[endNodeId]
            self.origRConnPositions[cnt,:] = endNode
            self.rFisheyeConnPositions[cnt,:] = self.fisheyePositions[endNodeId]
            cnt += 1

        self.network = network

        self.origOrientations,_ = self.calcOrientations(self.origLConnPositions,self.origRConnPositions)

        self.lastConnPositions[0] = self.origLConnPositions
        self.lastConnPositions[1] = self.origRConnPositions
        self.lastNodePositions = self.nodes
        
        self.fisheyeOrientations, self.fisheyeLengths = self.calcOrientations(self.lFisheyeConnPositions,self.rFisheyeConnPositions)
        if(self.startAtFisheye):
            self.lastConnPositions[0] = self.lFisheyeConnPositions
            self.lastConnPositions[1] = self.rFisheyeConnPositions
            self.lastNodePositions = self.fisheyePositions

        # -----------------------------------------------

    def calculateEdgeCrossLoss(self,stepLConnVec,stepRConnVec):
        """Detects edge crossings in focal area and increases node loss where there is a low angle between crossings.
        (edge1 counter-clockwise rotation, edge2 clockwise rotation)
        
        :param stepLConnVec: np.array((nodes,2)) Left hand side edgeconnection positions of step
        :param stepRConnVec: np.array((nodes,2)) Right hand side edgeconnection positions of step
        :return: edge losses at each crossing, indices to find edges in global context
        """

        #To Filter out connected edges
        minStartDistance = 0.05
        minEndDistance = 0.05
        
        directions = self.focalConnPositions[1] - self.focalConnPositions[0]

        start2 = self.focalConnPositions[0]
        dir2 = directions

        #self.crossingsTable = np.zeros((directions.shape[0],directions.shape[0],2))
        self.crossingsLookup = np.zeros((directions.shape[0],directions.shape[0]),dtype=bool)

        inRangeStart = 0.0 + minStartDistance
        inRangeEnd = 1.0 - minStartDistance

        #iterations = 3
        iterations = directions.shape[0]
        for i in range(0,iterations):

            start1 = self.focalConnPositions[0][i]
            dir1 = directions[i]

            dir12cross = np.cross(dir1,dir2)

            start12cross = np.cross((start1 - start2),dir1)

            np.seterr(divide='ignore', invalid='ignore')
            u = dir12cross/start12cross
            u = np.nan_to_num(u,-1000)
            #print(u)

            incondition= (u >= inRangeStart) & (u <= inRangeEnd)
            self.crossingsLookup[i,:] = incondition

        crossingsListIndices = np.argwhere(self.crossingsLookup)

        globalEdgePairIndices = self.focalConnIndices[crossingsListIndices]
        leftEdges = globalEdgePairIndices[:,0]
        rightEdges = globalEdgePairIndices[:,1]

        alpha = np.pi/2
        angle = (np.pi - alpha)/2
        #rotationMat = np.array([[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]])
        rotationMat = np.array([[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]])
        counterRotMat = np.array([[np.cos(-angle),-np.sin(-angle)],[np.sin(-angle),np.cos(-angle)]])

        leftCrossLConnPositions = stepLConnVec[leftEdges[:,0]]
        leftCrossRConnPositions = stepLConnVec[leftEdges[:,1]]
        leftCrossOrientations, leftCrossLengths = self.calcOrientations(leftCrossLConnPositions,leftCrossRConnPositions)
        #print(leftCrossOrientations)
        #print(np.sin(angle) * leftCrossOrientations[0,0] + np.cos(angle) * leftCrossOrientations[0,1])
        #print(np.cos(angle) * leftCrossOrientations[0,0] - np.sin(angle) * leftCrossOrientations[0,1])
        leftCrossOrientations = np.matmul(leftCrossOrientations,rotationMat)
        #print(leftCrossOrientations)

        rightCrossLConnPositions = stepLConnVec[rightEdges[:,0]]
        rightCrossRConnPositions = stepLConnVec[rightEdges[:,1]]
        rightCrossOrientations, rightCrossLengths = self.calcOrientations(rightCrossLConnPositions,rightCrossRConnPositions)
        rightCrossOrientations = np.matmul(rightCrossOrientations,counterRotMat)

        #print(leftCrossLConnPositions)
        #print(rightCrossLConnPositions)
        lconns = np.vstack((leftCrossLConnPositions,rightCrossLConnPositions))
        rconns = np.vstack((leftCrossRConnPositions,rightCrossRConnPositions))
        orientations = np.vstack((leftCrossOrientations,rightCrossOrientations))

        #print(leftCrossLengths)
        lengths = np.concatenate((leftCrossLengths,rightCrossLengths))

        globalindices = np.vstack((globalEdgePairIndices[:,0],globalEdgePairIndices[:,1]))
        #print(lconns.shape)
        #print(rconns.shape)
        #print(orientations.shape)
        #print(lengths.shape)
        return np.power(np.abs(lconns - rconns - orientations*lengths[:,None]),2), globalindices

    def calculateOverlapLoss(self,stepLConnVec,stepRConnVec):
        """Detects overlapping nodes in focal area and increases node loss if nodes are too close.
        Inserts virtual edge with minimum length to nudge nodes apart
        
        :param stepLConnVec: np.array((nodes,2)) Left hand side edgeconnection positions of step
        :param stepRConnVec: np.array((nodes,2)) Right hand side edgeconnection positions of step
        :return: edge losses at each node overlapping edge, indices to find edges in global context
        """
        xm, xn = np.meshgrid(self.focalNodePositions[:,0], self.focalNodePositions[:,0])
        ym, yn = np.meshgrid(self.focalNodePositions[:,1], self.focalNodePositions[:,1])
        distanceMatrix = np.sqrt(np.power(xm - xn,2) + np.power(ym - yn,2)) + np.identity(self.focalNodePositions.shape[0])*100000
        #print("distanceMatrix")
        #print(distanceMatrix)
        noderadius = 10
        mindistance = 10

        focalOverlappingIndices = np.argwhere(distanceMatrix < noderadius)
        globalOverlappingIndices = self.focalNodeIndices[focalOverlappingIndices]
        #print("overlappingIndices")
        #print(overlappingIndices)

        #Debugging overlapping selection
        #self.newNodePositions[globalOverlappingIndices[:,0]] = np.array([0,0])
        #self.newNodePositions[globalOverlappingIndices[:,1]] = np.array([0,0])
        
        readLConnPositions = stepLConnVec[globalOverlappingIndices[:,0]]
        readRConnPositions = stepLConnVec[globalOverlappingIndices[:,1]]

        readOrientations,_ = self.calcOrientations(readLConnPositions,readRConnPositions)

        #Nudges nodes to the other direction as long as they overlap
        length = noderadius + noderadius + mindistance

        overLappingEdgeLoss = np.power(np.abs(readLConnPositions - readRConnPositions - readOrientations*length),2)

        return overLappingEdgeLoss, globalOverlappingIndices

    def calculateStructuralLoss(self,stepLConnVec,stepRConnVec):
        """Incentivised the overall structure of the layout, by incentivising the edge orientations to follow the
        original layouts orientations, while letting the edge lengths follow the lengths of the 
        fisheye distortet layout
        
        :param stepLConnVec: np.array((nodes,2)) Left hand side edgeconnection positions of step
        :param stepRConnVec: np.array((nodes,2)) Right hand side edgeconnection positions of step
        :return: structural edge losses at each edge, indices to find edges in global context
        """
        orientations = self.origOrientations
        if(self.optimizeToFisheye):
            orientations = self.fisheyeOrientations

        return np.power(np.abs(stepLConnVec - stepRConnVec - orientations*self.fisheyeLengths[:,None]),2), self.edgeConns
    
    def calculateNodeLoss(self,stepLConnVec,stepRConnVec,rConnVecOriginal):
        """Calculates loss (or minimization term) for each edge and then summs the edges losses for the nodes
        to calculate the x, y loss at each node.
        
        :param stepLConnVec: np.array((nodes,2)) Left hand side edgeconnection positions of step
        :param stepRConnVec: np.array((nodes,2)) Right hand side edgeconnection positions of step
        :param rConnVecOriginal: np.array((nodes,2)) Right hand side edgeconnection positions of the original layout
        :return: x,y loss at each node for step
        """

        #For debugging focal area
        #self.extractFocalEdges(stepLConnVec,stepRConnVec)
        #self.newNodePositions[self.focalNodeIndices] = np.array([0,0])
        
        #Calculate Loss at each node
        
        constaintEdgesLossResults = []
        constaintEdgeConns = []

        if(self.structuralConstraintsEnabled):
            rconnvec = stepRConnVec
            if(self.useOriginalAsLossRef):
                rconnvec = rConnVecOriginal
            structureEdgeLoss, structureEdgeConns = self.calculateStructuralLoss(stepLConnVec,rconnvec)
            structureEdgeLoss *= self.structuralweight
            constaintEdgesLossResults.append(structureEdgeLoss)
            constaintEdgeConns.append(structureEdgeConns)

        if(self.overlapPreventionEnabled or self.crossingMaximEnabled):
            self.extractFocalEdges(stepLConnVec,stepRConnVec)

        if(self.overlapPreventionEnabled):
            readEdgeLoss, readEdgeConns = self.calculateOverlapLoss(stepLConnVec,stepRConnVec)
            readEdgeLoss *= self.readabilityweight
            constaintEdgesLossResults.append(readEdgeLoss)
            constaintEdgeConns.append(readEdgeConns)

        if(self.crossingMaximEnabled):
            crossEdgeLoss, crossEdgeConns = self.calculateEdgeCrossLoss(stepLConnVec,stepRConnVec)
            constaintEdgesLossResults.append(crossEdgeLoss)
            constaintEdgeConns.append(crossEdgeConns)

        #self.edgeLoss =  + self.readabilityweight * self.calculateReadAbilityLoss(stepLConnVec,stepRConnVec)

        nodeLoss = np.zeros((self.nodeCnt,2))
        #Partial Summation term
        for edgeLossRes, edgeConnsRes  in zip(constaintEdgesLossResults,constaintEdgeConns):

            for i in range(0,edgeLossRes.shape[0]):
                selEdge = int(edgeConnsRes[i][0])
                nodeLoss[selEdge] += edgeLossRes[i]

        return nodeLoss
    
    def step(self):
        """ Perform a gradient descent step: \n
        1) Move last node positions by gradient * velocity value \n
        2) Calculate node loss at the new positions \n
        3) Update Velocity and gradient direction based on if loss increased or decreased \n
        4) Set last positions to updated positions \n
        5) Repeat until optimized
        """

        self.newNodePositions = self.lastNodePositions + self.grad * self.gradvelocity
        #print("CURR Grad: ")
        #print(self.grad)
        #print("LASTPOS:")
        #print(self.lastNodePositions)
        #print("NEWPOS:")
        #print(self.newNodePositions)

        #lconnVec = []
        updatedConnPositions = self.getEdgeConnPositions(self.newNodePositions,self.edgeConns)
        #print(updatedConnPositions)

        #newLoss = self.calculateNodeLoss(updatedConnPositions[0],self.lastConnPositions[1],self.network["edges"])
        #newLoss = self.calculateNodeLoss(updatedConnPositions[0],updatedConnPositions[1],self.network["edges"])
        newLoss = self.calculateNodeLoss(updatedConnPositions[0],updatedConnPositions[1],self.origRConnPositions)

        #print("NEWLOSS")
        #print(newLoss)
        #print("TOTALLOSS: " + str(np.sum(newLoss)))

        #print("LossDIFF")
        #print(newLoss - self.nodeLoss)
        lossDiff = newLoss - self.nodeLoss

        self.gradvelocity[lossDiff <= 0] *= self.velocityFactor
        self.gradvelocity[lossDiff > 0] = 1.0

        self.gradvelocity[newLoss < 400] = 0.6
        self.gradvelocity[newLoss < 80] = 0.4
        self.gradvelocity[newLoss < 40] = 0.2
        self.gradvelocity[newLoss < self.lossThreshold] = 0


        switchGrad = ((newLoss < self.nodeLoss).astype(int) *2) - 1
        #print("switchGrad")
        #print(switchGrad)
        self.grad = self.grad * switchGrad#* 0.8
        #print("NewGrad:")
        #print(self.grad)

        self.nodeLoss = newLoss

        self.lastConnPositions[0] = updatedConnPositions[0]
        self.lastConnPositions[1] = updatedConnPositions[1]
        self.lastNodePositions = self.newNodePositions

        return self.newNodePositions.tolist()

        ##network["nodes"] = out_node_positions.tolist()

    def calcOrientations(self,startPositions,endPositions):
        """ Calculate the nomalized orientations between 2 Position Vectors"""
        lengths = self.calcLenghts(startPositions,endPositions)
        #return (rconnVec - lconnVec)/lengths
        dirVector =(startPositions - endPositions)
        return np.divide(dirVector,lengths[:,None]), lengths

    def calcLenghts(self,startPositions,endPositions):
        """ Calculate vector lengths between 2 position vectors"""
        powermat = np.power(startPositions - endPositions,2)
        summat = np.sum(powermat,axis=1)
        #print(summat)
        lengths = np.sqrt(summat)
        #print(lengths)
        return lengths

    def calcVectorLenghts(self,vector):
        """ Calculate vector lengths of a single position vector"""
        powermat = np.power(vector,2)
        #print(powermat)
        summat = np.sum(powermat,axis=1)
        #print(summat)
        lengths = np.sqrt(summat)
        #print(lengths)
        return lengths

    def getEdgeConnPositions(self,nodeVec,edgeConns):
        """Get a matrix where each index of a connection table was replaced by the corresponding position of the nodes table
        :param nodeVec: the vector of node positions to get the position values from
        :param edgeConns: rows of connected edge indices
        """
        connPositions = [np.zeros((edgeConns.shape[0],2)),np.zeros((edgeConns.shape[0],2))]
        cnt = 0
        for edge in edgeConns:
            startNodeId = int(edge[0])
            endNodeId = int(edge[1])
            connPositions[0][cnt,:] = nodeVec[startNodeId]
            connPositions[1][cnt,:] = nodeVec[endNodeId]
            cnt += 1

        return connPositions

    def calcFisheyePositions(self,nodes,focalPoint,radius):
        """Calculate the new node positions distorted by a fishey lens
        :param nodes: original positions of the nodes
        :param focalPoint: [x,y] focal Point of the fisheye lens (center)
        :param radius: radius of the fisheye lens/distortion
        """
        #self.fisheyePositions = np.zeros((nodeCnt,2))
        m = self.magnificationFactor

        nodePositions = np.asarray(nodes)
        orientations,_ = self.calcOrientations(nodePositions,focalPoint)
        boundaryPoints = focalPoint + orientations * radius
        # == radius ???
        boundaryDistances = self.calcLenghts(boundaryPoints, focalPoint)
        nodeDistances = self.calcLenghts(nodePositions, focalPoint)

        focalDistanceRatios = nodeDistances/boundaryDistances
        distortedRatios = ((m + 1) * focalDistanceRatios)/(m * focalDistanceRatios + 1)
        return focalPoint + (boundaryPoints - focalPoint) * distortedRatios[:,None]

    def extractFocalEdges(self,lConnPositions,rConnPositions):
        """Extract the nodes and edges inside the focal area of the fisheye lens
        
        :param lConnPositions: np.array((nodes,2)) Left hand side edgeconnection positions of step
        :param rConnPositions: np.array((nodes,2)) Right hand side edgeconnection positions of step
        """
        #Extract edges and nodes inside focal area
        nodesFocalDistances = self.calcLenghts(self.newNodePositions,self.focalPoint)
        nodeinsidecondition = nodesFocalDistances < self.radius
        self.focalNodeIndices = np.argwhere(nodeinsidecondition).flatten()

        self.focalNodePositions = self.newNodePositions[self.focalNodeIndices]
       
        edgeConnChecker = np.isin(self.edgeConns,self.focalNodeIndices)
        #and
        condition = np.all(edgeConnChecker, axis=1)

        self.focalConnPositions = np.array([lConnPositions[condition],rConnPositions[condition]])
        self.focalConnIndices = self.edgeConns[condition]


    