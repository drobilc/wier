from datetime import datetime
from functions import HTMLFilesList,HTMLContent,getTokens,createDatabase,tokensToDatabase,positionsToDatabase,tokenPositions,snippetsToDatabase
from bs4 import BeautifulSoup
import argparse

zacetek=datetime.now()

parser = argparse.ArgumentParser()
parser.add_argument("--path", help="Path to the dataset", required=True, action='store')
args = parser.parse_args()
databaseDir=args.path

fileList=HTMLFilesList(databaseDir)

createDatabase()

for i in fileList:

    print("In prograss: ",i)
    fileContent = HTMLContent(i)
    
    soup = BeautifulSoup(fileContent, 'html.parser')
    fileContentWithoutHTML=soup.get_text(separator=" ")

    """
    #Samo zapise vsebino brez HTML v datoteko, da lahko potem preverjam, če je izpis OK
    ime=i+".txt"
    print(ime)
    fe=codecs.open(ime, 'w','utf-8')
    fe.write(fileContentWithoutHTML)
    """
    
    fileTokens = getTokens(fileContentWithoutHTML)

    tokensToDatabase(fileTokens)

    positions,snippets=tokenPositions(fileTokens,fileContentWithoutHTML,i)
    positionsToDatabase(databaseDir,positions)
    snippetsToDatabase(databaseDir,snippets)

konec=datetime.now()
print(zacetek)
print(konec)
