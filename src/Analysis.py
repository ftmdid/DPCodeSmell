'''
Created on Aug 5, 2019

@author: auresearchlab
'''
import re
import os
import FileOperations as FO
import csv
import SemanticAnalysis as SC

class Analysis(object):
    '''
    classdocs
    '''


    def __init__(self,projectName):
        '''
        Constructor
        '''
        self.projectName=projectName
        self.fileOp=FO.FileOperations(self.projectName)
        self.similiarityAnalysis=SC.SemanticAnalysis(self.projectName)
        
    
    """
        The syntactic confidence level is always an integer number between 0 and 2. 
        We initially assign a syntactic confidence syn of zero and raise the confidence
        by one for each of the following conditions that is met:
            1. The number is a bug number
            2. The log message contains a keyword or the log message contains only plain or bug numbers 
    """    
    def makeSyntacticSubjectAnalysis(self, subject):
        confidenceLevel = 0
        if self.isBugNumber(subject):
            confidenceLevel +=1
        if self.isKeywords(subject) or self.isPlainNumber(subject) or self.isWordAlphaNum(subject):
            confidenceLevel += 1
        print("Done with syntactic analysis")
        return confidenceLevel
        
    def isWordAlphaNum(self, subject):
        pattern = re.compile("[a-zA-Z0-9]+$")
        matched=False
        if not (' ' in subject):
            matched = bool(pattern.match(subject))
        return matched
    
            
    def isPlainNumber(self, subject):
        subjectList = re.sub(r'[^\w\s]','',subject).split(' ')
        myNewList = [s for s in subjectList if s.isdigit()]
        if set(subjectList) == set(myNewList):
            return True
        else:
            return False
    
    def isKeywords(self, subject):
        subject=subject.lower()
        p = re.compile(r'fix(e[ds])? | bug(s)? | defect(s)? | patch ')
        matched=False
        if p.search(subject):
            matched=True

        return matched
        
    def isBugNumber(self, subject):
        subject=subject.lower()
        #p = re.compile('bug[# \t]*[0-9]+ | bug?id=[0-9]+ | \[[0-9]+\]')
        pattern = re.compile('bug[\#?]*[0-9]+ | bug *?[0-9]+ | [bug]? *?id *?= *?[0-9]+ | \[*[0-9]+\]*')
        matched=False
        if re.search(pattern, subject):
            matched=True
        return matched
    
   

    def makeSemanticAnalysis(self):
        #self.similiarityAnalysis.calculateSimiliaritiesBetweenIssueAndCommits()
        projectPath = os.path.dirname(os.path.dirname(__file__))+ '/util'  
        
        #similiarClosedBugIssues=os.path.join(projectPath, 'Analysis/similiarities/similiaritiesOf'+self.projectName+".csv")
        commitsPath=os.path.join(projectPath, 'commits/commitsOf'+self.projectName+".csv")
         
        '''
            similiarClosedBugIssues returns similiar issues that has cosine similiarity GT 0.5
            The list has [issueID, issueBody, issueUser,commitID, CommitSubject, cosineSimiliarity, LevensteinDistance]
        '''
        #similiarClosedBugIssuesList=self.fileOp.readCSVFile(similiarClosedBugIssues) 
       
        # The commitsList has [commitID, parentID, AuthorName, AuthorEmail,AuthorDate,committerName,committerEmail, committerDate, Subject, logSize]
        commitsList= self.fileOp.readCSVFile(commitsPath)
        
        projectPath = os.path.dirname(os.path.dirname(__file__))+ '/util/Analysis/SemanticAnalysis'   
        csvfile='semanticAnalysisOf'+self.projectName+".csv"
        csvout = csv.writer(open(os.path.join(projectPath,csvfile), 'w+'))
        print("The CSV file for semantic analysis has been created!")
        csvout.writerow(['commitID','Commit Subject','Issue ID', 'Issue Title','issue User',"Semantic Confidence Level"])
        semanticConfValue=0
       
       
        issuesPath=os.path.dirname(os.path.dirname(__file__))+'/util/issues/issues/issuesOf'+self.projectName+'.csv'
        ''' 
                issuesList=[id, Title,Body,User,Label, Created At, Updated At]
        '''
        issuesList = self.fileOp.readCSVFile(issuesPath)
        closedBugIssuesList=self.similiarityAnalysis.filterIssueFile(issuesList,os.path.join(os.path.dirname(os.path.dirname(__file__))+ '/util'))[1]
        #closedBugRelatedIssues = self.fileOp.readCSVFile(filteredIssuesList)#[id, title, body, user, label, created at, updated at]
       
        for commit in commitsList:
#             for each in similiarClosedBugIssuesList:
            for i in range(len(closedBugIssuesList)):
                #if commit[2]==each[2]: # the author of the change log message has been assigned to bug
                if commit[2]==closedBugIssuesList[i][3]: 
#                     if each[1] in commit[8]: # the short description of bug report in issue tracking system is contained in change log message
                    if closedBugIssuesList[i][1] in commit[8]:
                        #semanticConfValue =3 # this is 3 because the issue is closed and labeled as bug
                        semanticConfValue =2
                    else:
                        #semanticConfValue =2  # this is 3 because the issue is closed and labeled as bug and bug vs commits are similiar
                        semanticConfValue =1
                if closedBugIssuesList[i][1].lower() in commit[8].lower():
                    if commit[2]==closedBugIssuesList[i][3]: 
                        semanticConfValue =2
                    else:
                        semanticConfValue =1
                else:
                    semanticConfValue=0
                if semanticConfValue>0:
                    csvout.writerow([commit[0],commit[8],closedBugIssuesList[i][0],closedBugIssuesList[i][1],closedBugIssuesList[i][3], semanticConfValue])
#                 
#                 csvout.writerow([commit[0],commit[8],each[0],each[1],each[2], semanticConfValue])   
               
        print("Done with semantic analysis")
        
    def makeSemanticAndSyntacticAnalysis(self):
        
        self.makeSemanticAnalysis()
        
        projectPath = os.path.dirname(os.path.dirname(__file__))+ '/util/Analysis'
        semanticAnalysisFilePath=os.path.join(projectPath,'SemanticAnalysis/semanticAnalysisOf'+self.projectName+".csv")
        
        
        '''semanticAnalysisList returns ['Issue ID', 'Issue Title','issue of User', 'commitID','Commit Subject',"Semantic Confidence Level"]'''
        semanticAnalysisList=self.fileOp.readCSVFile(semanticAnalysisFilePath)
        
        csvfile='SemanticVsSyntacticAnalysis/SemanticVsSyntacticAnalysisOf'+self.projectName+".csv"
        csvout = csv.writer(open(os.path.join(projectPath,csvfile), 'w+'))
        csvout.writerow(['commitID','Commit Subject','Issue ID', 'Issue Title','issue User',"Semantic Confidence Level","Syntactic Confidence Level"]) 
        resultsList=[]
        
        #'commitID','Commit Subject','Issue ID', 'Issue Body','issue User',"Semantic Confidence Level"
        for each in semanticAnalysisList:
            syntacticConfidenceLevel=self.makeSyntacticSubjectAnalysis(each[1])
            if int(each[5])>1 or (int(each[5])==1 and int(syntacticConfidenceLevel)>0):
                result=[each[0],each[1],each[2],each[3],each[4],each[5],syntacticConfidenceLevel]
                if not result in resultsList:
                    csvout.writerow([each[0],each[1],each[2],each[3],each[4],each[5],syntacticConfidenceLevel])
        print("Done with semantic and syntactic Analysis")
        
        

#projectName='django'
#analysis=Analysis(projectName)
# analysis.makeSemanticAndSyntacticAnalysis()
  
 
    