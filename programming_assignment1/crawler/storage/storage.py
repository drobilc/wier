from operator import truediv
import threading
import psycopg2 
import logging
import time
from datetime import datetime
from urllib.parse import urlparse
import hashlib

datatype=['DOC','DOCX','PDF','PPT','PPTX']

class Storage(object):

    def __init__(self, configuration):
        host = configuration.get('database_host')
        user = configuration.get('database_user')
        password = configuration.get('database_password')
        database = configuration.get('database_name')

        self.lock = threading.Lock()

        self.conn = psycopg2.connect(database=database, host=host, user=user, password=password)
        self.conn.autocommit = True

        self.db_pool = None
    
    def save_page(self, url, html, page_hash=None, page_type='HTML'):
        url_parts = urlparse(url)
        
        # First, add domain to database. If it already exists, it will be not be
        # changed.
        domain = url_parts.hostname
        site_id = self.add_site(domain, '', '')

        # Then, 
        return self.add_page(site_id, page_type, url, html, page_hash, 200, datetime.now())
    
    def save_page_data(self, url, extension):
        page_id = self.save_page(url, None, page_type='BINARY')
        self.add_page_data(page_id, extension, None)
    
    def save_image(self, page_id, image_url, file_extension):
        return self.add_image(page_id, image_url, file_extension, None, datetime.now())

    def add_site(self, domain, robots_content, sitemap_content):
        """
            Insert a site into database and return its id. If the site could not
            be inserted, `None` will be returned instead.
        """

        # Try to find site in database. If it already exists, return its id.
        existing_site_id = self.contains_site(domain)
        if existing_site_id is not None:
            return existing_site_id

        # The site does not exist yet, insert it into database, get its id and
        # return it.
        with self.lock:
            cur = self.conn.cursor()
            cur.execute("INSERT INTO crawldb.site (domain, robots_content, sitemap_content) VALUES (%s, %s, %s) RETURNING id", (domain, robots_content, sitemap_content))
            site_id = cur.fetchone()[0]
            cur.close()
            return site_id
    
    def contains_site(self, domain):
        """
            Find site by its domain name. If the site does not exist, `None`
            will be returned.
        """
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id FROM crawldb.site WHERE domain=%s", (domain,))
            
            # The site doesn't exist yet, return None.
            if cursor.rowcount < 1:
                return None
            
            site_id = cursor.fetchone()[0]
            cursor.close()
            return site_id

    def update_site(self, domain, robots_content, sitemap_content):        
        if self.contains_site(domain)!=0:
            with self.lock:
                cur = self.conn.cursor()
                cur.execute("UPDATE crawldb.site SET robots_content=%s, sitemap_content=%s WHERE domain=%s", (robots_content, sitemap_content,domain))
                cur.close()
            return True
        else:
            return False

    def retrieve_site(self, domain):
        with self.lock:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM crawldb.site WHERE domain=%s", (domain,))
            dataFromBase=cur.fetchall()
            cur.close()
        if len(dataFromBase)==0:
            return False
        return list(dataFromBase[0])

#---------------------------------------------------------------------------------

    def add_page(self, site_id, page_type_code, url, html_content, accessed_time, http_status_code=200):
        """
            Add page to database and return its id. If the page could not be
            added to database, `None` will be returned.
        """
        existing_page_id = self.get_page_id(url)
        if existing_page_id is not None:
            return existing_page_id
        
        with self.lock:
            cur = self.conn.cursor()

            page_hash = self.compute_hash(html_content)

            cur.execute("INSERT INTO crawldb.page (site_id, page_type_code, url, html_content, page_hash, accessed_time, http_status_code) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id", (site_id, page_type_code.upper(), url, html_content, page_hash, accessed_time, http_status_code))
            page_id = cur.fetchone()[0]
            cur.close()
            return page_id
    
    def get_page_id(self, url):
        """
            Find page by its URL address. If the page does not exist, `None`
            will be returned.
        """
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id FROM crawldb.page WHERE url=%s", (url,))
            
            # The site doesn't exist yet, return None.
            if cursor.rowcount < 1:
                return None
            
            page_id = cursor.fetchone()[0]
            cursor.close()
            return page_id
    
    def contains_page(self, site, url):
        return self.get_page_id(url)
    
    def update_page(self, site, page_type_code, url, html_content, http_status_code, accessed_time):
        if self.contains_page(site,url)!=0:
            pageSite=self.contains_site(site)
            if pageSite!=0:
                with self.lock:
                    cur = self.conn.cursor()
                    cur.execute("UPDATE crawldb.page SET site_id=%s,page_type_code=%s, html_content=%s, http_status_code=%s, accessed_time=%s WHERE url=%s", (pageSite,page_type_code, html_content, http_status_code, accessed_time, url))
                    cur.close()
                return True
            else:
                return False
        else:
            return False

    def retrieve_page(self, site,url):
        pageSite=self.contains_site(site)
        if pageSite==False:
            pageSite=0
        with self.lock:
            cur = self.conn.cursor()
            cur.execute("SELECT crawldb.site.domain, crawldb.page.* FROM crawldb.page  LEFT JOIN crawldb.site ON crawldb.page.site_id=site.id WHERE url=%s AND site_id=%s", (url,pageSite))
            dataFromBase=cur.fetchall()
            cur.close()
        if len(dataFromBase)==0:
            return False
        return list(dataFromBase[0])


#------------------------------------------------

    def contains_redirection(self,from_page_id, to_page_id):
        with self.lock:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM crawldb.link WHERE from_page=%s AND to_page=%s", (from_page_id,to_page_id))
            dataFromBase=cur.fetchall()
            cur.close()
        if len(dataFromBase)==0:
            return False
        return True

    def save_redirection(self, url1, url2):
        id1 = self.get_page_id(url1)
        id2 = self.get_page_id(url2)
        self.add_redirection(id1, id2)
    
    def compute_hash(self, content):
        return hashlib.md5(content.encode()).hexdigest()
    
    def check_if_duplicate(self, content):
        hash = self.compute_hash(content)
        with self.lock:
            cur = self.conn.cursor()
            cur.execute("SELECT id FROM crawldb.page WHERE page_hash=%s", (hash,))
            dataFromBase=cur.fetchall()
            cur.close()
        if len(dataFromBase)==0:
            return None
        else:
            return dataFromBase[0][0]
        # poizvedba v bazi, ce obstaja, vrni id, sicer None

    def add_redirection(self, from_page_id, to_page_id):
        # Preveri ali obstaja redirection, ce ja, vrni neki, sicer dodaj in vrni neki
        if not self.contains_redirection(from_page_id,to_page_id):
            with self.lock:
                cur = self.conn.cursor()
                cur.execute("INSERT INTO crawldb.link (from_page, to_page) VALUES(%s,%s)", (from_page_id,to_page_id))
                cur.close()
            return True
        else:
            return False

#------------------------------------------------

    def add_image(self, page_id, image_url, content_type, data, accessed_time):
        with self.lock:
            cur = self.conn.cursor()
            cur.execute("INSERT INTO crawldb.image (page_id, filename, content_type, data, accessed_time) VALUES(%s,%s,%s,%s,%s) RETURNING id", (page_id, image_url, content_type, data, accessed_time))
            image_id = cur.fetchone()[0]
            cur.close()
            return image_id
        """pageID=self.contains_page(site,url)
        if pageID!=0:
            with self.lock:
                cur = self.conn.cursor()
                cur.execute("INSERT INTO crawldb.image (page_id,filename,content_type,data,accessed_time) VALUES(%s,%s,%s,%s,%s)", (pageID,filename,content_type,data,accessed_time))
                cur.close()
            return True
        else:
            return False"""

    def contains_image(self, site,url,filename):
        pageID=self.contains_page(site,url)
        if pageID!=0:
            with self.lock:
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
        pageID=self.contains_page(site,url)
        if pageID==False:
            pageID=0
        dataFromBase=[]
        with self.lock:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM crawldb.image WHERE page_id=%s", (pageID,))
            dataFromBase=cur.fetchall()
            cur.close()
        return dataFromBase

#------------------------------------------------
# 

    def add_page_data(self, page_id, data_type_code, data):
        with self.lock:
            cur = self.conn.cursor()
            cur.execute("INSERT INTO crawldb.page_data (page_id, data_type_code,data) VALUES(%s,%s,%s) RETURNING id", (page_id, data_type_code.upper(), data))
            page_data_id = cur.fetchone()[0]
            cur.close()
            return page_data_id
        """pageID=self.contains_page(site,url)
        if pageID!=0 and data_type_code.upper() in datatype:
            with self.lock:
                cur = self.conn.cursor()
                cur.execute("INSERT INTO crawldb.page_data (page_id, data_type_code,data) VALUES(%s,%s,%s)", (pageID,data_type_code.upper(),data))
                cur.close()
            return True
        else:
            return False"""

    def contains_pagedata(self,site,url,data_type_code,data):
        pageID=self.contains_page(site,url)
        if pageID!=0:
            with self.lock:
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
        pageID=self.contains_page(site,url)
        dataFromBase=[]
        if pageID!=0:
            with self.lock:
                cur = self.conn.cursor()
                cur.execute("SELECT * FROM crawldb.page_data WHERE page_id=%s", (pageID,))
                dataFromBase=cur.fetchall()
                cur.close()
        return dataFromBase
    
    def check_for_duplicate_html(self, hashed_content):
        with self.lock:
            duplicate_page = None

            cur = self.conn.cursor()
            try:
                sql_query = "SELECT id FROM crawldb.page WHERE page_hash = %s"
                cur.execute(sql_query, (hashed_content,))
                if cur.rowcount < 0:
                    return None
                duplicate_page = cur.fetchone()
                return duplicate_page[0]
            except Exception as error:
                logging.exception(error)
            return duplicate_page
    
    def save_duplicate(self, page_id, duplicate_url):
        duplicate_id = self.save_page(duplicate_url, None, page_type='DUPLICATE')
        with self.lock:
            cur = self.conn.cursor()
            cur.execute("INSERT INTO crawldb.link (from_page, to_page) VALUES(%s, %s)", (duplicate_id, page_id))
            cur.close()
    
    def getFromFrontier(self):
        time.sleep(12)
        accessed_current_page = None

        cur = self.conn.cursor()
        try:
            sql_query = """ SELECT * FROM crawldb.page
                                WHERE accessed_time IS %s
                                ORDER BY id asc
                                LIMIT 1 """
            cur.execute(sql_query, (None, ))
            current_page = cur.fetchone()
            if current_page is not None:
                now = datetime.now()
                access_time = now.strftime("%Y-%m-%d %H:%M:%S'")
                sql_query = """ UPDATE crawldb.page
                                    SET accessed_time = %s
                                    WHERE id = %s
                                    RETURNING * """
                cur.execute(sql_query, (access_time, current_page[0]))
                accessed_current_page = cur.fetchone()
                self.conn.commit()
        except Exception as error:
            print("Getting the first site from the frontier led to", error)
        return accessed_current_page
    
    def disconnect(self):
        try:
            if self.db_pool:
                self.db_pool.closeall()
                logging.info('PostgreSQL connection pool is closed!')
        except Exception as error:
            logging.exception(error)