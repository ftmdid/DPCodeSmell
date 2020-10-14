'''
Created on Aug 5, 2019

@author: auresearchlab
'''
import re
import os
import src.FileOperations as FO
import csv
import src.SemanticAnalysis as SC

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
        p = re.compile(r'fix(e[ds])? | bug(s)? | defect(s)? | patch ',flags=re.IGNORECASE | re.VERBOSE)
        matched = p.search(subject)
        return matched
        
    def isBugNumber(self, subject):
        p = re.compile('bug[# \t]*[0-9]+ | pr[# \t]*[0-9]+ | show\_bug.cgi\?id=[0-9]+ | \[[0-9]+\]', flags = re.IGNORECASE | re.X)
        matched = p.search(subject)
        return matched
    
   

    def makeSemanticAnalysis(self):
        self.similiarityAnalysis.calculateSimiliaritiesBetweenIssueAndCommits()
        projectPath = os.path.dirname(os.path.dirname(__file__))+ '/util'  
        
        similiarClosedBugIssues=os.path.join(projectPath, 'Analysis/similiarities/similiaritiesOf'+self.projectName+".csv")
        commitsPath=os.path.join(projectPath, 'commits/commitsOf'+self.projectName+".csv")
         
        '''
            similiarClosedBugIssues returns similiar issues that has cosine similiarity GT 0.5
            The list has [issueID, issueBody, issueUser,commitID, CommitSubject, cosineSimiliarity, LevensteinDistance]
        '''
        similiarClosedBugIssuesList=self.fileOp.readCSVFile(similiarClosedBugIssues) 
       
        # The commitsList has [commitID, parentID, AuthorName, AuthorEmail,AuthorDate,committerName,committerEmail, committerDate, Subject, logSize]
        commitsList= self.fileOp.readCSVFile(commitsPath)
        
        projectPath = os.path.dirname(os.path.dirname(__file__))+ '/util/Analysis/SemanticAnalysis'   
        csvfile='semanticAnalysisOf'+self.projectName+".csv"
        csvout = csv.writer(open(os.path.join(projectPath,csvfile), 'w+'))
        csvout.writerow(['Issue ID', 'Issue Body','issue User', 'commitID','Commit Subject',"Semantic Confidence Level"]) 
      
        
        semanticConfValue=2
        for each in similiarClosedBugIssuesList:
            for commit in commitsList:
                if each[2]==commit[2]:
                    
                    if each[0] in commit[8]:
                        semanticConfValue =3
                    else:
                        semanticConfValue =2 
                    
                    #csvout.writerow([each[0],each[1],each[3],commit[0],commit[8], semanticConfValue])
                    csvout.writerow([each[0],each[1],each[2],commit[0],commit[8], semanticConfValue])

        print("Done with semantic analysis")
        
    def makeSemanticAndSyntacticAnalysis(self):
        
        self.makeSemanticAnalysis()
        
        projectPath = os.path.dirname(os.path.dirname(__file__))+ '/util/Analysis'
        semanticAnalysisFilePath=os.path.join(projectPath,'SemanticAnalysis/semanticAnalysisOf'+self.projectName+".csv")
        
        
        '''semanticAnalysisList returns ['Issue ID', 'Issue Body','issue of User', 'commitID','Commit Subject',"Semantic Confidence Level"]'''
        semanticAnalysisList=self.fileOp.readCSVFile(semanticAnalysisFilePath)
        
        
  
        csvfile='SemanticVsSyntacticAnalysisOf'+self.projectName+".csv"
        csvout = csv.writer(open(os.path.join(projectPath,csvfile), 'w+'))
        csvout.writerow(['Issue ID', 'Issue Body','issue of User', 'commitID','Commit Subject',"Semantic Confidence Level","Syntactic Confidence Level"]) 
      
        for each in semanticAnalysisList:
            syntacticConfidenceLevel=self.makeSyntacticSubjectAnalysis(each[4])
            if int(each[5])>1 or (int(each[5])==1 and int(syntacticConfidenceLevel)>0):
                csvout.writerow([each[0],each[1],each[2],each[3],each[4],each[5],syntacticConfidenceLevel])
        print("Done with Analysis")
        
        
#projectName='Django'
#projectName='django'
# projectName='models'
# analysis=Analysis(projectName)
# analysis.makeSemanticAndSyntacticAnalysis()
#print gt.pullListChangedFiles()
# gt.getChangedFiles()
#print gt.isWordAlphaNum('123abc')
#print gt.isKeywords("Fixed bug 537484: .class file is missing and your code should also have some defects in it. You should fix your patch.")            
#print gt.isPlainNumber("54677, 34555")
#print gt.makeSyntacticAnalysis("Fixed bug 537484: .class file is missing and your code should also have some defects in it. You should fix your patch.")
#print gt.makeSyntacticAnalysis("52264,51529")   
#print gt.makeSyntacticAnalysis("Updated copyrights to 2004")    
 
    