'''
Created on Jun 9, 2020

@author: Neda
'''
from builtins import isinstance

# def getClassLinesOfAPythonFile(pythonFile):
#     '''
#         python file is a file that includes all files of a specific commit
#     '''
#     try:
#         classList=[]
#         with open(pythonFile) as fileToRead:
#             fileLines=fileToRead.readlines()
#             count=0
#             for line in fileLines:
#                 if line.lstrip().startswith('class '):
#                     print(line.lstrip())
#                     count +=1
#                     print(count)
#                 if line.lstrip().startswith('class ') and (":" in line):
#                     classList.append(line)
#         fileToRead.close()
#         return classList
#     except Exception as ex:
#         print(ex)       
def getClassLinesOfAPythonFile(pythonFile):
    '''
        python file is a file that includes all files of a specific commit
    '''
    try:
        classList=[]
        with open(pythonFile) as fileToRead:
            fileLines=fileToRead.read()
            lines=fileLines.splitlines()
            import ast
            tree= ast.parse(fileLines)
            for item in ast.walk(tree):
                if isinstance(item, ast.ClassDef):
                    className=lines[item.lineno-1].lstrip()
            
                    classList.append(className)
        fileToRead.close()
        return classList
    except Exception as ex:
        print(ex)  
        
def getAllClassesInACommit(classLine):
    classesInACommit=[]
    for each in classLine:
        if "(" and ")" in each:
            child=each.split('class ')[1].split("(")[0].lstrip().rstrip()
            if child not in classesInACommit:
                classesInACommit.append(child)
            if ("." not in each) and ("," not in each): 
                parent= each.split("(")[1].split(")")[0]
                if parent and (parent not in classesInACommit):
                    classesInACommit.append(parent)
            elif ("." in each) and ("," not in each):
                parent=each.split("(")[1].split(")")[0].split(".")[1]
                if parent and (parent not in classesInACommit):
                    classesInACommit.append(parent)
                parentsOfParent=each.split("(")[1].split(")")[0].split(".")[0]
                if parentsOfParent and (parentsOfParent not in classesInACommit):
                    classesInACommit.append(parentsOfParent)
            elif ("." not in each) and ("," in each):
                parents=each.split("(")[1].split(")")[0].split(",")
                for parent in parents:
                    if parent and (parent not in classesInACommit):
                        classesInACommit.append(parent)
            elif ("." in each) and ("," in each):
                parents=each.split("(")[1].split(")")[0].split(",")
                for parent in parents:
                    if "." in parent:
                        if parent.split(".")[1] and (parent.split(".")[1] not in classesInACommit):
                            classesInACommit.append(parent.split(".")[1])
                        if parent.split(".")[0]  and (parent.split(".")[0] not in classesInACommit):
                            classesInACommit.append(parent.split(".")[0])
        else:
            if not each.split('class ')[1].split(":")[0].lstrip().rstrip() in classesInACommit:
                classesInACommit.append(each.split('class ')[1].split(":")[0].lstrip().rstrip())

    return classesInACommit
    
def getParentsOfAClassesInACommit(classList):
    parentOfClassDict={}
    for each in classList:
        if "(" and ")" in each:
            child=each.split('class ')[1].split("(")[0].lstrip().rstrip()
            parentOfClassDict[child]=[]
            if ("." not in each) and ("," not in each): 
                parent= each.split("(")[1].split(")")[0]
                if parent!=child:
                    parentOfClassDict[child].append(parent)
            elif ("." in each) and ("," not in each):
                parent=each.split("(")[1].split(")")[0].split(".")[1]
                if parent!=child:
                    parentOfClassDict[child].append(parent)
                parentOfClassDict[parent]=[]
                if parent!=each.split("(")[1].split(")")[0].split(".")[0]:
                    parentOfClassDict[parent].append(each.split("(")[1].split(")")[0].split(".")[0])
            elif ("." not in each) and ("," in each):
                parents=each.split("(")[1].split(")")[0].split(",")
                for parent in parents:
                    if child!=parent:
                        parentOfClassDict[child].append(parent)
            elif ("." in each) and ("," in each):
                parents=each.split("(")[1].split(")")[0].split(",")
                for parent in parents:
                    if "." in parent:
                        if child!=parent.split(".")[1]:
                            parentOfClassDict[child].append(parent.split(".")[1])
                        parentOfClassDict[parent.split(".")[1]]=[]
                        if parent.split(".")[1]!=parent.split(".")[0]:
                            parentOfClassDict[parent.split(".")[1]].append(parent.split(".")[0])
        else:
            child=each.split('class ')[1].split(":")[0].lstrip().rstrip()
            parentOfClassDict[child]=['object']
    return parentOfClassDict
                
def calculateDIT(className, parentsDict, count):        
    if className in parentsDict.keys():
        parents=parentsDict[className]
        if (len(parents)==1) and (parents[0]=='object'):
            count =1
        elif (len(parents)==1) and (parents==['']):
            count=1
        elif (len(parents)>=1):
            count += calculateDIT(parents[0], parentsDict, count)  
            # if  (len(parents)==1):
                # count += calculateDIT(parents[0], parentsDict, count)  
            # else:
                # for i in range(0, len(parents)):
                    # if (parents[i]!='object'):
                        # count += calculateDIT(parents[i], parentsDict, count)
         
                         
    return count
           
  
#def calculateNumberOfChildren(className, classLines) 

def getNumberOfChildrenOfClassesInACommit(keys, classLines):
    childClassesDict={}
    for key in keys:
        childClasses=[]
        for eachClassLine in classLines:
            if "(" and ")" in eachClassLine:
                if "," in eachClassLine:
                    parentClasses = eachClassLine.split("(")[1].split(")")[0].split(",")
                    for parent in parentClasses:
                        if "." in parent:
                            parent = parent.split(".")[1]
                            if parent==key:
                                childClasses.append(eachClassLine.split("(")[0].split("class ")[1].lstrip().rstrip())
                        else:
                            if parent==key:
                                childClasses.append(eachClassLine.split("(")[0].split("class ")[1].lstrip().rstrip())
                else:
                    parentClass=eachClassLine.split("(")[1].split(")")[0]
                    if "." in parentClass:
                        parentClass= parentClass.split(".")[1]
                        if parentClass==key:
                            childClasses.append(parentClass)
                    else:
                        if parentClass==key:
                            childClasses.append(parentClass)
        childClassesDict[key]=childClasses
    return childClassesDict

def calculateNumberOfChildren(key, classLines):
    childClasses=[]
    for eachClassLine in classLines:
        if "(" and ")" in eachClassLine:
            if "," in eachClassLine:
                parentClasses = eachClassLine.split("(")[1].split(")")[0].split(",")
                for parent in parentClasses:
                    if "." in parent:
                        if parent.split(".")[1]==key:
                            childClasses.append(eachClassLine.split("(")[0].split("class ")[1].lstrip().rstrip())
                        elif parent.split(".")[0]==key:
                            childClasses.append(parent.split(".")[1])
                    else:
                        if parent==key:
                            childClasses.append(eachClassLine.split("(")[0].split("class ")[1].lstrip().rstrip())
            else:
                parentClass=eachClassLine.split("(")[1].split(")")[0]
                if "." in parentClass:
                    if parentClass.split(".")[1]==key:
                        childClasses.append(eachClassLine.split("(")[0].split("class ")[1].lstrip().rstrip())
                    elif parentClass.split(".")[0]==key:
                        childClasses.append(parentClass.split(".")[1])
                elif "[" and "]" in parentClass:
                    if parentClass.split("[")[0]==key:
                        childClasses.append(eachClassLine.split("(")[0].split("class ")[1].lstrip().rstrip())
    
                else:
                    if parentClass==key:
                        childClasses.append(eachClassLine.split("(")[0].split("class ")[1].lstrip().rstrip())
    
    childClasses = list(dict.fromkeys(childClasses))
    return len(childClasses)
                
    
def calculateParallelInheritanceHiearchySmell(pythonFile):

    pihSmellListDict={}
    
    classLines= getClassLinesOfAPythonFile(pythonFile)
    
    parents= getParentsOfAClassesInACommit(classLines)
    
    
    keysList=getAllClassesInACommit(classLines)
    
    
    for key in keysList:
        if key!='object':
            dit = calculateDIT(key, parents, 1)
            
            noc = calculateNumberOfChildren(key, classLines)
            
            #print("class= "+key+" dit= "+str(dit)+" noc= "+str(noc))
        
            pihSmell= False
            if dit>3 or noc>4:
                pihSmell= True
            pihSmellListDict[key]={'dit':dit,'noc':noc,'isPIHSmell':pihSmell}
            #print(pihSmellListDict)
            
    return pihSmellListDict

            
            

if __name__ == '__main__':
    pythonFile="/Users/neda/Desktop/workspace/BadSmells/util/Zip/numpy/allPythonFiles.py" 
    pihSmellListDict = calculateParallelInheritanceHiearchySmell(pythonFile)
 


























