import re
import src.runOperations as op
import src.BadSmell as smll
import src.smell.parallelInheritance as inheritance



def calculateRefusedBequestSmell(fileInTheFolder, projectName):
    
    try:
        smell = smll.BadSmell()
        commitID=op.find_between(fileInTheFolder, "@", "@")
        refusedBequestSmellDict={}
        pythonFile=inheritance.downloadProjectInASpecificCommit(projectName, commitID)
        refusedBequestSmellDict=calculateRefusedBequest(pythonFile)
        avgUsedInheritanceMembers=0
        count=0
        if refusedBequestSmellDict:
            for k in refusedBequestSmellDict.keys():
                if refusedBequestSmellDict[k] and 'parentClassName' in refusedBequestSmellDict[k].keys():
                    if refusedBequestSmellDict[k]['parentClassName']!="":
                        avgUsedInheritanceMembers +=refusedBequestSmellDict[k]['averageInheritanceUsageRatio']
                        count +=1
                        
            avgUsedInheritanceMembers = avgUsedInheritanceMembers/count
                    
            for key, _ in refusedBequestSmellDict.items():
                if  refusedBequestSmellDict[key]:
                    averageInheritanceUsageRatio=refusedBequestSmellDict[key]['averageInheritanceUsageRatio']
                    refusedBequestSmellDict[key]['averageInheritanceUsageRatioOfTheProject']=avgUsedInheritanceMembers
                    refusedBequestSmellDict[key]['isRefusedBequest']=((averageInheritanceUsageRatio<=avgUsedInheritanceMembers and not(refusedBequestSmellDict[key]['dit']<2)) and averageInheritanceUsageRatio<33)
              
    
            refusedBequestSmellList={}
    
            with open(fileInTheFolder, "r") as f:
                lines=f.readlines()
                classes=smell.getClassLinesOfFile(lines)
    
                if classes!=None and len(classes.items())>=1:
                    for k, _ in classes.items(): 
                        if refusedBequestSmellDict:
                            if k.lstrip().rstrip() in refusedBequestSmellDict.keys():
                                    refusedBequestSmellList[k]={'parentClassName':refusedBequestSmellDict[k]['parentClassName'], 
                                                                'dit':refusedBequestSmellDict[k]['dit'],
                                                                'totalNumberOfUsedInheritanceMembers':refusedBequestSmellDict[k]['totalNumberOfUsedInheritanceMembers'], 
                                                                'totalNumberOfInheritanceMembers':refusedBequestSmellDict[k]['totalNumberOfInheritanceMembers'], 
                                                                'averageInheritanceUsageRatio':refusedBequestSmellDict[k]['averageInheritanceUsageRatio'],
                                                                'averageInheritanceUsageRatioOfTheProject':refusedBequestSmellDict[k]['averageInheritanceUsageRatioOfTheProject'],
                                                                'isRefusedBequest':refusedBequestSmellDict[k]['isRefusedBequest']}      
                                    
            f.close()
            return refusedBequestSmellList
    except Exception as ex:
        print(ex)
        print("Exception occurrred in refusedBequestSmell.calculateRefusedBequestSmell in :"+fileInTheFolder+" of "+projectName +"with ")

def findParentClassForRefusedBequest(key, lines):
    try:
        parentClassList= []
        for line in lines: 
            if ("class "+key) in line: 
                if ("(" in line) and (")" in line) and (":" in line):
                    #temp =re.search(r'class '+key+'(.+?)?:',line).group(1)
                    temp = op.find_between(line, "(", ")")
                    if temp:
                        if "[" and "]" in temp:
                            temp =temp.split("[")[0]
                            if temp.isalnum():
                                parentClassList.append(temp)
                                return parentClassList
                        elif "," in temp:
                            for each in temp.split(","):
                                if each.isalnum():
                                    parentClassList.append(each)
                                    return parentClassList
                        elif "." in temp:
                            parentClassList.append(temp.rsplit(".",1)[1])
                            return parentClassList
                        elif "(" in temp:
                            parentClassList.append(temp.split("(")[0])
                        else: 
                            parentClassList.append(temp)
                            return parentClassList
                              
        return parentClassList
    except Exception as ex:
        print(ex)
        print("Exception occurred in refusedBequestSmell.findParentClassForRefusedBequest")
  
    
def checkIfParentClassExistInProjectForRefusedBequest(key, lines):
    try:
        for line in lines:
            if (re.search(r'class '+key+'(.+?)?:',line)):
                return True
        return False
    except Exception as ex:
        print(ex)
        print("Exception occurred in refusedBequestSmell.checkIfParentClassExistInProjectForRefusedBequest")
        
    
def checkIfParentNamedAsDifferentlyForRefusedBequest(key,parentClassKey, lines):
    try:
        parentClssKey=parentClassKey
        for line in lines: 
            if re.search(r"from (.+?) import (.+?) as "+key, line):
                temp=op.find_between(line, "import", "as").lstrip().rstrip()
                if temp:
                    parentClssKey[parentClssKey.index(key)]=temp
                return parentClssKey
        return parentClssKey
    except Exception as ex:
        print(ex)
        print("Exception occurred in refusedBequestSmell.checkIfParentNamedAsDifferentlyForRefusedBequest")
   
        
    
def getClassLinesForRefusedBequest(key, classes,lines):
    try:
        classLines=[]
        if key in classes.keys():
            value = classes[key]
            if 'start' and 'end' in value: 
                classLines=lines[int(value['start']):int(value['end'])]
                if classLines:
                    sourceCode = ''.join(classLines)
                    classLines= op.removeCommentsFromString(sourceCode)
        return classLines
    except Exception as ex:
        print(ex)
        print("Exception occurred in refusedBequestSmell.getClassLinesForRefusedBequest")
  
    
def getClassAttributesForRefusedBequest(classLines):
    try:
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
    except Exception as ex:
        print(ex)
        print("Exception occurred in refusedBequestSmell.getClassAttributesForRefusedBequest")
  
def getClassAttributesForWholeProject(classes,lines):
    classAttributes={}
    try:
        if classes!=None and len(classes.items())>=1:    
            for key, _ in classes.items():
                classLines=[]
                value = classes[key]
                if 'start' and 'end' in value: 
                    classLines=lines[int(value['start']):int(value['end'])]
                    source= classLines
                    if source:
                        classLines=op.removeCommentsFromString(''.join(source))
                    classAttributes[key.lstrip()]=getClassAttributesForRefusedBequest(classLines)
              
        return classAttributes
    except Exception as ex:
        print(ex)
        print("Exception occurred in refusedBequestSmell.getClassAttributesForWholeProject")
       
                  
def getCalledParentMethodsForRefusedBequest(parentClassKey,parentClassMethods, childrenClassLines):
    try:
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
    except Exception as ex:
        print(ex)
        print("Exception occurred in refusedBequestSmell.getCalledParentMethodsForRefusedBequest")
  
    
def getUsedInheritanceMembersForRefusedBequest(childClassAttributes,parentClassAttributes):
    try:
        usedInheritanceMembersDict={}
        if childClassAttributes:
            keys =['classMethodsWithSelf','classMethodsWithCls','classAttributes'] 
            for key in keys:
                usedInheritanceMembersDict[key]=op.getCommonData(childClassAttributes[key], parentClassAttributes[key])
        return usedInheritanceMembersDict
    except Exception as ex:
        print(ex)
        print("Exception occurred in refusedBequestSmell.getUsedInheritanceMembersForRefusedBequest")
         
def calculateUsedInheritanceMembersForRefusedBequest(calledParentMethodsList,usedInheritanceMembersDict):
    try:
        totalNumberOfUsedNumber0fInheritanceMembers = len(calledParentMethodsList)
        for key in usedInheritanceMembersDict.keys():
            totalNumberOfUsedNumber0fInheritanceMembers += len(usedInheritanceMembersDict[key])
        return totalNumberOfUsedNumber0fInheritanceMembers
    except Exception as ex:
        print(ex)
        print("Exception occurred in refusedBequestSmell.calculateUsedInheritanceMembersForRefusedBequest")
      
def calculateTotalNumberOfInheritanceMembersForRefusedBequest(parentClassAttributes):
    try:
        totalNumberOfInheritanceMembers=0
        for key in parentClassAttributes.keys():
            totalNumberOfInheritanceMembers += len(parentClassAttributes[key])
        return totalNumberOfInheritanceMembers
    except Exception as ex:
        print(ex)
        print("Exception occurred in refusedBequestSmell.calculateTotalNumberOfInheritanceMembersForRefusedBequest")
  
    
    
def getCalledParentMethodsWithSelfAndClsForRefusedBequest(parentClassKey, parentClassAttributes, childClassLines):
    try:
        calledParentMethods= []
        if parentClassAttributes:
            calledParentMethodsWithSelfKeyword = getCalledParentMethodsForRefusedBequest(parentClassKey, parentClassAttributes['classMethodsWithSelf'], childClassLines)
            calledParentMethodsWithClsKeyword = getCalledParentMethodsForRefusedBequest(parentClassKey[0], parentClassAttributes['classMethodsWithCls'], childClassLines)
            
            calledParentMethods = calledParentMethodsWithSelfKeyword + calledParentMethodsWithClsKeyword
        return calledParentMethods
    except Exception as ex:
        print(ex)
        print("Exception occurred in refusedBequestSmell.getCalledParentMethodsWithSelfAndClsForRefusedBequest")
       

def calculateAUIRForRefusedBequest(parentClassKey, childClassAttributes, parentClassAttributes, calledParentMethods):
    try:
        totalNumberOfUsedInheritanceMembers=0
        totalNumberOfInheritanceMembers=0 
        if parentClassAttributes:
        #if childClassAttributes and parentClassAttributes:
            usedInheritanceMembersDict = getUsedInheritanceMembersForRefusedBequest(childClassAttributes, parentClassAttributes)
            totalNumberOfUsedInheritanceMembers = calculateUsedInheritanceMembersForRefusedBequest(calledParentMethods, usedInheritanceMembersDict)
            totalNumberOfInheritanceMembers = calculateTotalNumberOfInheritanceMembersForRefusedBequest(parentClassAttributes)
        averageInheritanceUsageRatio = 0
        try:
            if totalNumberOfUsedInheritanceMembers:
                averageInheritanceUsageRatio = totalNumberOfUsedInheritanceMembers / totalNumberOfInheritanceMembers
          
        except ZeroDivisionError :
            averageInheritanceUsageRatio=0
           
        if parentClassKey != "":
            return {"parentClassName":parentClassKey, "totalNumberOfUsedInheritanceMembers":totalNumberOfUsedInheritanceMembers, "totalNumberOfInheritanceMembers":totalNumberOfInheritanceMembers, "averageInheritanceUsageRatio":averageInheritanceUsageRatio}
    except Exception as ex:
        print(ex)
        print("Exception occurred in refusedBequestSmell.calculateAUIRForRefusedBequest")
       
    
def calculateRefusedBequest(fileName):
    try:
        smell=smll.BadSmell()
        refusedBequestDict={}
        classes={}
        classLines=[]
        classLines = inheritance.getClassLinesOfAPythonFile(fileName)

        with open(fileName, "r") as f:
            
            lines=[]
            lines = f.readlines()
         
            parentsDict={}
            parentsDict= inheritance.getParentsOfAClassesInACommit(classLines)
            
            classes=smell.getClassLinesOfFile(lines)
            classesAttributesDict = getClassAttributesForWholeProject(classes, lines)
            
            
            if classes!=None and len(classes.items())>=1:   
                print("Number of classes "+str(len(classes.keys())) +" in "+fileName)
                count=1 
                for key, _ in classes.items():
                    print("---------------------------")
                    print(str(count) +" of "+str(len(classes.keys())))
                    count+=1
                    childClassLines=[]
                    parentClassLines=[]
                    childClassAttributes={}
                    parentClassAttributes={}
                    calledParentMethods=[]
                    print("child class key is: "+key)
                    childClassLines = getClassLinesForRefusedBequest(key,classes, lines)
                    if key in classesAttributesDict.keys():
                        childClassAttributes=classesAttributesDict[key.strip()]
                    else:
                        childClassAttributes = getClassAttributesForRefusedBequest(childClassLines)
                    dit = inheritance.calculateDIT(key, parentsDict, 1)   
                    
                    parentClassKey = findParentClassForRefusedBequest(key, lines)
                    
                    refusedBequestDict[key]={}  
                    if len(parentClassKey)==1 and parentClassKey[0]!='' and parentClassKey[0]!='object' : 
           
                        print("parent of child is "+parentClassKey[0])
                        parentClassKey=checkIfParentNamedAsDifferentlyForRefusedBequest(parentClassKey[0], parentClassKey,lines)
                        print("After checking if parent named as differently, parent of child is "+parentClassKey[0])
                        if checkIfParentClassExistInProjectForRefusedBequest(parentClassKey[0], lines):
                            print(parentClassKey[0])
                            if parentClassKey[0] in classesAttributesDict.keys():
                                parentClassAttributes = classesAttributesDict[parentClassKey[0].lstrip()]
                            else:
                                parentClassLines = getClassLinesForRefusedBequest(parentClassKey[0], classes, lines)
                                parentClassAttributes = getClassAttributesForRefusedBequest(parentClassLines)
                           
                            print("parent class attributes is calculated. ") 
                            calledParentMethods = getCalledParentMethodsWithSelfAndClsForRefusedBequest(parentClassKey[0], parentClassAttributes, childClassLines)
                            print("called parent methods are calculated. ")    
                            
                            refusedBequestDict[key]=calculateAUIRForRefusedBequest(parentClassKey[0], childClassAttributes, parentClassAttributes, calledParentMethods) 
                            refusedBequestDict[key]['dit']=dit 
                        
                    elif len(parentClassKey)>1:
                        for i in range(len(parentClassKey)):
                            if parentClassKey[i]!='' and parentClassKey[i]!='object':
                                parentClassKey=checkIfParentNamedAsDifferentlyForRefusedBequest(parentClassKey[i], parentClassKey,lines)
                                
                                if checkIfParentClassExistInProjectForRefusedBequest(parentClassKey[i], lines):
                                    
                                    if parentClassKey[i] in classesAttributesDict.keys():
                                   
                                        parentClassAttributes = classesAttributesDict[parentClassKey[i].lstrip()]
                                    else:
                                        parentClassLines = getClassLinesForRefusedBequest(parentClassKey[i], classes, lines)
                                        parentClassAttributes = getClassAttributesForRefusedBequest(parentClassLines)
                         
                                    calledParentMethods = getCalledParentMethodsWithSelfAndClsForRefusedBequest(parentClassKey[i], parentClassAttributes, childClassLines)
                                        
                                    refusedBequestDict[key]=calculateAUIRForRefusedBequest(parentClassKey[i], childClassAttributes, parentClassAttributes, calledParentMethods) 
                                    refusedBequestDict[key]['dit']=dit                    
            f.close()
        
        return refusedBequestDict
    except Exception as ex:
        print(ex)
        print("Exception occurred in refusedBequestSmell.calculateRefusedBequest in "+fileName)
        