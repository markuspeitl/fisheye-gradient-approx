import sys
import random
import numpy as np
from networkgenerator import NetworkGenerator
from pythonmessenger import PythonMessenger
from networkoptimizer import NetworkOptimizer
import json
import time


class PythonCommunicator:
    """Handling events sent to this process by writing to its stdin and sending data updates to stdout"""

    def __init__(self):
        """Generate Initial Nework and setup stdin stdout messaging"""

        self.running = True
        self.communicate = True
        self.debugging = False

        self.networkGenerator = NetworkGenerator()
        self.networkoptimizer = NetworkOptimizer()
        if(not self.debugging):
            self.createNewNetwork(500,500)
        else:
            self.createNewNetwork(30,100)

        #self.networkoptimizer = NetworkOptimizer(len(network["nodes"]),len(network["edges"]))

        if(self.debugging):
            #print("BEFORE: ")
            #print(self.network)
            self.networkoptimizer.initOptimization(self.network,[400,400],400)
            for x in range(0,1):
                self.network["nodes"] = self.networkoptimizer.step()
            #print("AFTER: ")
            #print(self.network)

        if self.communicate and not self.debugging:
            self.pythonmessenger = None
            self.setupMessageHandlers()


    def sendBackNetwork(self,updateType,positionsonly=False):
        """Serialize network and send to stdout
        
        :param updateType: (str) prefix to send data with, spaces not allowed in this name
        :param positionsonly: (bool) only send back network node positions (omit edges and clusterids data)
        """
        tempnetwork = self.network
        if(positionsonly):
            tempnetwork = {
                "nodes": tempnetwork["nodes"]
            }

        networkjson = json.dumps(tempnetwork)
        networkjson = networkjson.replace(" ","")
        networkjson = updateType + " " + networkjson
        self.pythonmessenger.sendMessage(networkjson)
        sys.stdout.flush()

    def createNewNetwork(self,nodeCnt,edgesCnt,clustersCnt=4):
        """Generate Network and initialize NetworkOptimizer with new network
        
        :param nodeCnt: (int) Amount of nodes to be generated
        :param edgesCnt: (int) Amount of edges to be generated
        :param clusterCenters: (int) Amount of clusters centers to be generated
        """

        self.network = self.networkGenerator.generateNetwork(nodeCnt,edgesCnt,0,900,0,900,closerSamplingIterations=30,clusterCenters=clustersCnt)
        self.originalNodesPos = self.network["nodes"]

    def setupMessageHandlers(self):
        """Setup callbacks for specific stdin string events ("fishdown","strucdown","up","generate")
        """

        self.pythonmessenger = PythonMessenger(sys.stdout,sys.stdin)

        self.sendBackNetwork("create")

        #Perform optimization to fisheye target
        def handleDown(data):
            pos = data.split(",")
            focusPoint = [float(pos[0]),float(pos[1])]

            self.networkoptimizer.initOptimization(self.network,focusPoint,int(pos[2]))
            self.networkoptimizer.magnificationFactor = float(pos[3])
            self.networkoptimizer.optimizeToFisheye = True

            for x in range(0,50):
                #if(x > 40):
                #    self.networkoptimizer.overlapPreventionEnabled = True

                self.network["nodes"] = self.networkoptimizer.step()

            self.sendBackNetwork("fupdate",positionsonly=True)

        #Perform optimization to structure aware fisheye layout
        def handleStrucDown(data):
            pos = data.split(",")
            focusPoint = [float(pos[0]),float(pos[1])]

            self.networkoptimizer.initOptimization(self.network,focusPoint,int(pos[2]))
            self.networkoptimizer.magnificationFactor = float(pos[3])
            self.networkoptimizer.optimizeToFisheye = False

            for x in range(0,100):
                self.network["nodes"] = self.networkoptimizer.step()

            self.sendBackNetwork("fupdate",positionsonly=True)

        #Reset to original layout
        def handleUp(data):
            self.network["nodes"] = self.originalNodesPos
            self.sendBackNetwork("fupdate",positionsonly=False)

        #Generate new Network
        def handleGenRequest(data):
            splitdata = pos = data.split(",")
            self.createNewNetwork(int(pos[0]),int(pos[0]),int(pos[1]))
            self.sendBackNetwork("create")

        self.pythonmessenger.registerMessageHandler("fishdown",handleDown)
        self.pythonmessenger.registerMessageHandler("strucdown",handleStrucDown)
        self.pythonmessenger.registerMessageHandler("up",handleUp)
        self.pythonmessenger.registerMessageHandler("generate",handleGenRequest)

        self.pythonmessenger.startInputReading()


pythonCommunicator = PythonCommunicator()
