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
      
    
    def getModifiedFiles(self,folderDirs):
        modifiedFileListDict={}
        for _, _, files in os.walk(folderDirs):
            for file in files:
                if file.endswith('py'):
                    modifiedFileListDict[file] = self.find_between(file, "@", "@")
        return modifiedFileListDict
    
    
    def getcommitIDsFromSyntacticvsSemanticAnalysisFile(self,buggedCommitsList):
        commitIDList=[]
        for each in buggedCommitsList:
            commitID = each[3]
            commitIDList.append(commitID)
        
        return commitIDList
    
    def checkForDuplicatesInListsofList(self,listToBeChecked):
        listToBeChecked=list(k for k,_ in itertools.groupby(listToBeChecked))
        return listToBeChecked
    
    
    def checkForRelation(self):
        try:
            
            smell=BS.BadSmell()
            
            projectPath = os.path.dirname(os.path.dirname(__file__)) + '/util/Analysis'
            csvfile = 'SemanticVsSyntacticAnalysisOf'+self.projectName+'.csv'
            '''
                buggedCommits=['Issue ID', 'Issue Body','issue User', 'commitID','Commit Subject',"Semantic Confidence Level","Syntactic Confidence Level"]
            '''
            
            folderDirs = os.path.dirname(os.path.dirname(__file__)) + '/util/Python/'+self.projectName.lower()
            buggedCommitsList = self.fileOp.readCSVFile(os.path.join(projectPath, csvfile))
        
           
            relationAnalysisLargeClassCSVfile = os.path.dirname(os.path.dirname(__file__)) + '/util/Analysis/BadSmells/LargeClassRelationAnalysisOf'+self.projectName+'.csv'
            relationAnalysisLargeClassCSVout = csv.writer(open(os.path.join(projectPath, relationAnalysisLargeClassCSVfile), 'w+'))
            relationAnalysisLargeClassCSVout.writerow(('CommitID' ,'File Name','Class Name' ,'isLargeClass', 'Index of File In Folder', 'Index of Bug Fixed Commit In File',"Number of Files In Folder", "Folder"))
      
            
            relationAnalysisLongParameterListCSVfile = os.path.dirname(os.path.dirname(__file__)) + '/util/Analysis/BadSmells/LongParameterListRelationAnalysisOf'+self.projectName+'.csv'
            relationAnalysisLongParameterListCSVout = csv.writer(open(os.path.join(projectPath, relationAnalysisLongParameterListCSVfile), 'w+'))
            relationAnalysisLongParameterListCSVout.writerow(('CommitID', 'File Name','Method Name' ,'isLongParameterList', 'Index of File In Folder','Index of Bug Fixed Commit In File', "Number of Files In Folder", "Folder"))
      
           
    
            relationAnalysisMessageChainCVoutListCSVfile = os.path.dirname(os.path.dirname(__file__)) + '/util/Analysis/BadSmells/MessageChainRelationAnalysisOf'+self.projectName+'.csv'
            relationAnalysisMessageChainCVoutListCSVout = csv.writer(open(os.path.join(projectPath, relationAnalysisMessageChainCVoutListCSVfile), 'w+'))
            relationAnalysisMessageChainCVoutListCSVout.writerow(('CommitID', 'File Name','Message Chain Line' ,'isMessageChain', 'Index of File In Folder','Index of Bug Fixed Commit In File', "Number of Files In Folder", "Folder"))
     
           
           
            modifiedFileListDict = self.getModifiedFiles(folderDirs)  # key is the file itself and the value is the commit id on the file name,  # 14885 files modified
           
          
            commitIDList = self.getcommitIDsFromSyntacticvsSemanticAnalysisFile(buggedCommitsList)  # this has commitID on the analysis csv file, # 2862 commits
           
           
            
            possibleChoices = [] # possibleChoices list is to find the files that have bug fixed commits
            for commitID in commitIDList:
                for file, commitIDInFile in modifiedFileListDict.items():  # file refers to key and commitIDInFile refers to value of dictionary
                    if commitID in commitIDInFile:
                        possibleChoices.append(file)
                        
                
            possibleChoices = list(set(possibleChoices))     #337 files that have bug fixed commit IDs   
            
                 
            filesListWithBugFixedCommitsDict = {} #337 files that have bug fixed commit IDs
            for each in possibleChoices:
                rootName = os.path.dirname(os.path.dirname(__file__)) + '/util/Python/'+self.projectName.lower()+"/"+ each.split("@")[0]
                filesListWithBugFixedCommitsDict[each] = self.checkFilesWithinRoot(rootName)
                 
            
          
            
            longParameterListDict={}
            fileIndex = 0
            largeClassRelationAnalysisCSVoutList=[]
            longParameterListRelationAnalysisCSVoutList=[]
            messageChainRelationAnalysisCVoutList=[]
            #for fileName, filesInRootOfFileName in filesListWithBugFixedCommitsDict.items():  # key=fileName, value=filesInRootOfFileName
            for fileName in filesListWithBugFixedCommitsDict.keys():  # key=fileName, value=filesInRootOfFileName
                
                filesInFolder=filesListWithBugFixedCommitsDict[fileName]
                bugFixedCommitFileDir=  os.path.dirname(os.path.dirname(__file__)) + '/util/Python/'+self.projectName.lower()+"/"+ fileName.split("@")[0] +"/"+fileName
                bugFixedCommitIndexInItsFolder=filesInFolder.index(bugFixedCommitFileDir)
                largeClassDict = {}
                messageChainDict={}
                for fileInTheFolder in filesInFolder:
                    #print(fileInTheFolder)
                    
                    largeClassDict = smell.checkForLargeClass(fileInTheFolder)
                    if largeClassDict:
                        for k, v in largeClassDict.items():
                            if str(v['isLargeClass']) == "True":
                                fileIndex = filesInFolder.index(fileInTheFolder)
                                rootName = fileInTheFolder.split("@")[0] 
        #                       commitID=fileName.split('@')[1]
                                largeClassRelationAnalysisCSVoutList.append([fileName.split('@')[1],fileInTheFolder,k, "Yes", str(fileIndex), str(bugFixedCommitIndexInItsFolder) ,str(len(filesInFolder)), rootName])
                                                                     
                for fileInTheFolder in filesInFolder:
                    longParameterListDict=smell.checkForLongParameterList(fileInTheFolder)
                    if longParameterListDict:
                        for k, v in longParameterListDict.items():
                            if str(v['isLongParameterList'])=="True":
                                fileIndex = filesInFolder.index(fileInTheFolder)
                                rootName = fileInTheFolder.split("@")[0] 
                                longParameterListRelationAnalysisCSVoutList.append([fileName.split('@')[1], fileInTheFolder,k,"Yes", str(fileIndex),str(bugFixedCommitIndexInItsFolder) ,str(len(filesInFolder)), rootName])
                 
                for fileInTheFolder in filesInFolder:   
                    messageChainDict= smell.checkForMessageChain(fileInTheFolder)
                    if messageChainDict:
                        for k, v in messageChainDict.items():
                            if str(v["isMessageChain"])=="True":
                                messageChainRelationAnalysisCVoutList.append([fileName.split('@')[1],fileInTheFolder,k, "Yes", str(fileIndex), str(bugFixedCommitIndexInItsFolder) ,str(len(filesInFolder)), rootName])
                                                                      
                                
                    
        
            largeClassRelationAnalysisCSVoutList=self.checkForDuplicatesInListsofList((largeClassRelationAnalysisCSVoutList))
            for analysis in largeClassRelationAnalysisCSVoutList:
                relationAnalysisLargeClassCSVout.writerow(analysis)
                 
            longParameterListRelationAnalysisCSVoutList=self.checkForDuplicatesInListsofList(longParameterListRelationAnalysisCSVoutList)
            for analysis in longParameterListRelationAnalysisCSVoutList:
                relationAnalysisLongParameterListCSVout.writerow(analysis)
     
     
                             
                 
            messageChainRelationAnalysisCVoutList = self.checkForDuplicatesInListsofList(messageChainRelationAnalysisCVoutList)
            for analysis in messageChainRelationAnalysisCVoutList:
                relationAnalysisMessageChainCVoutListCSVout.writerow(analysis)
#                                                                
            print("Done")
        except Exception as ex:
            print(ex)
            print("Exception occurred in Relation.checkForRelation() method")                             
    

    

#fileName="/Users/neda/OneDrive - Auburn University/PhDworkspace/BadSmells/util/Python/numpy/misc_util/misc_util@cba01fd50@Thu Feb 2 03:29:38 2006 +0000.py"
#fileName="/Users/neda/OneDrive - Auburn University/PhDworkspace/BadSmells/util/Python/numpy/core/core@77f95a139@Mon Dec 1 17:56:58 2008 +0000.py"
# #fileName="/Users/neda/OneDrive - Auburn University/PhDworkspace/BadSmells/util/Python/numpy/system_info/system_info@5082215ea@Mon Apr 1 23:28:37 2002 +0000.py"
# projectName="keras"   
# relation=Relation(projectName)   
# relation.checkForRelation()  




