'''
Created on Jun 26, 2020

@author: neda
'''

import src.FileOperations as FO
import os
from datetime import datetime
import csv
import itertools
import src.BadSmell as BS
import numpy as np

class Relation(object):
    def __init__(self,projectName):
        self.projectName=projectName
        self.fileOp = FO.FileOperations(self.projectName)
        
    def sortListsByDateOnFileName(self,fileList):
             
        sortedDateListDict={}         
        for each in fileList:
            fileDate=each.split("@",2)[2].replace('.py','')
            dateTimeObj = datetime.strptime(fileDate,  "%a %b %d %H:%M:%S %Y %z")
            sortedDateListDict[each]=dateTimeObj
        
       
        sortedList=[k for k, _ in sorted(sortedDateListDict.items(), key=lambda item: item[1])]
     
        return sortedList

    '''
        Referenced from:https://www.enricozini.org/blog/2019/debian/gitpython-list-all-files-in-a-git-commit/ 
    
    def list_paths(root_tree, path=Path(".")):
        for blob in root_tree.blobs:
            yield path / blob.name
        for tree in root_tree.trees:
            yield from list_paths(tree, path / tree.name)
    '''

    '''
        Referenced from: https://stackoverflow.com/questions/3368969/find-string-between-two-substrings
    '''      
    def find_between(self,s, first, last ):
        try:
            start = s.index( first ) + len( first )
            end = s.index( last, start )
            return s[start:end]
        except ValueError:
            return ""

    def checkFilesWithinRoot(self,root):
        filesInFolder = [os.path.join(root,x) for x in os.listdir(root)]
        filesInFolder=self.sortListsByDateOnFileName(filesInFolder)
        return filesInFolder
      
    
    def getModifiedFilesFromProject(self,folderDirs):
        modifiedFileListDict={}
        for _, _, files in os.walk(folderDirs):
            for file in files:
                if file.endswith('py'):
                    modifiedFileListDict[file] = self.find_between(file, "@", "@")
        return modifiedFileListDict
    
    
    def getcommitIDsFromSyntacticvsSemanticAnalysisFile(self,buggedCommitsList):
        commitIDList=[]
        for each in buggedCommitsList:
            commitID = each[0] # 0 is the commit id index in buggedCommitsList 
            commitIDList.append(commitID)
        
        return commitIDList
    
    def checkForDuplicatesInListsofList(self,listToBeChecked):
        listToBeChecked=list(k for k,_ in itertools.groupby(listToBeChecked))
        return listToBeChecked
    
    def analyzeLargeClassSmell(self,filesListWithBugFixedCommitsDict, projectName,projectPath,smell):            
        try:
            print("Started on large class bad smell analysis for "+projectName)
            relationAnalysisLargeClassCSVfile = os.path.dirname(os.path.dirname(__file__)) + '/util/Analysis/BadSmells/LargeClass/LargeClassRelationAnalysisOf'+self.projectName+'.csv'
            relationAnalysisLargeClassCSVout = csv.writer(open(os.path.join(projectPath, relationAnalysisLargeClassCSVfile), 'w+'))
            relationAnalysisLargeClassCSVout.writerow(('CommitID' ,'File Name','Class Name' ,'isLargeClass', 'Index of File In Folder', 'Index of Bug Fixed Commit In File','Diff',"Number of Files In Folder", "Folder"))
           
            largeClassRelationAnalysisCSVoutList=[]
            for fileName in filesListWithBugFixedCommitsDict.keys():     
                filesInFolder=filesListWithBugFixedCommitsDict[fileName]
                bugFixedCommitFileDir=  os.path.dirname(os.path.dirname(__file__)) + '/util/Python/'+self.projectName.lower()+"/"+ fileName.split("@")[0] +"/"+fileName
                bugFixedCommitIndexInItsFolder=filesInFolder.index(bugFixedCommitFileDir)
                largeClassDict = {}
                for fileInTheFolder in filesInFolder:
                    fileIndex = filesInFolder.index(fileInTheFolder)
                    if (bugFixedCommitIndexInItsFolder-fileIndex<=5) and (bugFixedCommitIndexInItsFolder-fileIndex>=0):
                        largeClassDict = smell.checkForLargeClass(fileInTheFolder)
                        if largeClassDict:
                            for k, v in largeClassDict.items():
                                #if str(v['isLargeClass']) == "True":
                                    fileIndex = filesInFolder.index(fileInTheFolder)
                                    rootName = fileInTheFolder.split("@")[0] 
                #                   commitID=fileName.split('@')[1]
                                    #largeClassRelationAnalysisCSVoutList.append([fileName.split('@')[1],fileInTheFolder,k, "Yes", str(fileIndex), str(bugFixedCommitIndexInItsFolder) ,str(len(filesInFolder)), rootName])
                                    largeClassRelationAnalysisCSVoutList.append([fileName.split('@')[1],fileInTheFolder,k, str(v['isLargeClass']), str(fileIndex), str(bugFixedCommitIndexInItsFolder),str(bugFixedCommitIndexInItsFolder-fileIndex) ,str(len(filesInFolder)), rootName])
                                
            largeClassRelationAnalysisCSVoutList=self.checkForDuplicatesInListsofList((largeClassRelationAnalysisCSVoutList))
            for analysis in largeClassRelationAnalysisCSVoutList:
                relationAnalysisLargeClassCSVout.writerow(analysis)
            print("Large class bad smell analysis for "+projectName + " is done!")
        except Exception as ex:
            print(ex)
            print("Exception occurred in Relation.analyzeLargeClassSmell() method")   
        
    def analyzeLongParameterClassSmell(self,filesListWithBugFixedCommitsDict, projectName,projectPath,smell):  
        try:
            print("Started on long parameter list bad smell analysis for "+projectName)       
            relationAnalysisLongParameterListCSVfile = os.path.dirname(os.path.dirname(__file__)) + '/util/Analysis/BadSmells/LongParameterList/LongParameterListRelationAnalysisOf'+self.projectName+'.csv'
            relationAnalysisLongParameterListCSVout = csv.writer(open(os.path.join(projectPath, relationAnalysisLongParameterListCSVfile), 'w+'))
            relationAnalysisLongParameterListCSVout.writerow(('CommitID', 'File Name','Method Name' ,'isLongParameterList', 'Index of File In Folder','Index of Bug Fixed Commit In File', "Number of Files In Folder", "Folder"))
           
                       
            longParameterListDict={}
            fileIndex = 0
            longParameterListRelationAnalysisCSVoutList=[]
    
                #for fileName, filesInRootOfFileName in filesListWithBugFixedCommitsDict.items():  # key=fileName, value=filesInRootOfFileName
            for fileName in filesListWithBugFixedCommitsDict.keys():  # key=fileName, value=filesInRootOfFileName
                    
                filesInFolder=filesListWithBugFixedCommitsDict[fileName]
                bugFixedCommitFileDir=  os.path.dirname(os.path.dirname(__file__)) + '/util/Python/'+self.projectName.lower()+"/"+ fileName.split("@")[0] +"/"+fileName
                bugFixedCommitIndexInItsFolder=filesInFolder.index(bugFixedCommitFileDir)
              
                  
                for fileInTheFolder in filesInFolder:  
                    fileIndex = filesInFolder.index(fileInTheFolder)
                    if (bugFixedCommitIndexInItsFolder-fileIndex<=5) and (bugFixedCommitIndexInItsFolder-fileIndex>=0):
                      
                        longParameterListDict=smell.checkForLongParameterList(fileInTheFolder)
                        if longParameterListDict:
                            for k, v in longParameterListDict.items():
                                #if str(v['isLongParameterList'])=="True":
                                fileIndex = filesInFolder.index(fileInTheFolder)
                                rootName = fileInTheFolder.split("@")[0] 
                                #longParameterListRelationAnalysisCSVoutList.append([fileName.split('@')[1], fileInTheFolder,k,"Yes", str(fileIndex),str(bugFixedCommitIndexInItsFolder) ,str(len(filesInFolder)), rootName])
                                longParameterListRelationAnalysisCSVoutList.append([fileName.split('@')[1], fileInTheFolder,k,str(v['isLongParameterList']), str(fileIndex),str(bugFixedCommitIndexInItsFolder) ,str(len(filesInFolder)), rootName])
                     
                       
            longParameterListRelationAnalysisCSVoutList=self.checkForDuplicatesInListsofList(longParameterListRelationAnalysisCSVoutList)
            for analysis in longParameterListRelationAnalysisCSVoutList:
                relationAnalysisLongParameterListCSVout.writerow(analysis)
            print("Long parameter list bad smell analysis for "+projectName +" is done!")
        except Exception as ex:
            print(ex)
            print("Exception occurred in Relation.analyzeLongParameterClassSmell() method")                             


    def analyzeMessageChainsSmell(self,filesListWithBugFixedCommitsDict, projectName,projectPath,smell):
        try:
            print("Started on message chain bad smell analysis for "+projectName)    
            relationAnalysisMessageChainCVoutListCSVfile = os.path.dirname(os.path.dirname(__file__)) + '/util/Analysis/BadSmells/MessageChain/MessageChainRelationAnalysisOf'+self.projectName+'.csv'
            relationAnalysisMessageChainCVoutListCSVout = csv.writer(open(os.path.join(projectPath, relationAnalysisMessageChainCVoutListCSVfile), 'w+'))
            relationAnalysisMessageChainCVoutListCSVout.writerow(('CommitID', 'File Name','Message Chain Line' ,'isMessageChain', 'Index of File In Folder','Index of Bug Fixed Commit In File', "Number of Files In Folder", "Folder"))
          
               
            fileIndex = 0
            messageChainRelationAnalysisCVoutList=[]
            for fileName in filesListWithBugFixedCommitsDict.keys():  # key=fileName, value=filesInRootOfFileName
                     
                filesInFolder=filesListWithBugFixedCommitsDict[fileName]
                bugFixedCommitFileDir=  os.path.dirname(os.path.dirname(__file__)) + '/util/Python/'+self.projectName.lower()+"/"+ fileName.split("@")[0] +"/"+fileName
                bugFixedCommitIndexInItsFolder=filesInFolder.index(bugFixedCommitFileDir)
    
                messageChainDict={}
                for fileInTheFolder in filesInFolder:
                        
                    messageChainDict= smell.checkForMessageChain(fileInTheFolder)
                    if messageChainDict:
                        for k, v in messageChainDict.items():
                            if str(v["isMessageChain"])=="True":
                                rootName = fileInTheFolder.split("@")[0] 
                                messageChainRelationAnalysisCVoutList.append([fileName.split('@')[1],fileInTheFolder,k, "Yes", str(fileIndex), str(bugFixedCommitIndexInItsFolder) ,str(len(filesInFolder)), rootName])
    
            messageChainRelationAnalysisCVoutList = self.checkForDuplicatesInListsofList(messageChainRelationAnalysisCVoutList)
            for analysis in messageChainRelationAnalysisCVoutList:
                relationAnalysisMessageChainCVoutListCSVout.writerow(analysis)
            print("Message chain bad smell analysis for "+projectName + " is done")
        except Exception as ex:
            print(ex)
            print("Exception occurred in Relation.analyzeMessageChainsSmell() method")                             

    def analyzeParallelInheritanceHiearchySmell(self,filesListWithBugFixedCommitsDict, projectName,projectPath,smell):  
        try:
            print("Started on parallel hierarchy bad smell analysis for "+projectName)       
            relationAnalysisParallelInheritanceHierarchySmellCSVfile = os.path.dirname(os.path.dirname(__file__)) + '/util/Analysis/BadSmells/ParallelInheritanceHierarchy/ParallelInheritanceHierarchySmellRelationAnalysisOf'+self.projectName+'.csv'
            relationAnalysisParallelInheritanceHierarchySmellCSVout = csv.writer(open(os.path.join(projectPath, relationAnalysisParallelInheritanceHierarchySmellCSVfile), 'w+'))
            relationAnalysisParallelInheritanceHierarchySmellCSVout.writerow(('CommitID', 'File Name','Class Name' ,'DIT','NOC','isParallelInheritanceHiearchy', 'Index of File In Folder','Index of Bug Fixed Commit In File', "Number of Files In Folder", "Folder"))
           
                       
            parallelInheritanceHierarchySmellDict={}
            fileIndex = 0
            parallelInheritanceHierarchySmellRelationAnalysisCSVoutList=[]
    
                #for fileName, filesInRootOfFileName in filesListWithBugFixedCommitsDict.items():  # key=fileName, value=filesInRootOfFileName
            if filesListWithBugFixedCommitsDict:

                for fileName in filesListWithBugFixedCommitsDict.keys():  # key=fileName, value=filesInRootOfFileName
                    filesInFolder=filesListWithBugFixedCommitsDict[fileName]
                    bugFixedCommitFileDir=  os.path.dirname(os.path.dirname(__file__)) + '/util/Python/'+self.projectName.lower()+"/"+ fileName.split("@")[0] +"/"+fileName
                    bugFixedCommitIndexInItsFolder=filesInFolder.index(bugFixedCommitFileDir)
                      
                    for fileInTheFolder in filesInFolder:
                            fileIndex = filesInFolder.index(fileInTheFolder)
                        #if (bugFixedCommitIndexInItsFolder-fileIndex<=3) and (bugFixedCommitIndexInItsFolder-fileIndex>=0):
                            parallelInheritanceHierarchySmellDict=smell.checkForParallelInheritanceHiearchy(fileInTheFolder, self.projectName)
                            if parallelInheritanceHierarchySmellDict:
                                for k, v in parallelInheritanceHierarchySmellDict.items():
                                        #if str(v['isPIHSmell'])=="True":
                                    #fileIndex = filesInFolder.index(fileInTheFolder)
                                    rootName = fileInTheFolder.split("@")[0] 
                                    parallelInheritanceHierarchySmellRelationAnalysisCSVoutList.append([fileName.split('@')[1], fileInTheFolder,k,str(v['dit']),str(v['noc']),str(v['isPIHSmell']), str(fileIndex),str(bugFixedCommitIndexInItsFolder) ,str(len(filesInFolder)), rootName])
                                    
                                
                parallelInheritanceHierarchySmellRelationAnalysisCSVoutList=self.checkForDuplicatesInListsofList(parallelInheritanceHierarchySmellRelationAnalysisCSVoutList)
                for analysis in parallelInheritanceHierarchySmellRelationAnalysisCSVoutList:
                    relationAnalysisParallelInheritanceHierarchySmellCSVout.writerow(analysis)
                print("Parallel Hierarchy bad smell analysis for "+projectName +" is done!")
        except Exception as ex:
            print(ex)
            print("Exception occurred in Relation.analyzeParallelInheritanceHiearchySmell() method")                             
    
    def analyzeLazyClassSmell(self,filesListWithBugFixedCommitsDict, projectName,projectPath,smell):  
        try:
            print("Started on lazy class bad smell analysis for "+projectName)       
            relationAnalysisLazyClassSmellCSVfile = os.path.dirname(os.path.dirname(__file__)) + '/util/Analysis/BadSmells/LazyClass/LazyClassSmellRelationAnalysisOf'+self.projectName+'.csv'
            relationAnalysisLazyClassSmellCSVout = csv.writer(open(os.path.join(projectPath, relationAnalysisLazyClassSmellCSVfile), 'w+'))
            relationAnalysisLazyClassSmellCSVout.writerow(('CommitID', 'File Name','Class Name' ,'Number of Methods','Number of Attributes','DIT','isLazyClass', 'Index of File In Folder','Index of Bug Fixed Commit In File', "Number of Files In Folder", "Folder"))
           
                       
            lazyClassSmellDict={}
            fileIndex = 0
            lazyClassSmellRelationAnalysisCSVoutList=[]
    
                #for fileName, filesInRootOfFileName in filesListWithBugFixedCommitsDict.items():  # key=fileName, value=filesInRootOfFileName
            if filesListWithBugFixedCommitsDict:

                for fileName in filesListWithBugFixedCommitsDict.keys():  # key=fileName, value=filesInRootOfFileName
                    filesInFolder=filesListWithBugFixedCommitsDict[fileName]
                    bugFixedCommitFileDir=  os.path.dirname(os.path.dirname(__file__)) + '/util/Python/'+self.projectName.lower()+"/"+ fileName.split("@")[0] +"/"+fileName
                    bugFixedCommitIndexInItsFolder=filesInFolder.index(bugFixedCommitFileDir)
                      
                    for fileInTheFolder in filesInFolder:
                            fileIndex = filesInFolder.index(fileInTheFolder)
                        #if (bugFixedCommitIndexInItsFolder-fileIndex<=3) and (bugFixedCommitIndexInItsFolder-fileIndex>=0):
                            lazyClassSmellDict=smell.checkForLazyClass(fileInTheFolder, self.projectName)
                            if lazyClassSmellDict:
                                for k, v in lazyClassSmellDict.items():
                                        #if str(v['isPIHSmell'])=="True":
                                    #fileIndex = filesInFolder.index(fileInTheFolder)
                                    rootName = fileInTheFolder.split("@")[0] 
                                    lazyClassSmellRelationAnalysisCSVoutList.append([fileName.split('@')[1], fileInTheFolder,k,str(v['classMethodCount']),str(v['classAttributesCount']),str(v['dit']),str(v['isLazyClass']), str(fileIndex),str(bugFixedCommitIndexInItsFolder) ,str(len(filesInFolder)), rootName])
                                    
                                
                lazyClassSmellRelationAnalysisCSVoutList=self.checkForDuplicatesInListsofList(lazyClassSmellRelationAnalysisCSVoutList)
                for analysis in lazyClassSmellRelationAnalysisCSVoutList:
                    relationAnalysisLazyClassSmellCSVout.writerow(analysis)
                print("Lazy class bad smell analysis for "+projectName +" is done!")
        except Exception as ex:
            print(ex)
            print("Exception occurred in Relation.analyzeLazyClassSmell() method")                             

    def analyzeDataClassSmell(self,filesListWithBugFixedCommitsDict, projectName,projectPath,smell):  
        try:
            print("Started on data class bad smell analysis for "+projectName)       
            relationAnalysisDataClassSmellCSVfile = os.path.dirname(os.path.dirname(__file__)) + '/util/Analysis/BadSmells/DataClass/DataClassSmellRelationAnalysisOf'+self.projectName+'.csv'
            relationAnalysisDataClassSmellCSVout = csv.writer(open(os.path.join(projectPath, relationAnalysisDataClassSmellCSVfile), 'w+'))
            relationAnalysisDataClassSmellCSVout.writerow(('CommitID', 'File Name','Class Name' ,'WMC','LCOM','isDataClass', 'Index of File In Folder','Index of Bug Fixed Commit In File', "Number of Files In Folder", "Folder"))
                
            dataClassSmellDict={}
            fileIndex = 0
            dataClassSmellRelationAnalysisCSVoutList=[]
    
            #for fileName, filesInRootOfFileName in filesListWithBugFixedCommitsDict.items():  # key=fileName, value=filesInRootOfFileName
            if filesListWithBugFixedCommitsDict:

                for fileName in filesListWithBugFixedCommitsDict.keys():  # key=fileName, value=filesInRootOfFileName
                    filesInFolder=filesListWithBugFixedCommitsDict[fileName]
                    bugFixedCommitFileDir=  os.path.dirname(os.path.dirname(__file__)) + '/util/Python/'+self.projectName.lower()+"/"+ fileName.split("@")[0] +"/"+fileName
                    bugFixedCommitIndexInItsFolder=filesInFolder.index(bugFixedCommitFileDir)
                      
                    for fileInTheFolder in filesInFolder:
                            fileIndex = filesInFolder.index(fileInTheFolder)
                        #if (bugFixedCommitIndexInItsFolder-fileIndex<=3) and (bugFixedCommitIndexInItsFolder-fileIndex>=0):
                            dataClassSmellDict=smell.checkForDataClass(fileInTheFolder, self.projectName)
                            if dataClassSmellDict:
                                for k, v in dataClassSmellDict.items():
                                        #if str(v['isPIHSmell'])=="True":
                                    #fileIndex = filesInFolder.index(fileInTheFolder)
                                    rootName = fileInTheFolder.split("@")[0] 
                                    dataClassSmellRelationAnalysisCSVoutList.append([fileName.split('@')[1], fileInTheFolder,k,str(v['wmc']),str(v['lcom']),str(v['isDataClass']), str(fileIndex),str(bugFixedCommitIndexInItsFolder) ,str(len(filesInFolder)), rootName])
                                    
                                
                dataClassSmellRelationAnalysisCSVoutList=self.checkForDuplicatesInListsofList(dataClassSmellRelationAnalysisCSVoutList)
                for analysis in dataClassSmellRelationAnalysisCSVoutList:
                    relationAnalysisDataClassSmellCSVout.writerow(analysis)
                print("Data class bad smell analysis for "+projectName +" is done!")
        except Exception as ex:
            print(ex)
            print("Exception occurred in Relation.analyzeDataClassSmell() method")                             


    def checkForRelation(self):
        try:
             
            smell=BS.BadSmell()
             
            projectPath = os.path.dirname(os.path.dirname(__file__)) + '/util/Analysis/SemanticVsSyntacticAnalysis'
            csvfile = 'SemanticVsSyntacticAnalysisOf'+self.projectName+'.csv'
            '''
                buggedCommits=['Issue ID', 'Issue Body','issue User', 'commitID','Commit Subject',"Semantic Confidence Level","Syntactic Confidence Level"]
            '''
             
            buggedCommitsList = self.fileOp.readCSVFile(os.path.join(projectPath, csvfile))
               
            folderDirs = os.path.dirname(os.path.dirname(__file__)) + '/util/Python/'+self.projectName.lower()
            modifiedFileListDict = self.getModifiedFilesFromProject(folderDirs)  # key is the file itself and the value is the commit id on the file name,  # 14885 files modified
 
            commitIDList = self.getcommitIDsFromSyntacticvsSemanticAnalysisFile(buggedCommitsList)  # this has commitID on the analysis csv file, # 2862 commits
            commitIDList = list(set(commitIDList))
             
            possibleChoices = []  
            possibleChoices=np.array([file for file, commitIDInFile in modifiedFileListDict.items() for commitID in commitIDList if commitID in commitIDInFile])
        
                 
            possibleChoices = list(set(possibleChoices))  
          
                  
            filesListWithBugFixedCommitsDict = {} #337 files that have bug fixed commit IDs
            for each in possibleChoices:
                rootName = os.path.dirname(os.path.dirname(__file__)) + '/util/Python/'+self.projectName.lower()+"/"+ each.split("@")[0]
                filesListWithBugFixedCommitsDict[each] = self.checkFilesWithinRoot(rootName)
             
            #self.analyzeLargeClassSmell(filesListWithBugFixedCommitsDict, self.projectName,projectPath,smell)
            #self.analyzeLongParameterClassSmell(filesListWithBugFixedCommitsDict, self.projectName, projectPath, smell)
            #self.analyzeMessageChainsSmell(filesListWithBugFixedCommitsDict, self.projectName, projectPath, smell)
            #self.analyzeParallelInheritanceHiearchySmell(filesListWithBugFixedCommitsDict, self.projectName, projectPath, smell)
            #self.analyzeLazyClassSmell(filesListWithBugFixedCommitsDict, self.projectName, projectPath, smell)
            self.analyzeDataClassSmell(filesListWithBugFixedCommitsDict, self.projectName, projectPath, smell)
                                                                      
            print("Checking for Relation between smells and defects for "+self.projectName+" is done")
        except Exception as ex:
            print(ex)
            print("Exception occurred in Relation.checkForRelation() method")                             

    

#fileName="/Users/neda/OneDrive - Auburn University/PhDworkspace/BadSmells/util/Python/numpy/misc_util/misc_util@cba01fd50@Thu Feb 2 03:29:38 2006 +0000.py"
#fileName="/Users/neda/OneDrive - Auburn University/PhDworkspace/BadSmells/util/Python/numpy/core/core@77f95a139@Mon Dec 1 17:56:58 2008 +0000.py"
# #fileName="/Users/neda/OneDrive - Auburn University/PhDworkspace/BadSmells/util/Python/numpy/system_info/system_info@5082215ea@Mon Apr 1 23:28:37 2002 +0000.py"
# projectName="keras"   
# relation=Relation(projectName)   
# relation.checkForRelation()  




