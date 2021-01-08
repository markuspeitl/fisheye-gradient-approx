import json

class PythonMessenger:
    """Writing messages to stdout and reading messages from stdin and executing registered callbacks based on those messages"""

    def __init__(self,stdout,stdin):
        """Setting target/subject stdout, stdin streams

        :param stdout: writable python stream
        :param stdin: readable python stream
        """

        self.stdout = stdout
        self.stdin = stdin

        self.selfcallbackdict = {}

        self.inReading = True

    def sendMessage(self,message):
        """Write message to subject stdout

        :param message: (str) message to be written
        """
        self.stdout.write(message)
        self.stdout.flush()

    def registerMessageHandler(self,keyword,callback):
        """Register callback method in internal dict for use from input reader

        :param callback: (data)=>None with parameter containing data from stdin (spaces not allowed) 
        """
        self.selfcallbackdict[keyword] = callback

    def startInputReading(self):
        """Start loop which continuously reads new available bytes from stdin, and calls callback based on
        first message part (callback name) with message payload
        """
        buff = ''
        while self.inReading:
            self.stdout.flush()

            buff += self.stdin.read(1)
            #print(buff[:-1])
            if buff.endswith('\n'):

                message = "" + buff[:-1]
                messageParts = message.split(" ")
                #print(message)
                if(len(messageParts) > 1):
                    if(messageParts[0] in self.selfcallbackdict):
                        self.selfcallbackdict[messageParts[0]](messageParts[1])

                self.stdout.flush()

                buff = ''

    def stop(self):
        self.inReading = False

