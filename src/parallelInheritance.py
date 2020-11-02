'''
Created on Jun 9, 2020

@author: Neda
'''

def getClassLinesOfAPythonFile(pythonFile):
    '''
        python file is a file that includes all files of a specific commit
    '''
    try:
        classList=[]
        with open(pythonFile) as fileToRead:
            fileLines=fileToRead.readlines()
            for line in fileLines:
                if line.lstrip().startswith('class ') and (":" in line):
                    classList.append(line)
        fileToRead.close()
        return classList
    except Exception as ex:
        print(ex)       
    
def getParentsOfClass(txt, classList):  
    classDict={} 
    if "(" and ")" in txt:
        nameOfClass=txt.split('class ')[1].lstrip().split("(")[0]
        classDict[nameOfClass]=[]
        lineOfSuperClass=txt.split("(")[1].split(")")[0].strip()
        if lineOfSuperClass:
            if "." in lineOfSuperClass:
                superClasses=lineOfSuperClass.split(".")
                for each in superClasses:
                    getParentsOfClass("class "+each, classList)
            else:
                if not lineOfSuperClass in classDict[nameOfClass]:
                    classDict[nameOfClass].append(lineOfSuperClass)
                    
                    getParentsOfClass("class "+lineOfSuperClass, classList)
    else:
        for each in classList:
            if ":" in txt:
                nameOfClass=txt.split("class ")[1].split(":")[0].strip()
            else: 
                nameOfClass=txt.split("class ")[1].strip()
            classDict[nameOfClass]=[]
            if each.startswith(txt):
                if "(" in each:
                    superClass = each.split("(")[0]
                    if superClass==txt:
                        getParentsOfClass(each, classList)
                else:
                    superClass=each.split(":")[0]
                    if superClass==txt:
                        getParentsOfClass(each, classList)
    return classDict
           
    

def getClassNameFromList(className, classList):
    for each in classList:
        if className in each:
            return  each
    return False 
    
def getDIT(pythonFile):
    classList= getClassLinesOfAPythonFile(pythonFile)
    superClassDict={}
    for each in classList:
        result=getParentsOfClass(each,classList)
        for k, v in result.items():
            if k not in superClassDict.keys():
                superClassDict[k]=v
            else:
                if not v in superClassDict[k]:
                    for item in v:
                        superClassDict[k].append(item)

    return superClassDict

def calculateNumberOfChildren(classDictionary):
    children={}
    for i in classDictionary.values():

        if len(i)==1:
            children[i[0]]=[]
            for k,v in classDictionary.items():
                if i[0] in v:
                    children[i[0]].append(k)
        elif len(i)>1:
            for each in i: 
                if not each in children.keys():
                    children[each]=[]
                for k,v in classDictionary.items():
                   
                    if each in v:
                        children[each].append(k)
        
    return children



if __name__ == '__main__':
    pythonFile="/Users/neda/Desktop/workspace/BadSmells/util/Zip/numpy/allPythonFiles.py" 
    #calculateDepthOfInheritance(pythonFile)
    parentDict=getDIT(pythonFile)
    childrenDict= calculateNumberOfChildren(parentDict)
#     for k, v in parentDict.items():
#         print(k,v)
    for k,v in childrenDict.items():
        print(k,v)


'''

ancestorClassesForEachClass=dit #Ancestor of each class
childrens=calculateNumberOfChildren(dit)
for k,v in dit.items(): # k is the name of class, v is the number of parent class
    for key, value in childrens.items():
        if k.lstrip().rstrip()==key.lstrip().rstrip():
            print(k,len(v), len(value))
        else:
            print(k, len(v),0)
     
'''    

# print("Number of children : ")
# for each in calculateNumberOfChildren(dit):
#     print(each)























