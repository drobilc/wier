from datetime import datetime
from functions import getTokens,dataFromDatabase,printDBData
import argparse
import time

database='inverted-index.db'

start=datetime.now()

parser = argparse.ArgumentParser()
parser.add_argument("--query", help="String for query", required=True, action='store')
parser.add_argument("--dbpath", help="Path to database", required=False, action='store')
args = parser.parse_args()
query=args.query
if args.dbpath is not None:
    database=args.dbpath

print("\n\nResults for a query: ", query)

start=time.time()

tokenizedQuery=getTokens(query)

DBData=dataFromDatabase(tokenizedQuery, database)

if not DBData:
    if len(DBData)<1:
        print("No data available.")
    quit()


stop=time.time()
querytime = stop-start
print("Results found in:",round(querytime*1000), "ms")

printDBData(DBData,tokenizedQuery)


