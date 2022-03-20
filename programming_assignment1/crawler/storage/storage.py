import threading
import psycopg2 

lock = threading.Lock()

host="localhost"
user="postgres"
password="postgres"

datatype=['DOC','DOCX','PDF','PPT','PPTX']

class Storage(object):

    def __init__(self):
        self.conn = psycopg2.connect(host=host, user=user, password=password)
        self.conn.autocommit = True

    def add_site(self, domain, robots_content, sitemap_content):
        if Storage.contains_site(self,domain)==0:
            with lock:
                cur = self.conn.cursor()
                cur.execute("INSERT INTO crawldb.site (domain, robots_content, sitemap_content) VALUES (%s, %s, %s)", (domain, robots_content, sitemap_content))
            return True
        else:
            return False


    def update_site(self, domain, robots_content, sitemap_content):        
        if Storage.contains_site(self, domain)!=0:
            with lock:
                cur = self.conn.cursor()
                cur.execute("UPDATE crawldb.site SET robots_content=%s, sitemap_content=%s WHERE domain=%s", (robots_content, sitemap_content,domain))
            return True
        else:
            return False


    def contains_site(self,domain):
        with lock:
            cur = self.conn.cursor()
            cur.execute("SELECT id FROM crawldb.site WHERE domain=%s", (domain,))
            dataFromBase=cur.fetchall()
        if len(dataFromBase)==0:
            return False
        return dataFromBase[0][0]


    def retrieve_site(self, domain):
        with lock:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM crawldb.site WHERE domain=%s", (domain,))
            dataFromBase=cur.fetchall()
            cur.close()
        if len(dataFromBase)==0:
            return False
        return list(dataFromBase[0])

#---------------------------------------------------------------------------------

    def add_page(self, site, page_type_code, url, html_content, http_status_code, accessed_time):
        if Storage.contains_page(self, site,url)==0:
            pageSite=Storage.contains_site(self, site)
            if pageSite!=0:
                with lock:
                    cur = self.conn.cursor()
                    cur.execute("INSERT INTO crawldb.page (site_id, page_type_code, url, html_content, http_status_code, accessed_time) VALUES (%s, %s, %s, %s, %s, %s)", (pageSite,page_type_code.upper(), url, html_content, http_status_code, accessed_time))
                    cur.close()
                return True
            else:
                return False
        else:
            return False
    
    
    def update_page(self, site, page_type_code, url, html_content, http_status_code, accessed_time):
        if Storage.contains_page(self, site,url)!=0:
            pageSite=Storage.contains_site(self, site)
            if pageSite!=0:
                with lock:
                    cur = self.conn.cursor()
                    cur.execute("UPDATE crawldb.page SET site_id=%s,page_type_code=%s, html_content=%s, http_status_code=%s, accessed_time=%s WHERE url=%s", (pageSite,page_type_code, html_content, http_status_code, accessed_time, url))
                    cur.close()
                return True
            else:
                return False
        else:
            return False
    
    
    def contains_page(self, site,url):
        pageSite=Storage.contains_site(self, site)
        if pageSite==False:
            pageSite=0
        with lock:
            cur = self.conn.cursor()
            cur.execute("SELECT id FROM crawldb.page WHERE url=%s AND site_id=%s", (url,pageSite))
            dataFromBase=cur.fetchall()
            cur.close()
        if len(dataFromBase)==0:
            return False
        return dataFromBase[0][0]
    
    
    def retrieve_page(self, site,url):
        pageSite=Storage.contains_site(self, site)
        if pageSite==False:
            pageSite=0
        with lock:
            cur = self.conn.cursor()
            cur.execute("SELECT crawldb.site.domain, crawldb.page.* FROM crawldb.page  LEFT JOIN crawldb.site ON crawldb.page.site_id=site.id WHERE url=%s AND site_id=%s", (url,pageSite))
            dataFromBase=cur.fetchall()
            cur.close()
        if len(dataFromBase)==0:
            return False
        return list(dataFromBase[0])


#------------------------------------------------

    def contains_redirection(self, site1,url1,site2,url2):
        url1ID=Storage.contains_page(self, site1,url1)
        url2ID=Storage.contains_page(self, site2,url2)
        if url1ID==False:
            url1ID=0
        if url2ID==False:
            url2ID=0
        with lock:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM crawldb.link WHERE from_page=%s AND to_page=%s", (url1ID,url2ID))
            dataFromBase=cur.fetchall()
            cur.close()
        if len(dataFromBase)==0:
            return False
        return True


    def add_redirection(self, site1,url1,site2,url2):
        if Storage.contains_redirection(self, site1,url1,site2,url2)==0:
            url1ID=Storage.contains_page(self, site1,url1)
            url2ID=Storage.contains_page(self, site2,url2)
            if url1ID!=0 and url2ID!=0:
                with lock:
                    cur = self.conn.cursor()
                    cur.execute("INSERT INTO crawldb.link (from_page, to_page) VALUES(%s,%s)", (url1ID,url2ID))
                    cur.close()
                return True
            else:
                return False
        else:
            return False


#------------------------------------------------

    def add_image(self, site,url,filename,content_type,data,accessed_time):
        pageID=Storage.contains_page(self, site,url)
        if pageID!=0:
            with lock:
                cur = self.conn.cursor()
                cur.execute("INSERT INTO crawldb.image (page_id,filename,content_type,data,accessed_time) VALUES(%s,%s,%s,%s,%s)", (pageID,filename,content_type,data,accessed_time))
                cur.close()
            return True
        else:
            return False

    def contains_image(self, site,url,filename):
        pageID=Storage.contains_page(self, site,url)
        if pageID!=0:
            with lock:
                cur = self.conn.cursor()
                cur.execute("SELECT * FROM crawldb.image WHERE page_id=%s AND filename=%s", (pageID,filename))
                dataFromBase=cur.fetchall()
                cur.close()
            if len(dataFromBase)==0:
                return False
            return True
        else:
            return False

    def list_images(self, site,url):
        pageID=Storage.contains_page(self, site,url)
        if pageID==False:
            pageID=0
        dataFromBase=[]
        with lock:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM crawldb.image WHERE page_id=%s", (pageID,))
            dataFromBase=cur.fetchall()
            cur.close()
        return dataFromBase

#------------------------------------------------
# 

    def add_pagedata(self, site,url,data_type_code, data):
        pageID=Storage.contains_page(self, site,url)
        if pageID!=0 and data_type_code.upper() in datatype:
            with lock:
                cur = self.conn.cursor()
                cur.execute("INSERT INTO crawldb.page_data (page_id, data_type_code,data) VALUES(%s,%s,%s)", (pageID,data_type_code.upper(),data))
                cur.close()
            return True
        else:
            return False

    def contains_pagedata(self, site,url,data_type_code,data):
        pageID=Storage.contains_page(self, site,url)
        if pageID!=0:
            with lock:
                cur = self.conn.cursor()
                cur.execute("SELECT * FROM crawldb.page_data WHERE page_id=%s AND data=%s AND data_type_code=%s", (pageID,data,data_type_code.upper()))
                dataFromBase=cur.fetchall()
                cur.close()
            if len(dataFromBase)==0:
                return False
            return True
        else:
            return False

    def list_pagedata(self, site,url):
        pageID=Storage.contains_page(self, site,url)
        dataFromBase=[]
        if pageID!=0:
            with lock:
                cur = self.conn.cursor()
                cur.execute("SELECT * FROM crawldb.page_data WHERE page_id=%s", (pageID,))
                dataFromBase=cur.fetchall()
                cur.close()
        return dataFromBase




