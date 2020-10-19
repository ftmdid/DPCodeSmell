'''
Created on Jun 26, 2020

@author: neda
'''

import os
import csv
from collections import Counter
import re
import sys
import math
import string
from Levenshtein import distance
import src.FileOperations as FO


import nltk, string
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

stemmer = nltk.stem.porter.PorterStemmer()
remove_punctuation_map = dict((ord(char), None) for char in string.punctuation)

def stem_tokens(tokens):
    stopWords= set(stopwords.words('english'))
    lowered= [word.lower()for word in tokens]
    removedStopWords= [r for r in lowered if not r in stopWords]
    lemmatizer=WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(word) for word in removedStopWords]
    return [stemmer.stem(item) for item in tokens]

'''remove punctuation, lowercase, stem'''
def normalize(text):
    return stem_tokens(nltk.word_tokenize(text.lower().translate(remove_punctuation_map)))




#vectorizer = TfidfVectorizer(tokenizer=normalize, stop_words='english')
vectorizer = TfidfVectorizer(tokenizer=normalize, stop_words=None)


def cosine_sim(text1, text2):
    tfidf = vectorizer.fit_transform([text1, text2])
    return ((tfidf * tfidf.T).A)[0,1]


class SemanticAnalysis(object):
    '''
    classdocs
    '''


    def __init__(self,projectName):
        '''
        Constructor
        '''
        self.projectName=projectName
        self.fileOp=FO.FileOperations(self.projectName)
    
    '''
    get_jaccord_sim method is referenced from:
    https://towardsdatascience.com/overview-of-text-similarity-metrics-3397c4601f50
    '''
    def get_jaccord_sim(self,str1, str2):
        a= set(str1.split())
        b= set(str2.split())
        c=a.intersection(b)
        return float(len(c))/(len(a)+len(b)-len(c))
    
    '''
        getCosine and textToVector functions are from:
        https://stackoverflow.com/questions/15173225/calculate-cosine-similarity-given-2-sentence-strings
    '''
           
    def getCosine(self,vec1, vec2):
        intersection = set(vec1.keys()) & set(vec2.keys())
        numerator = sum([vec1[x] * vec2[x] for x in intersection])
            
        sum1 = sum([vec1[x] ** 2 for x in list(vec1.keys())])
        sum2 = sum([vec2[x] ** 2 for x in list(vec2.keys())])
        denominator = math.sqrt(sum1) * math.sqrt(sum2)
            
        if not denominator:
            return 0.0
        else:
            return float(numerator) / denominator
            
            
    def textToVector(self,text):
        WORD = re.compile(r"\w+")
        words=WORD.findall(text)
    #   return Counter(words)
                
        noPunct = [word for word in words if word not in string.punctuation]
        lowered= [word.lower()for word in noPunct]
        stopWords= set(stopwords.words('english'))
        removedStopWords= [r for r in lowered if not r in stopWords]
        lemmatizer=WordNetLemmatizer()
        lemmatizedWords = [lemmatizer.lemmatize(word) for word in removedStopWords]
        return Counter(lemmatizedWords)
        #return Counter(noPunct)
       
    '''
        Code is referenced from: 
        https://stackoverflow.com/questions/15063936/csv-error-field-larger-than-field-limit-131072
    '''
    def increaseCSVReaderSize(self):
        maxInt = sys.maxsize
        try:
            csv.field_size_limit(maxInt) # for overflow csv error
        except OverflowError:
            maxInt = int(maxInt / 10)

     
    def filterIssueFile(self,issuesList,projectPath):    
    #     increaseCSVReaderSize()
        filteredIssueFilePath=os.path.join(projectPath,'issues/filtered/filteredIssuesOf'+self.projectName+'.csv')
        filteredIssueFile = csv.writer(open(filteredIssueFilePath,'w+'))
        filteredIssueFile.writerow(('id', 'Title', 'Body',"User", 'Label','Created At', 'Updated At'))
        for i  in range(0,len(issuesList)):
            if ('bug') in issuesList[i][4].lower() or (('bug') in issuesList[i][1].lower()) or (('bug') in issuesList[i][2].lower()):
                filteredIssueFile.writerow(issuesList[i])
        return filteredIssueFilePath
    
    def calculateSimiliaritiesBetweenIssueAndCommits(self):
        projectPath = os.path.join(os.path.dirname(os.path.dirname(__file__))+ '/util')
    
        issuesPath=os.path.join(projectPath, 'issues/issues/issuesOf'+self.projectName+'.csv')
    
        logsPath=os.path.join(projectPath, 'commits/commitsOf'+self.projectName+'.csv')
        
        try:
            
            issuesList=[]
            ''' 
                issuesList=[id, Title,Body,User,Label, Created At, Updated At]
            '''
            issuesList = self.fileOp.readCSVFile(issuesPath)
            issuesList = self.fileOp.readCSVFile(self.filterIssueFile(issuesList,projectPath))
            
                
            commitsList=[]
            '''
                commitsList=[commitID, parentID, Author Name, Author Date, committer Name, commiter Email, committer Date, Subject, log size]
            '''
            commitsList=self.fileOp.readCSVFile(logsPath)
            
            projectPath = os.path.dirname(os.path.dirname(__file__))+ '/util/Analysis/similiarities'   
            csvfile='similiaritiesOf'+self.projectName+'.csv'
            csvout = csv.writer(open(os.path.join(projectPath,csvfile), 'w+'))
            csvout.writerow(['Issue ID', 'Issue Body','issue User', 'commitID','Commit Subject',"cosine similiarity", "Levenstein Distance","cosine similiarity2"]) 
                
          
            import datetime
            begin_time = datetime.datetime.now() 
            print(begin_time)
            
            #for i in range(0,len(issuesList)): #446 issues in total in django
            for i in range(0,50):
                bodyInIssue=issuesList[i][1]  #title not body  
             
                vectorForIssue=self.textToVector(str(bodyInIssue).lower())
               
                #for j in range(0,len(commitsList)): #28840 commits in total in django
                for j in range(0,100):
                    subjectInCommit=commitsList[j][8]
                
                    vectorForCommit =self.textToVector(str(subjectInCommit).lower())
                    cosineSimiliarity=self.getCosine(vectorForIssue, vectorForCommit)  
                    levensteinDistance= distance(bodyInIssue, subjectInCommit)
                    
                
                     
                    #print("issue number: "+str(i))
                    cosineSimiliarity2=(cosine_sim(bodyInIssue, subjectInCommit))
                    csvout.writerow([issuesList[i][0],issuesList[i][1],issuesList[i][3],commitsList[j][0],commitsList[j][8], cosineSimiliarity,levensteinDistance, cosineSimiliarity2])
#                    
#                     if cosineSimiliarity>=0.5 or cosineSimiliarity2>=0.5:
#                         print("Cosine Similiarity: " +str(cosineSimiliarity))
#                         print("Issue number: "+str(i), "--->","Commit number: "+str(j))
#                         csvout.writerow([issuesList[i][0],issuesList[i][1],issuesList[i][3],commitsList[j][0],commitsList[j][8], cosineSimiliarity,levensteinDistance,cosineSimiliarity2])
#                      
            endTime=datetime.datetime.now()
            executionTime=endTime - begin_time
            print(executionTime)
            print("Similiarity between Commits and Issues are calculated,Done!")
            
        except FileNotFoundError or TypeError as ex:
            print(ex)
        