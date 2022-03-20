import threading
import psycopg2 

lock = threading.Lock()

host="localhost"
user="postgres"
password="postgres"

datatype=['DOC','DOCX','PDF','PPT','PPTX']

class Storage(object):

    def __init__(self):
        pass

    def add_site(domain, robots_content, sitemap_content):
        if Storage.contains_site(domain)==0:
            conn = psycopg2.connect(host=host, user=user, password=password)
            conn.autocommit = True
            with lock:
                cur = conn.cursor()
                cur.execute("INSERT INTO crawldb.site (domain, robots_content, sitemap_content) VALUES (%s, %s, %s)", (domain, robots_content, sitemap_content))
                cur.close()
            conn.close()
            return 1
        else:
            return 0


    def update_site(domain, robots_content, sitemap_content):        
        if Storage.contains_site(domain)!=0:
            conn = psycopg2.connect(host=host, user=user, password=password)
            conn.autocommit = True
            with lock:
                cur = conn.cursor()
                cur.execute("UPDATE crawldb.site SET robots_content=%s, sitemap_content=%s WHERE domain=%s", (robots_content, sitemap_content,domain))
                cur.close()
            conn.close()
            return 1
        else:
            return 0


    def contains_site(domain):
        conn = psycopg2.connect(host=host, user=user, password=password)
        conn.autocommit = True
        with lock:
            cur = conn.cursor()
            cur.execute("SELECT id FROM crawldb.site WHERE domain=%s", (domain,))
            dataFromBase=cur.fetchall()
            #dataFromBase=cur.fetchall()[0]
            cur.close()
        conn.close()
        if len(dataFromBase)==0:
            return 0
        return dataFromBase[0][0]


    def retrieve_site(domain):
        conn = psycopg2.connect(host=host, user=user, password=password)
        conn.autocommit = True
        with lock:
            cur = conn.cursor()
            cur.execute("SELECT * FROM crawldb.site WHERE domain=%s", (domain,))
            dataFromBase=cur.fetchall()
            cur.close()
        conn.close()
        if len(dataFromBase)==0:
            return 0
        return list(dataFromBase[0])

#---------------------------------------------------------------------------------

    def add_page(site, page_type_code, url, html_content, http_status_code, accessed_time):
        if Storage.contains_page(site,url)==0:
            pageSite=Storage.contains_site(site)
            if pageSite!=0:
                conn = psycopg2.connect(host=host, user=user, password=password)
                conn.autocommit = True
                with lock:
                    cur = conn.cursor()
                    cur.execute("INSERT INTO crawldb.page (site_id, page_type_code, url, html_content, http_status_code, accessed_time) VALUES (%s, %s, %s, %s, %s, %s)", (pageSite,page_type_code.upper(), url, html_content, http_status_code, accessed_time))
                    cur.close()
                conn.close()
                return 1
            else:
                return 0
        else:
            return 0
    
    
    def update_page(site, page_type_code, url, html_content, http_status_code, accessed_time):
        if Storage.contains_page(site,url)!=0:
            pageSite=Storage.contains_site(site)
            if pageSite!=0:
                conn = psycopg2.connect(host=host, user=user, password=password)
                conn.autocommit = True
                with lock:
                    cur = conn.cursor()
                    cur.execute("UPDATE crawldb.page SET site_id=%s,page_type_code=%s, html_content=%s, http_status_code=%s, accessed_time=%s WHERE url=%s", (pageSite,page_type_code, html_content, http_status_code, accessed_time, url))
                    cur.close()
                conn.close()
                return 1
            else:
                return 0
        else:
            return 0
    
    
    def contains_page(site,url):
        pageSite=Storage.contains_site(site)
        conn = psycopg2.connect(host=host, user=user, password=password)
        conn.autocommit = True
        with lock:
            cur = conn.cursor()
            cur.execute("SELECT id FROM crawldb.page WHERE url=%s AND site_id=%s", (url,pageSite))
            dataFromBase=cur.fetchall()
            cur.close()
        conn.close()
        if len(dataFromBase)==0:
            return 0
        return dataFromBase[0][0]
    
    
    def retrieve_page(site,url):
        pageSite=Storage.contains_site(site)
        conn = psycopg2.connect(host=host, user=user, password=password)
        conn.autocommit = True
        with lock:
            cur = conn.cursor()
            cur.execute("SELECT crawldb.site.domain, crawldb.page.* FROM crawldb.page  LEFT JOIN crawldb.site ON crawldb.page.site_id=site.id WHERE url=%s AND site_id=%s", (url,pageSite))
            dataFromBase=cur.fetchall()
            cur.close()
        conn.close()
        if len(dataFromBase)==0:
            return 0
        return list(dataFromBase[0])


#------------------------------------------------

    def contains_redirection(site1,url1,site2,url2):
        url1ID=Storage.contains_page(site1,url1)
        url2ID=Storage.contains_page(site2,url2)
        conn = psycopg2.connect(host=host, user=user, password=password)
        conn.autocommit = True
        with lock:
            cur = conn.cursor()
            cur.execute("SELECT * FROM crawldb.link WHERE from_page=%s AND to_page=%s", (url1ID,url2ID))
            dataFromBase=cur.fetchall()
            cur.close()
        conn.close()
        if len(dataFromBase)==0:
            return 0
        return 1


    def add_redirection(site1,url1,site2,url2):
        if Storage.contains_redirection(site1,url1,site2,url2)==0:
            url1ID=Storage.contains_page(site1,url1)
            url2ID=Storage.contains_page(site2,url2)
            if url1ID!=0 and url2ID!=0:
                conn = psycopg2.connect(host=host, user=user, password=password)
                conn.autocommit = True
                with lock:
                    cur = conn.cursor()
                    cur.execute("INSERT INTO crawldb.link (from_page, to_page) VALUES(%s,%s)", (url1ID,url2ID))
                    cur.close()
                conn.close()
                return 1
            else:
                return 0
        else:
            return 0


#------------------------------------------------

    def add_image(site,url,filename,content_type,data,accessed_time):
        pageID=Storage.contains_page(site,url)
        if pageID!=0:
            conn = psycopg2.connect(host=host, user=user, password=password)
            conn.autocommit = True
            with lock:
                cur = conn.cursor()
                cur.execute("INSERT INTO crawldb.image (page_id,filename,content_type,data,accessed_time) VALUES(%s,%s,%s,%s,%s)", (pageID,filename,content_type,data,accessed_time))
                cur.close()
            conn.close()
            return 1
        else:
            return 0

    def contains_image(site,url,filename):
        pageID=Storage.contains_page(site,url)
        if pageID!=0:
            conn = psycopg2.connect(host=host, user=user, password=password)
            conn.autocommit = True
            with lock:
                cur = conn.cursor()
                cur.execute("SELECT * FROM crawldb.image WHERE page_id=%s AND filename=%s", (pageID,filename))
                dataFromBase=cur.fetchall()
                cur.close()
            conn.close()
            if len(dataFromBase)==0:
                return 0
            return 1
        else:
            return 0

    def list_images(site,url):
        pageID=Storage.contains_page(site,url)
        dataFromBase=[]
        conn = psycopg2.connect(host=host, user=user, password=password)
        conn.autocommit = True
        with lock:
            cur = conn.cursor()
            cur.execute("SELECT * FROM crawldb.image WHERE page_id=%s", (pageID,))
            dataFromBase=cur.fetchall()
            cur.close()
        conn.close()
        return dataFromBase

#------------------------------------------------
# 

    def add_pagedata(site,url,data_type_code, data):
        pageID=Storage.contains_page(site,url)
        if pageID!=0 and data_type_code.upper() in datatype:
            conn = psycopg2.connect(host=host, user=user, password=password)
            conn.autocommit = True
            with lock:
                cur = conn.cursor()
                cur.execute("INSERT INTO crawldb.page_data (page_id, data_type_code,data) VALUES(%s,%s,%s)", (pageID,data_type_code.upper(),data))
                cur.close()
            conn.close()
            return 1
        else:
            return 0

    def contains_pagedata(site,url,data_type_code,data):
        pageID=Storage.contains_page(site,url)
        if pageID!=0:
            conn = psycopg2.connect(host=host, user=user, password=password)
            conn.autocommit = True
            with lock:
                cur = conn.cursor()
                cur.execute("SELECT * FROM crawldb.page_data WHERE page_id=%s AND data=%s AND data_type_code=%s", (pageID,data,data_type_code.upper()))
                dataFromBase=cur.fetchall()
                cur.close()
            conn.close()
            if len(dataFromBase)==0:
                return 0
            return 1
        else:
            return 0

    def list_pagedata(site,url):
        pageID=Storage.contains_page(site,url)
        dataFromBase=[]
        if pageID!=0:
            conn = psycopg2.connect(host=host, user=user, password=password)
            conn.autocommit = True
            with lock:
                cur = conn.cursor()
                cur.execute("SELECT * FROM crawldb.page_data WHERE page_id=%s", (pageID,))
                dataFromBase=cur.fetchall()
                cur.close()
            conn.close()
        return dataFromBase




