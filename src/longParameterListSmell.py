'''
Created on May 4, 2021

@author: neda
'''

import src.runOperations as op
import src.BadSmell as smll


def calculateLongParameterListSmell(fileName):
    try:
        smell = smll.BadSmell()
        with open(fileName, "r") as fileToBeRead:
            lines= fileToBeRead.readlines()
            methodsParameterList={}
            methodParameterCount=0
            methodsLines=smell.getMethodsLinesOfFile(fileName)
            if methodsLines!=None and len(methodsLines.items())>=1:
                for key in methodsLines:  
                    value=methodsLines[key]
                    if 'start' and 'end' in value:  
                        if value['end']>value['start']:
                            methodLines=lines[int(value['start']):int(value['end'])]
                        if value['end']==value['start']:
                            methodLines=lines[int(value['start']):int(value['start'])+1]
                        methodLOC=op.get_line_count("".join(methodLines))
                        methodParameterCount=smell.getFunctionParametersCount(methodLines)
                        isLongParameterList=False
                        if methodParameterCount>=5:
                            isLongParameterList=True
                        methodsParameterList[key]={'methodLoc':methodLOC,'methodParameterCount':methodParameterCount,'isLongParameterList':isLongParameterList}
            return methodsParameterList
        fileToBeRead.close()
    except Exception as ex:
        print(ex)
        print("Exception occurrred in longParameterList.calculateLongParameterListSmell List in :"+fileName)
