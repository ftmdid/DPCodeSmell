'''
    Created on Aug 15, 2021
    @author: neda
'''

import ast
import src.smell.longMethodSmell as lMethod
import src.smell.featureEnvySmell as fEnvy
import src.helper as helperMethods
import src.smell.parallelInheritance as inheritance
from src.runOperations import find_between, getMethodLinesOfClass
from src.removeComments import remove_comments_and_docstrings
import src.BadSmell as smell
import re
import os
from git import Repo
import src.FileOperations as FO


def calculateShotgunSurgery(fileCommitID,bugFixedCommitID, projectName,relationAnalysisShotgunSurgerySmellCSVout):
    try:
        
        repoPath= os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'Projects/'+projectName)
        repo = Repo(repoPath)
        list(repo.iter_commits(paths=repoPath))
        rootFolderForProject=  os.path.dirname(os.path.dirname(os.path.dirname(__file__)))+'/util/Analysis/BadSmells/ShotgunSurgery/'+projectName
        fileOp= FO.FileOperations(projectName)
        fileOp.createFolder(rootFolderForProject)
    
        '''1. Find the foreign class of each class in a project at the time project is not modified for bug fix '''
        filePath = inheritance.downloadProjectInASpecificCommit(projectName, fileCommitID) # project that is modified before bug fix commit
        #from lib2to3.main import main
        #main("lib2to3.fixes", ['--no-diffs', '-w', '-n', filePath])
        try:
            parsedFile = lMethod.parseFile(filePath)
            foreignClassCallOfEachClassInAProject = calculateForeignMethodsOfClassesWithAST(filePath, parsedFile, projectName)
        except Exception as ex:
            foreignClassCallOfEachClassInAProject = calculateForeignMethodsOfClassesWOutAST(filePath, projectName)
        '''2. Find the changes that is made in each file before and at the time bug fix'''
        differenceList = repo.git.diff(fileCommitID, bugFixedCommitID).split("\n")
        
        fileChangesDict = getFileChanges(differenceList)
        
        '''2.1 Modified file before and at the time bug is fixed'''
        rootFolderToCreateFiles=createModifiedFilesBeforeAndAtBugFixedCommit(fileOp, repo, rootFolderForProject, bugFixedCommitID, fileCommitID)
        '''2.2 Find the methods and classes changed before and at the time bug fixed commit'''
        whatChanged = []
        modifiedFilePath = os.path.dirname(os.path.dirname(os.path.dirname(__file__))) + '/util/Analysis/BadSmells/ShotgunSurgery/' + projectName.lower() + "/" + bugFixedCommitID
        for changedFileName, value in fileChangesDict.items():
            changedFileName = changedFileName.split(".py")[0] + "@@" + fileCommitID + ".py"
            changedFilePath = os.path.join(modifiedFilePath, changedFileName)
            #print(changedFilePath)
            linesOfChangedFile = {}
            #try:
            '''Find the line numbers of each class and function of a file'''
            linesOfChangedFile = checkForClassLinesWithAST(changedFilePath)
            if linesOfChangedFile:
                for it in value:
                    if it.startswith("@@"):
                        lineToSplit = find_between(it, "@@", "@@").split(" ")[1]
                        if "-" in lineToSplit:
                            lineToSplit = lineToSplit.split("-")[1].split(",")[0]
                        elif "+" in lineToSplit:
                            lineToSplit = lineToSplit.split("+")[1].split(",")[0]
                        whatChanged.append(findWhichClassMethod(linesOfChangedFile, int(lineToSplit)))
    
        whatChanged = helperMethods.removeEmptyStringsFromListOfStrings(whatChanged) #print(list(set(whatChanged)))
        
        '''2.3 Check if the  methods changed in whatChanged are compatible with its dependent'''
        if whatChanged:
            CM = []
            CC = []
            methodData = []
            commonCMItems = []
            commonCCItems = []
            for each in whatChanged:
                if foreignClassCallOfEachClassInAProject:
                    methodData = searchForMethod(each.lstrip().rstrip(), foreignClassCallOfEachClassInAProject)
                    if len(methodData[0]) > 0:
                        CM = methodData[0]
                        CC = methodData[1]
                        whatChanged.remove(each)
                        if whatChanged:
                            commonCMItems = list(set(whatChanged) & set(CM))
                            #commonCMItems = [i for i in newChangedList if i.lstrip().rstrip() in CM]
                            if commonCMItems:
                                commonCCItems = list(set([i.split(".")[0] for i in commonCMItems]))
                    relationAnalysisShotgunSurgerySmellCSVout.writerow([each, CM, len(CM), CC, len(CC), commonCMItems, len(commonCMItems), commonCCItems, len(commonCCItems)])
    
    except Exception as ex:
        print(ex)
        print("Exception occurred in shotgunSurgerySmell.calculateShotgunSurgery in " + projectName)


def findClassMethods(classes, lines):
    try:
        classWithMethods = {}
        for key, value in classes.items():
            classWithMethods[key.lstrip().rstrip()] = []
            if ('start' and 'end') in value:
                classLines = lines[int(value['start']):int(value['end'])]
                classMethods = checkClassMethods(classLines)
                classWithMethods[key.lstrip().rstrip()] = classMethods
        return classWithMethods
    except Exception as ex:
        print(ex)
        print("Exception occurred in shotgunSurgerySmell.findClassMethods")


def checkClassMethods(classLines):
    try:
        methodsList = []
        for each in classLines:
            if re.match(r'def(.+?)( ?\()', each.lstrip()) and not (each.lstrip().startswith("#")):
                currentMethod = each.split('def')[1].lstrip().split('(')[0]
                methodsList.append(currentMethod.lstrip().rstrip())

        return methodsList
    except Exception as ex:
        print(ex)
        print("Exception occurred in BadSmell.checkClassMethodsWithSelf method")


def checkForFunctionaCallsWoutAST(methods, classLines, parentClasses, className, classWithMethods):
    try:
        foreignCallsDict = {}
        string_check = re.compile('[=@!#$%^&*()<>?/\|}{~:]')
        if methods:
            for key, value in methods.items():
                funcCall = ""
                methodLines = classLines[int(value['start']):int(value['end'])]
                foreignCallsDict[key] = []
                for line in methodLines:
                    if "self." in line:
                        if "(" in line:
                            if string_check.search(line.split("self.")[1].split("(")[0]) == None:
                                if line.split("self.")[1].split("(")[0] == line.split("self.")[1].split("(")[0].strip():
                                    funcCall = line.split("self.")[1].split("(")[0]
                            if funcCall in classWithMethods[className]:
                                continue
                            else:
                                for eachParent in parentClasses:
                                    if eachParent in classWithMethods.keys():
                                        if funcCall in classWithMethods[eachParent]:
                                            funcCall = eachParent + "." + funcCall
                                            foreignCallsDict[key].append(funcCall)

                    elif "cls." in line:
                        if "(" in line:
                            if string_check.search(line.split("cls.")[1].split("(")[0]) == None:
                                if line.split("cls.")[1].split("(")[0] == line.split("cls.")[1].split("(")[0].strip():
                                    funcCall = line.split("cls.")[1].split("(")[0]
                            if funcCall in classWithMethods[className]:
                                continue
                            else:
                                for eachParent in parentClasses:
                                    if eachParent in classWithMethods.keys():
                                        if funcCall in classWithMethods[eachParent]:
                                            funcCall = eachParent + "." + funcCall
                                            foreignCallsDict[key].append(funcCall)



                    elif 'super().' in line:
                        funcCall = line.split("super().")[1].split("(")[0]
                        if parentClasses:
                            for eachParent in parentClasses:
                                if eachParent in classWithMethods.keys():
                                    if funcCall in classWithMethods[eachParent]:
                                        funcCall = eachParent + "." + funcCall
                                        foreignCallsDict[key].append(funcCall)
                    else:
                        if parentClasses:
                            for eachParent in parentClasses:
                                if (eachParent + ".") in line:
                                    funcCall = line.split(eachParent + ".")[1].split("(")[0]
                                    funcCall = eachParent + "." + funcCall
                                    foreignCallsDict[key].append(funcCall)

        return foreignCallsDict

    except Exception as ex:
        print(ex)
        print("Exception occurred in shotgunSurgerySmell.checkForFunctionaCallsWoutAST ")


def calculateForeignMethodsOfClassesWOutAST(fileName, projectName):
    try:
        smll = smell.BadSmell()
        with open(fileName, encoding="utf-8", errors='ignore') as f:
            classDict = {}
            fileLines = f.read()

            lines = remove_comments_and_docstrings(fileLines).split("\n")

            classes = smll.getClassLinesOfFile(lines)

            classWithMethods = findClassMethods(classes, lines)
            if classes != None and len(classes.items()) >= 1:

                for className, value in classes.items():
                    if ('start' and 'end') in value:
                        parentClasses = []
                        classLines = []
                        methods = {}
                        classLines = lines[int(value['start']):int(value['end'])]
                        methods = getMethodLinesOfClass(classLines)
                        if len(classLines) > 0:
                            if "(" and ")" in classLines[0]:
                                if "," in classLines[0]:
                                    parentClasses = classLines[0].split("(")[1].split(")")[0].split(",")
                                    for i in range(len(parentClasses)):
                                        if "." in parentClasses[i]:
                                            parentClasses[i] = parentClasses[i].split(".")[1]

                                else:
                                    parentClass = classLines[0].split("(")[1].split(")")[0]
                                    if "." in parentClass:
                                        parentClass = parentClass.split(".")[1]
                                    parentClasses.append(parentClass)

                                parentClasses = [each.lstrip().rstrip() for each in parentClasses]

                        foreignCallsDict = checkForFunctionaCallsWoutAST(methods, classLines, parentClasses, className,
                                                                         classWithMethods)
                        classDict[className] = foreignCallsDict
        f.close()
        return classDict
    except Exception as ex:
        print(ex)
        print("Exception occurred in shotgunSurgerySmell.calculateForeignMethodsOfClassesWOutAST in " + projectName)


def searchForMethod(searchKeyword, dictToBeSearched):
    try:
        CM = []
        CC = []
        for className, value in dictToBeSearched.items():
            for methodName, v in value.items():
                if searchKeyword in v:
                    CM.append(className + "." + methodName)
                    CC.append(className)
    
        CM = list(set(CM))
        CC = list(set(CC))
        return [CM, CC]
    except Exception as ex:
        print(ex)
        print("Exception occurred in shotgunSurgerySmell.searchForMethod")

        


def calculateForeignMethodsOfClassesWithAST(fileName, parsedFile, projectName):
    try:
        # parsedFile =  lMethod.parseFile(fileName)
        parsedFileContent = list(ast.walk(parsedFile))
        classOfFile = getClassesInFile(parsedFileContent)
        # methodsOfFile = getMethodsInFile(parsedFileContent)
        classMethodsOfFile = calculateClassMethods(parsedFileContent)  # this has the methods of the classes in the file
        textOfFile = lMethod.readFile(fileName)
        classDict = {}
        for content in parsedFileContent:
            if isinstance(content, ast.ClassDef):
                classData = visitClassNode(content, classOfFile, textOfFile,
                                           classMethodsOfFile)  # returns NIC and foreign calls
                classDict[content.name] = classData[1]
        return classDict

    except Exception as ex:
        print(ex)
        print("Exception occurred in shotgunSurgerySmell.calculateShotgunSurgery in " + fileName + " of " + projectName)


def calculateClassMethods(parsedFileContent):
    try:
        classDict = {}
        for content in parsedFileContent:
            if isinstance(content, ast.ClassDef):
                className = content.name
                classDict[className] = []
                for childNode in list(ast.walk(content)):
                    if isinstance(childNode, ast.FunctionDef):
                        methodName = childNode.name
                        classDict[className].append(methodName)
        return classDict
    except Exception as ex:
        print(ex)
        print("Exception occurred in shotgunSurgerySmell.calculateClassMethods")



def getClassesInFile(parsedFileContent):
    try:
        classOfFile = []
        for content in parsedFileContent:
            if isinstance(content, ast.ClassDef):
                classOfFile.append(content.name)
        return classOfFile
    except Exception as ex:
        print(ex)
        print("Exception occurred in shotgunSurgerySmell.getClassesInFile")


def getMethodsInFile(parsedFileContent):
    try:
        methodsOfFile = []
        for content in parsedFileContent:
            if isinstance(content, ast.ClassDef):
                continue
            elif isinstance(content, ast.FunctionDef):
                methodsOfFile.append(content.name)
        return methodsOfFile
    except Exception as ex:
        print(ex)
        print("Exception occurred in shotgunSurgerySmell.getMethodsInFile")


def visitClassNode(content, classOfFile, textOfFile, classMethodsOfFile):
    try:
        methodsOfClass = fEnvy.getClassMethods(content)
        if hasattr(content, 'bases') and len(content.bases) > 0:
            NIC = []
            NIC.append(content.bases)
            NIC.append(fEnvy.getImportStatementsInClass(content))
            if len(NIC) > 0:
                calls = getMethodCallOfEachClass(content, methodsOfClass, classOfFile, textOfFile, classMethodsOfFile)
            return [len(NIC), calls]  # calls: AID
        else:
            NIC = []
            NIC.append(fEnvy.getImportStatementsInClass(content))
            if len(NIC) > 0:
                calls = getMethodCallOfEachClass(content, methodsOfClass, classOfFile, textOfFile, classMethodsOfFile)
            return [len(NIC), calls]  # calls: AID    
    except Exception as ex:
        print(ex)
        print("Exception occurred in shotgunSurgerySmell.visitClassNode")

def getImportStatementsInClass(content):
    try:
        NIC = 0
        functions = fEnvy.getClassFunctions(content)
        for fnc in functions:
            NIC.append(fEnvy.checkForImportStatementsInFuncDefinition(fnc))
        return NIC
    except Exception as ex:
        print(ex)
        print("Exception occurred in shotgunSurgerySmell.getImportStatementsInClass")

def checkIfParentClassIsCalled(parentClassList, functionName, textOfFile, childNode):
    return [True for x in parentClassList if
            x + "." + functionName in textOfFile[childNode.lineno - 1].lstrip().rstrip()]


def getMethodCallOfEachClass(node, methodsOfClass, classOfFile, textOfFile, classMethodsOfFile):
    try:
        childnodes = list(ast.walk(node))
        pythonMethods = fEnvy.getPythonMethods()
        parentClassList = fEnvy.getClassOfParent(node)
        foreignCallsFromFunc = {}
        foreignCalls = []
        nodesList = []
        for childNode in childnodes:
            if isinstance(childNode, ast.FunctionDef):
                foreignCalls = []
                methodName = childNode.name
    
                for child in list(ast.walk(childNode)):
                    if isinstance(child, ast.Call):
                        functionName = fEnvy.visitCall(child)
                        if not ([child.lineno, functionName] in nodesList):
                            nodesList.append([child.lineno, functionName])
    
                            if (("super()." + functionName) in textOfFile[child.lineno - 1].lstrip().rstrip()):
                                if hasattr(node, 'bases'):
                                    if len(node.bases) == 1:
                                        if hasattr(node.bases[0], "id"):
                                            superClass = node.bases[0].id
                                        elif hasattr(node.bases[0], "attr"):
                                            superClass = node.bases[0].attr
                                        foreignCalls.append(superClass + "." + functionName)
                                    elif len(node.bases) > 1:
                                        superClasses = []
                                        for i in range(len(node.bases)):
                                            if hasattr(node.bases[i], "id"):
                                                superClasses.append(node.bases[i].id)
                                            elif hasattr(node.bases[i], "attr"):
                                                superClasses.append(node.bases[i].attr)
                                        for superClass in superClasses:
                                            if superClass in classMethodsOfFile.keys():
                                                if (functionName in classMethodsOfFile[superClass]):
                                                    foreignCalls.append(superClass + "." + functionName)
    
                            elif True in checkIfParentClassIsCalled(parentClassList, functionName, textOfFile, child):
                                for x in parentClassList:
                                    if x + "." + functionName in textOfFile[child.lineno - 1].lstrip().rstrip():
                                        foreignCalls.append(x + "." + functionName)
                            else:
                                if functionName in pythonMethods:
                                    continue
                                elif functionName in methodsOfClass:
                                    continue
                                elif functionName in classOfFile:  # create an instance of another class
                                    continue
                                else:
                                    tString = textOfFile[child.lineno - 1].lstrip().rstrip()
                                    if "self." + functionName in tString:
                                        if hasattr(node, 'bases'):
                                            if len(node.bases) == 1:
                                                superClass = ""
                                                if hasattr(node.bases[0], "id"):
                                                    superClass = node.bases[0].id
                                                elif hasattr(node.bases[0], "attr"):
                                                    superClass = node.bases[0].attr
                                                foreignCalls.append(superClass + "." + functionName)
                                            elif len(node.bases) > 1:
                                                superClasses = []
                                                for i in range(len(node.bases)):
                                                    if hasattr(node.bases[i], "id"):
                                                        superClasses.append(node.bases[i].id)
                                                    elif hasattr(node.bases[i], "attr"):
                                                        superClasses.append(node.bases[i].attr)
    
                                                for superClass in superClasses:
                                                    if superClass in classMethodsOfFile.keys():
                                                        if (functionName in classMethodsOfFile[superClass]):
                                                            foreignCalls.append(superClass + "." + functionName)
    
                foreignCalls = helperMethods.removeEmptyStringsFromListOfStrings(foreignCalls)
                foreignCalls = list(set(foreignCalls))
                foreignCallsFromFunc[methodName] = foreignCalls
        return foreignCallsFromFunc
    except Exception as ex:
        print(ex)
        print("Exception occurred in shotgunSurgerySmell.getMethodCallOfEachClass")

def getFileChanges(differenceList):
    try:
        fileChangesIndices = findIndicesOfModifiedFiles(differenceList)[0]
        lenOfDifferences = len(differenceList) #pythonFileChangeIndices = findIndicesOfModifiedFiles(differenceList)[1]
        fileChanges = []
        fileChangesDict = {}
        for i in range(lenOfDifferences):
            if re.search(r"diff --git a/(.+?).py b/.(.+?).py", differenceList[i]):
                fileName = find_between(differenceList[i], 'a/', 'b/').rstrip().rsplit("/", 1)[-1]
                ind = fileChangesIndices.index(i)
                if ind != len(fileChangesIndices) - 1:
                    fileChanges = differenceList[i:fileChangesIndices[ind + 1]]
                    fileChangesDict[fileName] = fileChanges
                else:
                    fileChanges = differenceList[i:lenOfDifferences + 1]
                    fileChangesDict[fileName] = fileChanges
        return fileChangesDict
    except Exception as ex:
        print(ex)
        print("Exception occurred in shotgunSurgerySmell.getFileChanges")
    
def findIndicesOfModifiedFiles(differenceList):
    try:
        pythonFileChangesIndices=[]
        fileChangesIndices=[]
        for i in range(len(differenceList)):
            if re.search(r"diff --git a/(.+?) b/.(.+?)", differenceList[i]):
                                    #print(differenceList[i])
                fileChangesIndices.append(i)
            if re.search(r"diff --git a/(.+?).py b/.(.+?).py", differenceList[i]):
                                    #print(differenceList[i])
                pythonFileChangesIndices.append(i)
        
        return [fileChangesIndices,pythonFileChangesIndices]
    except Exception as ex:
        print(ex)
        print("Exception occurred in shotgunSurgerySmell.findIndicesOfModifiedFiles")
    
def createModifiedFilesBeforeAndAtBugFixedCommit(fileOp, repo, rootFolderForProject, bugFixedCommitID, fileCommitID):
    try:
        rootFolderToCreateFiles = rootFolderForProject + "/" + bugFixedCommitID
        fileOp.createFolder(rootFolderToCreateFiles)
        
        #get the diff between two hashes in gitpython
        # print("fileCommitID:" + fileCommitID)
        sourceCommit = repo.commit(fileCommitID)
        # print("bugFixedCommitId:" + bugFixedCommitID)
        targetCommit = repo.commit(bugFixedCommitID)
        git_diff = sourceCommit.diff(targetCommit)
        changedFiles = [f.b_path for f in git_diff] #print( "\n".join( changedFiles ))
        
        for each in changedFiles:
            if each.endswith('.py'): #print(each)
                hexsha1 = repo.git.show('%s:%s' % (fileCommitID, each))
                fileName= os.path.join(rootFolderToCreateFiles, each.rsplit("/", 1)[-1]).split(".py")[0]+"@@"+fileCommitID + ".py"
                if not os.path.isfile(fileName):
                    fileOp.writeFileContentToPythonFile(hexsha1,fileName)
                hexsha2 = repo.git.show('%s:%s' % (bugFixedCommitID, each))
                fileName2 = os.path.join(rootFolderToCreateFiles, each.rsplit("/", 1)[-1]).split('.py')[0] + "@@"+bugFixedCommitID + ".py"
                if not os.path.isfile(fileName2):
                    fileOp.writeFileContentToPythonFile(hexsha2, fileName2)
        return rootFolderToCreateFiles
    except Exception as ex:
        print(ex)
        print("Exception occurred in shotgunSurgerySmell.createModifiedFilesBeforeAndAtBugFixedCommit method")
    
def checkForMethodLinesWithAST(node):
    try:
        methodLines={}
        for item in ast.walk(node):
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef )):
                methodLines[item.name]=[item.lineno, item.end_lineno]
        return methodLines
    except Exception as ex:
        print(ex)
        print("Exception occurred in shotgunSurgerySmell.checkForMethodLinesWithAST method")

def checkForClassLinesWithAST(fileInTheFolder):
    try:
        classLines={}
        if os.path.isfile(fileInTheFolder):
            parsedFileInTheFolder=lMethod.parseFile(fileInTheFolder)
            for item in ast.walk(parsedFileInTheFolder):
                if isinstance(item, ast.ClassDef):
                    #print(item.name)
                    classLines[item.name]={'lines':[item.lineno, item.end_lineno]}
                    classLines[item.name].update({'methods':checkForMethodLinesWithAST(item)})
                    #classLines[item.name]= checkForMethodLines(item)
        return classLines
    except Exception as ex:
        print(ex)
        print("Problem occurred in shotgunSurgerySmell.checkForClassWithAST method")
                
def findClassesInFile(fileInTheFolder):
    try:
        parsedFileInTheFolder=lMethod.parseFile(fileInTheFolder)
        classList=[]
        for item in ast.walk(parsedFileInTheFolder):
            if isinstance(item, ast.ClassDef):
                classList.append(item.name)
        return classList
    except Exception as ex:
        print(ex)
        print("Problem occurred in shotgunSurgerySmell.findClassesInFile method")
    
def findWhichClassMethod(linesOfChangedFile,lineToSplit):
    try:
        whatChanged=""
        for clss,clssItems in linesOfChangedFile.items(): 
            linesOfClass = clssItems['lines']
            if lineToSplit in range(int (linesOfClass[0]),int(linesOfClass[1])+1):
                for mthod,mthdLines in clssItems['methods'].items(): 
                    if lineToSplit in range(int(mthdLines[0]), int(mthdLines[1])+1):
                        whatChanged=clss+"."+mthod
        return whatChanged   
    except Exception as ex:
        print(ex)
        print("Problem occurred in shotgunSurgerySmell.findWhichClassMethod method")
            
                     

