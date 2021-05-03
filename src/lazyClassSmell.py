'''
Created on May 4, 2021

@author: neda
'''
import src.runOperations as op
import src.BadSmell as smll
import src.parallelInheritance as pih

def calculateLazyClassSmell(fileInTheFolder, projectName):
    smell = smll.BadSmell()
    commitID=op.find_between(fileInTheFolder, "@", "@")
    pythonFile=pih.downloadProjectInASpecificCommit(projectName, commitID)
    pihSmellListDict=pih.calculateParallelInheritanceHiearchySmell(pythonFile)
    lazyClassList={}
    try:
        with open(fileInTheFolder, "r") as f:
            lines=f.readlines()
            classes=smell.getClassLinesOfFile(lines)
            classMethodCount= 0
            classAttr = 0
            dit=0
            if classes!=None and len(classes.items())>=1:
                for key, value in classes.items():  
                    if 'start' and 'end' in value:  
                        classLines=lines[int(value['start']):int(value['end'])]
                        if len(classLines)>0:
                            classLinesStr="\n".join(classLines)
                            classMethodCount=smell.checkClassMethods(classLines)
                            classAttr=smell.getClassAttribututes(classLinesStr)
                            if key.lstrip().rstrip() in pihSmellListDict.keys():
                                dit = pihSmellListDict[key]['dit']
                            else:
                                dit = "none"
                            isLazyClass = False
                            #print("classMethodCount=" + str(classMethodCount) + " classAttributesCount=" + str(classAttr) + " dit=" + str(dit) + " isLazyClass=" + str(isLazyClass))
                            if dit != "none":
                                if (classMethodCount < 5 and classAttr < 5) or dit < 2:
                                    isLazyClass = True
                                lazyClassList[key] = {'classMethodCount':classMethodCount, 'classAttributesCount':classAttr, 'dit':dit, 'isLazyClass':isLazyClass}
            f.close()
            return lazyClassList
    except Exception as ex:
        print(ex)
        print("Exception occurrred in lazyClassSmell.calculateLazyClassSmell in :"+fileInTheFolder)
