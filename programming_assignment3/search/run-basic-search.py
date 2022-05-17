from functions import HTMLFilesList,HTMLContent,getTokens,offset,printDBData
from bs4 import BeautifulSoup
from nltk.tokenize import word_tokenize
import argparse
import time

parser = argparse.ArgumentParser()
parser.add_argument("--query", help="String for query", required=True, action='store')
parser.add_argument("--path", help="Path to the dataset", required=True, action='store')
args = parser.parse_args()
query=args.query
datasetPath=args.path

tokenizedQuery=getTokens(query)

print("\n\nResults for a query: ", query)

start=time.time()

fileList=HTMLFilesList(datasetPath)

datasetData=[]
for i in range(len(fileList)):
    fileContent = HTMLContent(fileList[i])
    soup = BeautifulSoup(fileContent, 'html.parser')
    fileContentWithoutHTML=soup.get_text(separator=" ")
    fileTokens=word_tokenize(fileContentWithoutHTML)

    for j in tokenizedQuery:
        positions =[k for k in range(len(fileTokens)) if fileTokens[k].lower().strip()==j.lower()]
        if positions:
            snippets=[]
            for l in positions:
                oneSnippet=" ".join(fileTokens[l:l+offset])
                snippets.append(oneSnippet)
            datasetData.append([[fileList[i].replace(datasetPath+"\\",'')],[j],positions,snippets,len(positions)])

datasetData.sort(key=lambda row: (row[4]), reverse=True)

stop=time.time()
querytime = stop-start
print("Results found in:",round(querytime*1000), "ms")


printDBData(datasetData,tokenizedQuery)




