'''
Created on May 4, 2021

@author: neda
'''

import src.pythonMethods as pyMethods
def calculateMessageChainSmell(fileName):
    try:
        messageChainDictForTheFile={}
        with open(fileName, "r") as fileToBeRead:
            lines= fileToBeRead.readlines()
            for line in lines: 
                if ")." in line or (") ." in line):
                    messageChain=checkForChain(line,0)
                    isMessageChain=False
                    if messageChain>=4:
                        isMessageChain=True
                    messageChainDictForTheFile[line.lstrip().rstrip()]={'messageChainCount':messageChain,'isMessageChain':isMessageChain}
        return messageChainDictForTheFile
    except Exception as ex:
        print(ex)
        print("Exception occurred in messageChainSmell.calculateMessageChainSmell in "+fileName)

def checkForChain(textToBeChecked, messageCount):
        
    pythonMethods=pyMethods.builtInFunctions+pyMethods.dictionaryMethods+pyMethods.fileMethods+pyMethods.listArrayMethods+pyMethods.setMethods+pyMethods.stringMethods+pyMethods.tupleMethods
    if ")." in textToBeChecked:
        patternIndex=textToBeChecked.find(").")
        restOfStr=textToBeChecked[patternIndex+2:]
        methodStartIndex=restOfStr.find("(")
        methodName=restOfStr[:methodStartIndex]
        if len(methodName)>0:
            if (methodName+"()" in pythonMethods):
                return messageCount
            else:
                return checkForChain(restOfStr,messageCount+1)
        else:
            return messageCount
        messageCount=len(methodName)
    else:
        return messageCount