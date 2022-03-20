import hashlib


def checkForDuplicateFRONTIER(url, db_connection):
    current_site_id = None

    cur = db_connection.cursor()
    try:
        sql_query = "SELECT id FROM crawldb.page WHERE url=%s"
        cur.execute(sql_query, (url,))
        current_site_id = cur.fetchall()
    except Exception as error:
        print("Checking for FRONTIER URL duplicates led to", error)
    return current_site_id


def checkForDuplicateSEED(url, db_connection):
    current_site = None

    cur = db_connection.cursor()
    try:
        sql_query = "SELECT id FROM crawldb.site WHERE domain=%s"
        cur.execute(sql_query, (url,))
        current_site = cur.fetchall()
    except Exception as error:
        print("Checking for SEED URL duplicates led to", error)
    return current_site


def checkForDuplicateHTML(page_id, hashed_content, db_connection):
    duplicate_page = None

    cur = db_connection.cursor()
    try:
        sql_query = "SELECT id FROM crawldb.page WHERE id != %s AND page_hash = %s"
        cur.execute(sql_query, (page_id, hashed_content,))
        duplicate_page = cur.fetchall()
    except Exception as error:
        print("Checking for HTML duplicates led to", error)
    return duplicate_page
