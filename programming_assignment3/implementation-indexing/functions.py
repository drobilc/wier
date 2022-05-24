import os
import codecs
from nltk.tokenize import word_tokenize
from stopwords import stop_words_slovene
import sqlite3
from datetime import datetime
import re

offset=4


def isDate(datum):
    try:
        date_object = datetime.strptime(datum, "%d.%m.%Y")
        return True
    except:
        pass
    
    try:
        date_object = datetime.strptime(datum, "%m/%d/%Y")
        return True
    except:
        pass

    try:
        date_object = datetime.strptime(datum, "%d/%m/%Y")
        return True
    except:
        pass

    return False



def isNumber(stevilka):
    prog=re.compile("[0-9]+[,][0-9]+")
    isNum=bool(prog.match(stevilka))

    try:
        float(stevilka)
        return True
    except:
        pass
    
    return isNum



def HTMLFilesList(direktorij):
    direcotriesList=[]
    filesList=[]
    direcotriesList.append(direktorij)
    i=0
    while i<len(direcotriesList):
        for filename in os.listdir(direcotriesList[i]):
            f = os.path.join(direcotriesList[i], filename)
            if os.path.isdir(f):
                direcotriesList.append(f)
        i=i+1

    for i in direcotriesList:
        for filename in os.listdir(i):
            f = os.path.join(i, filename)
            file_name, file_extension = os.path.splitext(f)
            if file_extension==".html" or file_extension==".htm":
                filesList.append(f)

    return filesList



def HTMLContent(pot):
    f=codecs.open(pot, 'r','utf-8')
    content=f.read()
    return content



def getTokens(content):
    content=content.lower()
    tokens=word_tokenize(content)
    newTokens=[]
    for i in tokens:
        if i not in newTokens:
            newTokens.append(i.strip())

    clearedTokens=[]
    for i in newTokens:
        if i not in stop_words_slovene and len(i)>2 and not i.isnumeric() and not isDate(i) and not isNumber(i):
            clearedTokens.append(i)

    return clearedTokens



def createDatabase():
    conn = sqlite3.connect('inverted-index.db')
    c = conn.cursor()
    try:
        c.execute('''
            CREATE TABLE IndexWord (
                word TEXT PRIMARY KEY
            );
        ''')
    except:
        pass

    try:
        c.execute('''
            CREATE TABLE Posting (
                word TEXT NOT NULL,
                documentName TEXT NOT NULL,
                frequency INTEGER NOT NULL,
                indexes TEXT NOT NULL,
                PRIMARY KEY(word, documentName),
                FOREIGN KEY (word) REFERENCES IndexWord(word)
            );
        ''')
    except:
        pass

    try:
        c.execute('''
            CREATE TABLE Snip (
                documentName TEXT NOT NULL,
                word TEXT NOT NULL,
                posIndex INTEGER NOT NULL,
                snippet TEXT NOT NULL,
                PRIMARY KEY(documentName,word,posIndex),
                FOREIGN KEY (word) REFERENCES IndexWord(word)
            );
        ''')
    except:
        pass

    conn.commit()
    conn.close()



def tokensToDatabase(tokensList):
    conn = sqlite3.connect('inverted-index.db')
    c = conn.cursor()

    for i in tokensList:
        try:
            c.execute("INSERT INTO IndexWord VALUES('"+i.replace("'"," ").strip()+"')")
        except:
            pass

    conn.commit()
    conn.close()



def positionsToDatabase(databaseDir,positions):
    conn = sqlite3.connect('inverted-index.db')
    c = conn.cursor()

    for i in positions:
        try:
            c.execute("INSERT INTO Posting VALUES ('"+i[0].replace("'"," ").strip()+"', '"+i[1].replace(databaseDir+"\\",'')+"', "+str(i[2])+", '"+i[3]+"');")
        except:
            pass
    
    conn.commit()
    conn.close()



def tokenPositions(fileTokens,fileContentWithoutHTML,fileName):
    allTokens=word_tokenize(fileContentWithoutHTML)
    positionsForDB=[]
    snippetsForDB=[]

    for element in fileTokens:
        positions = l=[i for i in range(len(allTokens)) if allTokens[i].lower().strip()==element.lower()]
        listForDB=','.join(str(e) for e in positions)
        oneRecord=[element,fileName,len(positions),listForDB]
        positionsForDB.append(oneRecord)
        for j in positions:
            enSnpiet=[fileName,element.lower(),j," ".join(allTokens[j:j+offset])]
            snippetsForDB.append(enSnpiet)
    
    return positionsForDB, snippetsForDB



def snippetsToDatabase(zacetniDirektorij,snipeti):
    conn = sqlite3.connect('inverted-index.db')
    c = conn.cursor()

    for i in snipeti:
        try:
            c.execute("INSERT INTO Snip VALUES ('"+i[0].replace(zacetniDirektorij+"\\",'')+"','"+i[1].replace("'"," ").strip()+"','"+str(i[2])+"','"+i[3].replace("'"," ").strip()+"');")
        except:
            pass
    
    conn.commit()
    conn.close()

    
def dataFromDatabase(poizvedba, database):
    
    conn = sqlite3.connect(database)
    c = conn.cursor()
    queryResukts=[]

    SQLquery="Posting.word='"+"' or Posting.word='".join(poizvedba)+"'"

    try:
        c.execute('''SELECT Posting.*, GROUP_CONCAT(Snip.posIndex,';;'), GROUP_CONCAT(Snip.snippet,';;') 
                     FROM Posting 
                     LEFT JOIN Snip ON Posting.documentName=Snip.documentName 
                     WHERE ('''+SQLquery+''') AND Posting.word=Snip.word AND Posting.documentName=Snip.documentName 
                     GROUP BY Posting.documentName,Posting.frequency,Posting.indexes,Posting.word 
                     ORDER BY frequency DESC''')
    except:
        print("Data table does not exist.")
        conn.close()
        quit()
    rows = c.fetchall()
    for row in rows:
        positions=row[4].split(';;')
        snippets = [int(i) for i in positions]
        senekej=row[5].split(";;")
        snippetsList=list(senekej)
        queryResukts.append([[row[1]],[row[0]],snippets,snippetsList,row[2]])

    conn.commit()
    conn.close()

    return queryResukts
    
def printDBData(dataFromDB,tokenizedQuery):

    zdruzeni=[]
    for i in  dataFromDB:
        if i[0] not in [j[0] for j in zdruzeni]:
            zdruzeni.append(i)
        else:
            indeks=[j[0] for j in zdruzeni].index(i[0])
            zdruzeni[indeks][1]=zdruzeni[indeks][1]+i[1]
            zdruzeni[indeks][2]=zdruzeni[indeks][2]+i[2]
            zdruzeni[indeks][3]=zdruzeni[indeks][3]+i[3]
            zdruzeni[indeks][4]=zdruzeni[indeks][4]+i[4]

    for i in zdruzeni:
        i.append([])
        i.append([])
        i[6]=[len(i[1])]
        counter=0
        while counter<len(i[2]):
            a=[j for j in i[2] if j<i[2][counter]+offset and j>i[2][counter]-offset and j!=i[2][counter]]
            i[5].append(len(a))
            zacetni=i[2][counter]
            koncni=i[2][counter]+offset-1
            for z in a:
                indeks=i[2].index(z)
                if z > zacetni:
                    if z+offset-1>koncni:
                        zam=abs(z-koncni)+1
                        last_word = i[3][indeks].split()[zam::]
                    else:
                        zam=0
                        last_word=""
                    koncni=koncni+abs(zam)
                    i[3][counter]=i[3][counter] + " " + " ".join(last_word)
                else:
                    zam=zacetni-z
                    zacetni=zacetni-zam
                    first_word = i[3][indeks].split()[0:zam]
                    i[3][counter]= " ".join(first_word)+" "+i[3][counter]
                i[3].pop(indeks)
                i[2].remove(z)
            counter=counter+1

    zdruzeni.sort(key=lambda row: (row[6]), reverse=True)

    for i in zdruzeni:
        list1, list2 = (list(t) for t in zip(*sorted(zip(i[5], i[3]), reverse=True)))
        i[5]=list1
        i[3]=list2

    print("\nFrequency".ljust(11), "Keywords".ljust(len("   ".join(tokenizedQuery))+5), "Document".ljust(50), "Snippets".ljust(100))
    line="-"*200
    print(line)
    for i in zdruzeni:
        print(str(i[4]).ljust(11), " + ".join(i[1]).ljust(len("   ".join(tokenizedQuery))+5), (i[0][0]).ljust(50), " ... ".join(i[3])[0:100].ljust(100))
