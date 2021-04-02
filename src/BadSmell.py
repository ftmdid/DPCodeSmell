'''
Created on Mar 27, 2019

@author: Neda
'''

import re
import src.runOperations as op
import src.pythonMethods as pyMethods
import src.parallelInheritance as pih


class BadSmell(object):
    '''
    classdocs
    '''
    def __init__(self):
        '''
        Constructor
        '''

       
    def getClassLinesOfFile(self,source):
        '''
            Some part of it is referenced from: https://stackoverflow.com/questions/58142456/how-to-get-the-scope-of-a-class-in-terms-of-starting-line-and-end-line-in-python
        '''
        try:               
                totalLine=len(source)
                classes = {}
                current_class = None
                for lineno, line in enumerate(source, start=0):
                    if current_class and not line.startswith(' '):
                        if line != '\n':
                            classes[current_class]['end'] = lineno - 1
                            current_class = None
                    if line.lstrip().startswith('class ') and (":" in line):
                        if "(" and ")" in line:
                            current_class=line.split('class ')[1].lstrip().split('(')[0]
                            classes[current_class] = {'start': lineno}
                        else:
                            className=line.split('class ')[1].lstrip().split(':')[0]
                            if not ' ' in className:
                                current_class=className
                                classes[current_class] = {'start': lineno}
                        
                    
                if current_class:
                    classes[current_class]['end'] = totalLine
                    #classes[current_class]['end'] = -1
                return classes
    #             fle.close()
        except Exception as ex:
            print(ex)
            print("Exception occurred in BadSmell.getClassLinesOfFile method")
    
    def getMethodsLinesOfFile(self,fileName):
        try:
            with open(fileName,'r') as fle:
                source=fle.readlines()                
                totalLine=len(source)
                methods = {}
                current_method = None
                for lineno, line in enumerate(source, start=0):
                    if current_method and not line.startswith(' '):
                        if line != '\n':
                            methods[current_method]['end'] = lineno - 1
                            current_method = None
                    if re.match(r'def (.+?)( ?\()', line.lstrip()):
                        if 'self' not in line:
                            current_method=line.split('def')[1].lstrip().split('(')[0]
                            methods[current_method] = {'start': lineno}
            
                if current_method:
                    methods[current_method]['end'] = totalLine
                    #methods[current_method]['end'] = -1
                fle.close()
                return methods
        except Exception as ex:
            print(ex)
            print("Exception occurred in BadSmell.getMethodsLinesOfFile method")
               
    def checkClassMethods(self,classLines):
            try:
                methodsList=[]
                for each in classLines:
                    if re.match(r'def (.+?)( ?\()', each.lstrip()):
                        if 'self'  in each:
                            currentMethod=each.split('def')[1].lstrip().split('(')[0]
                            methodsList.append(currentMethod)
                
                return len(methodsList)
            except Exception as ex:
                print(ex)
                print("Exception occurred in BadSmell.checkClassMethods method") 
    
    def getClassAttribututes(self,classLines):
        try:
            classLines = op.strip_blanklines(classLines)
            nondoctring = op.strip_docstring(classLines)
            noncomment = op.strip_comments(nondoctring, '#')
            classLines=noncomment.split('\n')
            attributesList=[]
            for each in classLines:
                if each.lstrip().startswith('self.') and ('=' in each):
                    currentAttribute = re.search(r'self.(.+?)=', each).group(1)
                    attributesList.append(currentAttribute)
            return len(list(set(attributesList))) 
        except Exception as ex:
            print(ex)
            print("Exception occurred in getClassAttributes method")   
                    
    def getClassName(self,classLines):
        current_class=""
        for each in classLines:
            if each.lstrip().startswith('class'):
                current_class = re.search(r'class (.+?)(?:\(|:)', each).group(1)
        return current_class
      
    def checkForLargeClass(self,fileName):
        try:
            with open(fileName, "r") as f:
                classesList={}
                lines=f.readlines()
                classes=self.getClassLinesOfFile(lines)
                classLOC = 0
                classMethodCount= 0
                classAttr = 0
                
                if classes!=None and len(classes.items())>=1:
                    
                    for key, value in classes.items():  
                        if 'start' and 'end' in value:  
                            classLines=lines[int(value['start']):int(value['end'])]
                            if len(classLines)>0:
                                classLinesStr="\n".join(classLines)
                                classLOC=op.loc(classLinesStr)['net']
                                #classLOC=int(value['end'])-int(value['start'])
                                classMethodCount=self.checkClassMethods(classLines)
                                classAttr=self.getClassAttribututes(classLinesStr)
                                isLargeClass=False
                                if (classLOC>=200) or (classAttr+classMethodCount>40):
                                    isLargeClass=True
                                classesList[key]={'classLOC':classLOC,'classMethodCount':classMethodCount,'classAttributesCount':classAttr,'isLargeClass':isLargeClass }
                return classesList
                
            f.close()
        except Exception as ex:
            print(ex)
            print("Exception occurred in BadSmell.checkForLargeClass in "+fileName)
    
    def getFunctionDefinition(self,methodLines):

        methodDef=""
        for i in range(len(methodLines)):
            if methodLines[i]:
                if re.search(".+\) ?:", methodLines[i]):
                    methodLines[i]=methodLines[i].split(":")[0]+":"
                    methodDef +=methodLines[i]
                    return methodDef
                else:
                    methodDef +=methodLines[i]
                           
        return methodDef
          
    '''
            This method is method level smell and we check if number of parameters is greater 
            than or equal to 5, that is a sign of long parameter list smell. 
    '''        
    def getFunctionParametersCount(self,methodLines):
        if not (")" and ":" in methodLines[0]):
            methodDef= self.getFunctionDefinition(methodLines)
        else:
            methodDef=methodLines[0]  
            
        funcAttrCount = 0
        line=methodDef
        if ',' in line:
            attrbts = line.split(",")
            funcAttrCount = len(attrbts)
        else:
            funcAttr=line.split("(")[1].split("):")[0]
            if not funcAttr:
                funcAttrCount  
            else:
                funcAttrCount = 1
        return funcAttrCount
    
    def checkForLongParameterList(self,fileName):
        try:
            with open(fileName, "r") as fileToBeRead:
                lines= fileToBeRead.readlines()
                methodsParameterList={}
                methodParameterCount=0
                methodsLines=self.getMethodsLinesOfFile(fileName)
                if methodsLines!=None and len(methodsLines.items())>=1:
                    for key in methodsLines:  
                        value=methodsLines[key]
                        if 'start' and 'end' in value:  
                            if value['end']>value['start']:
                                methodLines=lines[int(value['start']):int(value['end'])]
                            if value['end']==value['start']:
                                methodLines=lines[int(value['start']):int(value['start'])+1]
                            methodLOC=op.get_line_count("".join(methodLines))
                            methodParameterCount=self.getFunctionParametersCount(methodLines)
                            isLongParameterList=False
                            if methodParameterCount>=5:
                                isLongParameterList=True
                            methodsParameterList[key]={'methodLoc':methodLOC,'methodParameterCount':methodParameterCount,'isLongParameterList':isLongParameterList}
                return methodsParameterList
            fileToBeRead.close()
        except Exception as ex:
            print(ex)
            print("Exception occurrred in BadSmell.checkLongParameter List in :"+fileName)
    
    def checkForParallelInheritanceHiearchy(self,fileInTheFolder, projectName):
        commitID=op.find_between(fileInTheFolder, "@", "@")
        pythonFile=pih.downloadProjectInASpecificCommit(projectName, commitID)
        pihSmellListDict=pih.calculateParallelInheritanceHiearchySmell(pythonFile)
        parallelInheritanceHiearchyList={}
        try:
            classList=[]
            with open(fileInTheFolder) as fileToRead:
                fileLines=fileToRead.readlines()
                for line in fileLines:
                    if line.lstrip().startswith('class ') and (":" in line):
                        if "(" and ")" in line:
                            if ":" in line:
                                classList.append(line.split('(')[0].split('class ')[1].rstrip().lstrip())
                        elif not ("(" and ")" in line):
                            if ":" in line:
                                classList.append(line.split(':')[0].split('class ')[1].rstrip().lstrip())
            fileToRead.close()
            if classList and len(classList)>=1:
                for className in classList:
                    for key, value in pihSmellListDict.items():
                            if key==className:
                                parallelInheritanceHiearchyList[className]= value
            return parallelInheritanceHiearchyList
        except Exception as ex:
            print(ex)
            print("Exception occurrred in BadSmell.checkForParallelInheritanceHiearchy List in :"+fileInTheFolder)
                
    def checkForMessageChain(self,fileName):
        try:
            messageChainDictForTheFile={}
            with open(fileName, "r") as fileToBeRead:
                lines= fileToBeRead.readlines()
                for line in lines: 
                    if ")." in line or (") ." in line):
                        messageChain=self.checkForChain(line,0)
                        isMessageChain=False
                        if messageChain>=4:
                            isMessageChain=True
                        messageChainDictForTheFile[line.lstrip().rstrip()]={'messageChainCount':messageChain,'isMessageChain':isMessageChain}
            return messageChainDictForTheFile
        except Exception as ex:
            print(ex)
            print("Exception occurred in checkForMessageChain of "+fileName)

    def checkForChain(self,textToBeChecked, messageCount):
        
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
                    return self.checkForChain(restOfStr,messageCount+1)
            else:
                return messageCount
            messageCount=len(methodName)
        else:
            return messageCount