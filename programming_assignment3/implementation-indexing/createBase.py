from datetime import datetime
from functions import HTMLFilesList,HTMLContent,getTokens,createDatabase,tokensToDatabase,positionsToDatabase,tokenPositions,snippetsToDatabase
from bs4 import BeautifulSoup
import argparse

startTime=datetime.now()

parser = argparse.ArgumentParser()
parser.add_argument("--path", help="Path to the dataset", required=True, action='store')
args = parser.parse_args()
databaseDir=args.path

fileList=HTMLFilesList(databaseDir)

createDatabase()

for i in fileList:

    print("Processing: ",i)
    fileContent = HTMLContent(i)
    
    soup = BeautifulSoup(fileContent, 'html.parser')
    fileContentWithoutHTML=soup.get_text(separator=" ")
    
    #tokenisation of text
    #includes converting to lowercase, tokenisation, ekstracting unique tokens, removing stop words, short words, numvbers and dates
    fileTokens = getTokens(fileContentWithoutHTML)

    #writing unique tokens to database
    tokensToDatabase(fileTokens)

    #determing token positions in text and creating snippets    
    positions,snippets=tokenPositions(fileTokens,fileContentWithoutHTML,i)

    #writing tokoen positions to database 
    positionsToDatabase(databaseDir,positions)

    #writing snippets to database
    snippetsToDatabase(databaseDir,snippets)

endTime=datetime.now()
print("Database created in:",endTime-startTime,"hh:mm:ss.ms")
