from selenium import selenium
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.lxmlhtml import LxmlLinkExtractor
from scrapy.http import Request
from scrapy.link import Link
import scrapy

import gtk
import webkit
import jswebkit
from twisted.internet import defer

from scrapy.core.downloader.handlers.http import HttpDownloadHandler
from scrapy.http import HtmlResponse
from scrapy import log

import time

import urllib2

import threading

import random

import sqlite3

class WebkitParser: 

    def parse(self,response):
        webview = self._get_webview()
        win = gtk.Window()
        self.win=win

        self.links=[]
        # webview.connect('load-finished', lambda v, f: self._load_finished(d, v, f))
        # webview.connect("console-message", self._console_message)
        webview.connect("navigation-policy-decision-requested",self._nav_request_policy_decision_cb)
        webview.connect('document-load-finished', self._doc_load_finished)
        win.add(webview)
        win.hide_all()
        self.uri=response._get_url()
        page=response._get_body()
        webview.load_string(page,"text/html","iso-8859-15",self.uri)
        gtk.main()

    def _nav_request_policy_decision_cb(self,view,frame,net_req,nav_act,pol_dec):
            tmp_uri=net_req.get_uri()
            
            # print "--> %s"%tmp_uri

            if self.uri==tmp_uri:
                return False
            else:
                self.links.append(tmp_uri)
                # print self.links
                # page=urllib2.urlopen(tmp_uri)
                # view.load_string(page.read(),"text/html","iso-8859-15","")
                pol_dec.ignore()
                return True

    def _webview_done(self):
        gtk.main_quit()

    def _doc_load_finished(self, param1, param2):
        threading.Timer(2,self._webview_done).start()


    def _get_webview(self):
        webview = webkit.WebView()
        props = webview.get_settings()
        props.set_property('enable-java-applet', False)
        props.set_property('enable-plugins', False)
        props.set_property('enable-page-cache', False)
        #props.set_property('enable-frame-flattening', True)
        return webview

    # def _load_finished(self, deferred, view, frame):
    #     if frame != view.get_main_frame():
    #         return
    #     ctx = jswebkit.JSContext(frame.get_global_context())
    #     url = ctx.EvaluateScript('window.location.href')
    #     html = ctx.EvaluateScript('document.documentElement.innerHTML')
    #     response = HtmlResponse(url, encoding='utf-8', body=html.encode('utf-8'))
    #     self.deferred.callback(response)

sqlc=None

def checkAndInsertURL(tmp_uri):
    global sqlc
    tparams = (tmp_uri,)
    tq1=sqlc.cursor().execute("SELECT url from urls where url=?",tparams)
    tc1=0
    for tr1 in tq1:
        tc1=tc1+1
    if tc1==0:
        print "Inserting to urls db <--- [%s]"%tmp_uri
        tparams=(tmp_uri,'','','',)
        sqlc.cursor().execute("INSERT INTO urls VALUES (?,?,?,?)",tparams)
        sqlc.commit()

class WebKitLinkExtractor(LxmlLinkExtractor):

    def __init__(self, allow=(), deny=(), allow_domains=(), deny_domains=(), restrict_xpaths=(),
                     tags=('a', 'area'), attrs=('href',), canonicalize=True, unique=True, process_value=None,
                     deny_extensions=None):
        super(WebKitLinkExtractor, self).__init__(allow, deny, allow_domains, deny_domains, restrict_xpaths,
                     tags, attrs, canonicalize, unique, process_value,
                     deny_extensions)


    def extract_links(self,response):
        ret=None
        wp=WebkitParser()
        wp.parse(response)
        # lock.acquire()
        links=[]
        for tmp_uri in wp.links:
            links.append(Link(tmp_uri))
        ret=super(WebKitLinkExtractor,self).extract_links(response)
        if ret==None:
            ret=[]
        for link in links:
            ret.append(link)
        for link in ret:
            tmp_uri=link.url
            # print "---> %s"%tmp_uri
            checkAndInsertURL(tmp_uri)
        return ret



class MySpider(CrawlSpider):
    name = 'MySpider'
    rules = [
        Rule(WebKitLinkExtractor(allow=()), callback='parse_item', follow=True)
    ]

    def __init__(self, *args, **kwargs):
        global sqlc
        super(MySpider, self).__init__(*args, **kwargs) 
        #self.start_urls=['https://204.186.159.24/']
        urls_num = int(kwargs.get('urls_num','0'))
        start_urls = []
        for i in xrange(1, urls_num+1):
            start_urls.append(kwargs.get('start_url{0}'.format(i),''))

        self.start_urls = start_urls

        db_name = kwargs.get('db','url.db')
        conn = sqlite3.connect(db_name)
        sqlc = conn
        rows=sqlc.cursor().execute("SELECT name FROM sqlite_master WHERE type='table' AND name='urls';")
        count = 0
        for row in rows:
            count += 1
        if count==0:
            sqlc.cursor().execute("CREATE TABLE urls(url text, server text, framework text, os text)");

        for tmp_uri in self.start_urls:
            checkAndInsertURL(tmp_uri)

        # print start_urls

    # def set_crawler(self, crawler):
    #     crawler.settings.set("DOWNLOAD_HANDLERS",{'http': 'test.WebkitDownloadHandler','https': 'test.WebkitDownloadHandler'})
    #     super(TestSpider, self).set_crawler(crawler)

    def parse_item(self, response):
        fp=open("/tmp/fuck.txt","wb")
        fp.close()
        # sel = scrapy.selector.Selector(response)
        # questions = sel.css('#question-mini-list .question-summary')
        # for i, elem in enumerate(questions):
        #     l = scrapy.contrib.loader.ItemLoader(QuestionItem(), elem)
        #     l.add_value('idx', i)
        #     l.add_xpath('title', ".//h3/a/text()")
        #     yield l.load_item()
