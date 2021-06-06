import re
import src.runOperations as op
import src.BadSmell as smll
import src.parallelInheritance as inheritance
import src.removeComments as rC

def findParentClassForRefusedBequest(key, lines):
    parentClassList= []
    for line in lines: 
        if ("class "+key) in line: 
            if "(" and ")" and ":" in line:
                temp = op.find_between(line, "(", ")")
                if "[" and "]" in temp:
                    parentClassList.append(temp.split("[")[0])
                    return parentClassList
                elif "," in temp:
                    for each in temp.split(","):
                        parentClassList.append(each)
                    return parentClassList
                elif "." in temp:
                    parentClassList.append(temp.split(".")[1])
                    return parentClassList
                else: 
                    parentClassList.append(temp)
                    return parentClassList
                          
    return parentClassList
    
def checkIfParentClassExistInProjectForRefusedBequest(key, lines):
    for line in lines: 
        if (re.search(r'class '+key+'(.+?)?:',line)):
            return True

    return False
        
    
def checkIfParentNamedAsDifferentlyForRefusedBequest(key,parentClassKey, lines):
    for line in lines: 
        if re.search(r"from (.+?) import (.+?) as "+key, line):
            temp =re.search(r"from (.+?) import (.+?) as "+key, line).group(2)
            parentClassKey[parentClassKey.index(key)]=temp
            return parentClassKey
    return parentClassKey
   
        
    
def getClassLinesForRefusedBequest(key, classes,lines):
    classLines=[]
    if key in classes.keys():
        value = classes[key]
        if 'start' and 'end' in value: 
            classLines=lines[int(value['start']):int(value['end'])]
    return classLines
    
def getClassAttributesForRefusedBequest(classLines):
    getClassAttributesDict={}
    smell=smll.BadSmell()
    if len(classLines)>0:
        if 'classMethodsWithSelf' not in getClassAttributesDict.keys():
            getClassAttributesDict['classMethodsWithSelf']=smell.checkClassMethodsWithSelf(classLines)
        else:
            getClassAttributesDict['classMethodsWithSelf']= getClassAttributesDict['classMethodsWithSelf']+smell.checkClassMethodsWithSelf(classLines)
           
        if 'classMethodsWithCls' not in getClassAttributesDict.keys():
            getClassAttributesDict['classMethodsWithCls'] = smell.checkClassMethodsWithCls(classLines)
        else: 
            getClassAttributesDict['classMethodsWithCls'] = getClassAttributesDict['classMethodsWithCls']+smell.checkClassMethodsWithCls(classLines)
                
        classAttributes = smell.getClassInstanceAttributesWithSelf(classLines)+smell.getClassInstanceAttributesWithCls(classLines)+smell.getClassAttributes(classLines)
        if 'classAttributes' not in getClassAttributesDict:
            getClassAttributesDict['classAttributes'] = list(set(classAttributes))
        else:
            getClassAttributesDict['classAttributes'].append(list(set(classAttributes)))
        
    return getClassAttributesDict
            
def getCalledParentMethodsForRefusedBequest(parentClassKey,parentClassMethods, childrenClassLines):
    calledParentMethodsList=[]
    for parentClassMethod in parentClassMethods:
        for line in childrenClassLines:
            if ("self."+parentClassMethod.lstrip().rstrip()+"(") in line:
                calledParentMethodsList.append(parentClassMethod) 
            if ("cls."+parentClassMethod.lstrip().rstrip()+"(") in line:
                calledParentMethodsList.append(parentClassMethod)
            if ('super().'+parentClassMethod.lstrip().rstrip()+"(") in line:
                calledParentMethodsList.append(parentClassMethod)
            if ((parentClassKey+"."+parentClassMethod.lstrip().rstrip()+"(") or  (parentClassKey+"()."+parentClassMethod.lstrip().rstrip()+"(")) in line:
                calledParentMethodsList.append(parentClassMethod)
    return calledParentMethodsList
    
def getUsedInheritanceMembersForRefusedBequest(childClassAttributes,parentClassAttributes):
    usedInheritanceMembersDict={}
    if childClassAttributes:
        keys =['classMethodsWithSelf','classMethodsWithCls','classAttributes'] 
        for key in keys:
            usedInheritanceMembersDict[key]=op.getCommonData(childClassAttributes[key], parentClassAttributes[key])
    return usedInheritanceMembersDict
        
         
def calculateUsedInheritanceMembersForRefusedBequest(calledParentMethodsList,usedInheritanceMembersDict):
    totalNumberOfUsedNumber0fInheritanceMembers = len(calledParentMethodsList)
    for key in usedInheritanceMembersDict.keys():
        totalNumberOfUsedNumber0fInheritanceMembers += len(usedInheritanceMembersDict[key])
    return totalNumberOfUsedNumber0fInheritanceMembers
    
    
    
def calculateTotalNumberOfInheritanceMembersForRefusedBequest(parentClassAttributes):
    totalNumberOfInheritanceMembers=0
    for key in parentClassAttributes.keys():
        totalNumberOfInheritanceMembers += len(parentClassAttributes[key])
    return totalNumberOfInheritanceMembers
    
    
def getCalledParentMethodsWithSelfAndClsForRefusedBequest(parentClassKey, parentClassAttributes, childClassLines):
    calledParentMethodsWithSelfKeyword = getCalledParentMethodsForRefusedBequest(parentClassKey, parentClassAttributes['classMethodsWithSelf'], childClassLines)
    calledParentMethodsWithClsKeyword = getCalledParentMethodsForRefusedBequest(parentClassKey[0], parentClassAttributes['classMethodsWithCls'], childClassLines)
    calledParentMethods = calledParentMethodsWithSelfKeyword + calledParentMethodsWithClsKeyword
    return calledParentMethods
    

    
def calculateAUIRForRefusedBequest(key, parentClassKey, childClassAttributes, parentClassAttributes, calledParentMethods, refusedBequestDict):
        
    totalNumberOfUsedInheritanceMembers=0
    totalNumberOfInheritanceMembers=0 
    if childClassAttributes and parentClassAttributes:
        usedInheritanceMembersDict = getUsedInheritanceMembersForRefusedBequest(childClassAttributes, parentClassAttributes)
        totalNumberOfUsedInheritanceMembers = calculateUsedInheritanceMembersForRefusedBequest(calledParentMethods, usedInheritanceMembersDict)
        totalNumberOfInheritanceMembers = calculateTotalNumberOfInheritanceMembersForRefusedBequest(parentClassAttributes)
    averageInheritanceUsageRatio = 0
    if totalNumberOfUsedInheritanceMembers:
        averageInheritanceUsageRatio = totalNumberOfUsedInheritanceMembers / totalNumberOfInheritanceMembers
    if parentClassKey != "":
        refusedBequestDict[key] = {"parentClassName":parentClassKey, "totalNumberOfUsedInheritanceMembers":totalNumberOfUsedInheritanceMembers, "totalNumberOfInheritanceMembers":totalNumberOfInheritanceMembers, "averageInheritanceUsageRatio":averageInheritanceUsageRatio}
    return refusedBequestDict
    
def calculateRefusedBequest(fileName):
    try:
        smell=smll.BadSmell()
        #with open(fileName, "r") as f:
        refusedBequestDict={}
        pihSmellListDict= inheritance.calculateParallelInheritanceHiearchySmell(fileName)
            
        with open(fileName,  encoding="utf-8", errors='ignore') as f:
                
            fileLines= f.read()
            lines = rC.remove_comments_and_docstrings(fileLines).split('\n')
                
           
            classes=smell.getClassLinesOfFile(lines)
                  
            if classes!=None and len(classes.items())>=1:
                    
                for key, _ in classes.items():
                            
                    childClassLines=[]
                    parentClassLines=[]
                    childClassAttributes={}
                    parentClassAttributes={}
                        
                    childClassLines = getClassLinesForRefusedBequest(key,classes, lines)
                    childClassAttributes = getClassAttributesForRefusedBequest(childClassLines)
                        
                         
                    parentClassKey = findParentClassForRefusedBequest(key, lines)
                        
                    if len(parentClassKey)==1 and parentClassKey[0]!='':
                            
                          
                        parentClassKey=checkIfParentNamedAsDifferentlyForRefusedBequest(parentClassKey[0], parentClassKey,lines)
                            
                        if checkIfParentClassExistInProjectForRefusedBequest(parentClassKey[0], lines):
                            parentClassLines = getClassLinesForRefusedBequest(parentClassKey[0], classes, lines)
                                                          
                            if parentClassLines:
                                parentClassAttributes = getClassAttributesForRefusedBequest(parentClassLines)
                                    
                                calledParentMethods = getCalledParentMethodsWithSelfAndClsForRefusedBequest(parentClassKey[0], parentClassAttributes, childClassLines)
                                
                            calculateAUIRForRefusedBequest(key, parentClassKey[0], childClassAttributes, parentClassAttributes, calledParentMethods, refusedBequestDict) 
                     
                       
                    elif len(parentClassKey)>1:
                        for i in range(len(parentClassKey)):
                            if parentClassKey[i]!='':
                                parentClassKey=checkIfParentNamedAsDifferentlyForRefusedBequest(parentClassKey[i], parentClassKey,lines)
                                
                            if checkIfParentClassExistInProjectForRefusedBequest(parentClassKey[i], lines):
                                parentClassLines = getClassLinesForRefusedBequest(parentClassKey[i], classes, lines)
                                if parentClassLines:
                                    parentClassAttributes = getClassAttributesForRefusedBequest(parentClassLines)
                                    calledParentMethods = getCalledParentMethodsWithSelfAndClsForRefusedBequest(parentClassKey[i], parentClassAttributes, childClassLines)
                                        
                            calculateAUIRForRefusedBequest(key, parentClassKey[i], childClassAttributes, parentClassAttributes, calledParentMethods, refusedBequestDict) 
                    
                                        
            f.close()
           
        avgUsedInheritanceMembers=0
        count=0
        for k in refusedBequestDict.keys():
            if refusedBequestDict[k]['parentClassName']!="":
                avgUsedInheritanceMembers +=refusedBequestDict[k]['averageInheritanceUsageRatio']
                count +=1
            
        avgUsedInheritanceMembers = avgUsedInheritanceMembers/count
            
        for key, _ in refusedBequestDict.items():
            averageInheritanceUsageRatio=refusedBequestDict[key]['averageInheritanceUsageRatio']
            refusedBequestDict[key]['dit']=pihSmellListDict[key]['dit']
            refusedBequestDict[key]['averageInheritanceUsageRatioOfTheProject']=avgUsedInheritanceMembers
            refusedBequestDict[key]['isRefusedBequest']=((averageInheritanceUsageRatio<=avgUsedInheritanceMembers and not(pihSmellListDict[key]['dit']<2)) and averageInheritanceUsageRatio<33)
      
        return refusedBequestDict
    except Exception as ex:
        print(ex)
        print("Exception occurred in largeClassSmell.calculateLargeClassSmell in "+fileName)
        