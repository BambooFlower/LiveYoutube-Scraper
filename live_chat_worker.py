# -*- coding: utf-8 -*-
"""
Worker class which immitates the browser behaviour

1) LiveStats
2) LiveComments
"""
from requests import session
import re
from random import random
from urllib.parse import urlparse
from time import sleep
from time import time
import json
import threading
from CommentsParser import parse_response

class RequestJSONGenerator():
    def __init__(self,data):
        self.clickTrackingParams = data['clickTrackingParams']
        self.visitordata = data['visitorData']
        self.clientScreenNonce = data['clientScreenNonce']
        self.sessionId = data['sessionId']
        self.userAgent = data['userAgent']
        self.videoId = data['videoId']
        self.continuation = data['continuation']
        
        self.browserName = 'Firefox'
        self.browserVersion = '78.0'
        self.clientName = 'WEB'
        self.clientVersion = '2.20200911.04.00'
        self.gl = 'GB'
        self.hl = 'en-GB'
        self.osName = 'Windows'
        self.osVersion = '10.0'
        self.screenHeightPoints = 1080
        self.screenPixelDensity = 1
        self.screenWidthPoints = 1920
        self.userInterfaceTheme = 'USER_INTERFACE_THEME_LIGHT'
        self.utcOffsetMinutes = 60
        
        self.continuation = None
        
        self.metadata = self.gen_metadata_json()
        self.stats = self.gen_stats_json()
    
    def gen_metadata_json(self):
        adSignalsInfo = {
                'consentBumpParams':{
                        'consentDay':'4',
                        'consentHostnameOverride':'https://www.youtube.com',
                        'urlOverride':''
                        }
                }
        clickTracking = {
                'clickTracking':self.clickTrackingParams
                }
        client={
            'browserName':self.browserName,
            'browserVersion':self.browserVersion,
            'clientName':self.clientName,
            'clientVersion':self.clientVersion,
            'gl':self.gl,
            'hl':self.hl,
            'osName':self.osName,
            'osVersion':self.osVersion,
            'screenHeightPoints':self.screenHeightPoints,
            'screenPixelDensity':self.screenPixelDensity,
            'screenWidthPoints':self.screenWidthPoints,
            'userAgent':self.userAgent,
            'userInterfaceTheme':self.userInterfaceTheme,
            'utcOffsetMinutes':self.utcOffsetMinutes,
            'visitorData':self.visitordata
        }
        request = {
                'consistencyTokenJars':[],
                'internalExperimentFlags':[],
                'sessionId':self.sessionId
                }        
        
        context = {
                'adSignalsInfo':adSignalsInfo,
                'clickTracking':clickTracking,
                'client':client,
                'clientScreenNonce':self.clientScreenNonce,
                'request':request,      
                'user':{}
                }        
        return {'context':context,'videoId':self.videoId}
    
    def gen_stats_json(self):
        client={
            'browserName':self.browserName,
            'browserVersion':self.browserVersion,
            'clientName':self.clientName,
            'clientVersion':self.clientVersion,
            'gl':self.gl,
            'hl':self.hl,
            'osName':self.osName,
            'osVersion':self.osVersion,
            'screenHeightPoints':self.screenHeightPoints,
            'screenPixelDensity':self.screenPixelDensity,
            'screenWidthPoints':self.screenWidthPoints,
            'userAgent':self.userAgent,
            'userInterfaceTheme':self.userInterfaceTheme,
            'utcOffsetMinutes':self.utcOffsetMinutes,
            'visitorData':self.visitordata
        }
        request = {
                'consistencyTokenJars':[],
                'internalExperimentFlags':[],
                'sessionId':self.sessionId
                }        
        
        context = {
                    'context':{
                    'client':client,
                    'clientScreenNonce':self.clientScreenNonce,
                    'request':request,      
                    'user':{},
                    },
                'hidden':False
                }
        return context
    
    def update_metadata(self,continuation):
        try:
            self.metadata.pop('videoId')
        except KeyError:
            pass
        self.metadata['continuation'] = continuation
        

class LiveMachine():
    def __init__(self,video_id):
        self.session = session()
        self.base_url = 'https://www.youtube.com/'
        self.video_id = video_id
        self.watch_url = '{}watch?v={}'.format(self.base_url,self.video_id)        
        
        self.user_agent = self.get_user_agent()
        
        self.req_key = None
        self.req_serializedEventId = None
        self.req_sessionId = None
        self.req_clickTrackingParams = None
        self.req_CSN = self.create_csn()
        self.req_comment_continuation = None
        self.req_stats_continuation = None
        self.req_visitorData = None

        self.channel_id = ''
        self.video_name = ''
        self.is_live = False
        self.comments_enabled = False
        self.timestamp_start = ''
        
        self.num_viewers = 0
        self.num_likes = 0
        self.num_dislikes = 0
        self.num_og_likes = 0
        self.num_og_dislikes = 0
        
        self.stop = False  ## Stop flag...
        self.stats_waiting = False
        self.comments_waiting = False
        
        self.get_initial_data()
        
        self.session_stats = self.session
        self.session_comments = self.session
        
        self.get_initial_comment_continuation()
        
        
        self.stats_timeout = 0
        self.comment_timeout = 0
        
        self.stats_hist = []
        self.comments_hist = []
        
                
        dataForJSON = {
                'clickTrackingParams':self.req_clickTrackingParams,
                'visitorData':self.req_visitorData,
                'clientScreenNonce':self.req_CSN,
                'sessionId':self.req_sessionId,
                'userAgent':self.user_agent,
                'videoId':self.video_id,
                'continuation':self.req_comment_continuation
                }
        
        self.req_json = RequestJSONGenerator(dataForJSON)
        
                
    def get_user_agent(self):
        # Might want to find a better way to initialise a User-Agent
        return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0'
    
    def update_comment_continuation(self,continuation):
        self.req_comment_continuation = continuation
        pass
    
    def get_initial_comment_continuation(self,dbg=False):
        # Set headers
        headers = {
                'Host': 'www.youtube.com',
                'User-Agent': self.user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-GB,en;q=0.5',
#                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'max-age=0',
                'TE': 'Trailers'
                }
        url = self.base_url + 'live_chat?v={}'.format(self.video_id)
        self.session_comments.headers = headers
        r = self.session_comments.get(url)
        
        if r.status_code != 200:
            print('YouTube says {}. bad user!')
            exit(r.status_code)
        
        resp_html = r.text
        
        if 'Chat is disabled for this live stream.' in r.text:
            self.comments_enabled = False
        else:
            self.comments_enabled = True
        
        # Find continuation parameter in HTML
        try:
            match = re.findall('"continuation":"[aA0-zZ9_]+"',resp_html)[0]
            tmp_val = match.replace('"','').replace(':','').replace('continuation','')
            self.update_comment_continuation(tmp_val)
        except IndexError:
            if dbg:
                print("Can't find the 'continuation' in the initial request, " +
                  'reverting to 0ofMyANmGlBDamdLRFFvTGNXTnVZVkZYYkVoZmNVa3FKd29ZVlVOekxUWnpRM295VEVwdE1WQnlWMUZPTkVWeWMxQjNFZ3R4WTI1aFVWZHNTRjl4U1NBQjABggECCASIAQGgAeOUlv_f5usC')
            tmp_val = '0ofMyANmGlBDamdLRFFvTGNXTnVZVkZYYkVoZmNVa3FKd29ZVlVOekxUWnpRM295VEVwdE1WQnlWMUZPTkVWeWMxQjNFZ3R4WTI1aFVWZHNTRjl4U1NBQjABggECCASIAQGgAeOUlv_f5usC'
            self.update_comment_continuation(tmp_val)
        
    
    def get_initial_data(self,dbg=False):
        # Set headers
        headers = {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-GB,en;q=0.5',
#            'Accept-Encoding': 'gzip, deflate, br',  # Don't need to encode...
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'TE': 'Trailers'
        }
        self.session.headers = headers
        
        r = self.session.get(self.watch_url)
                
        if r.status_code != 200:
            print('YouTube frowns with Error {} on its face'.format(r.status_code))
            exit(r.status_code)
        
        resp_html = r.text
        
        # Find key parameter -- "innertubeApiKey"
        try:
            match = re.findall('"innertubeApiKey":"[aA0-zZ9_]+"',resp_html)[0]
            self.req_key = match.replace('"','').replace(':','').replace('innertubeApiKey','')
        except IndexError:
            if dbg:
                print("Can't find the 'innertubeApiKey/key' in the initial request, " +
                  'reverting to AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8')
            self.req_key = 'AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8'
#        print(self.req_key)
        
        # Find EVENT_ID -- "serializedEventId"
        try:
            match = re.findall('"EVENT_ID":"[aA0-zZ9_]+"',resp_html)[0]
            self.req_serializedEventId = match.replace('"','').replace(':','').replace('EVENT_ID','')
        except IndexError:
            if dbg:
                print("Can't find the 'EVENT_ID/serializedEventId' in the initial request, "+
                  'reverting to 5_NdX_76Mczj0wXb26bwCA')
            self.req_serializedEventId = '5_NdX_76Mczj0wXb26bwCA'
#        print(self.req_serializedEventId)
        
        # Find sessionId -- "sessionId"
        try:
            match = re.findall('"sessionId":"[aA0-zZ9_]+"',resp_html)[0]
            self.req_sessionId = match.replace('"','').replace(':','').replace('sessionId','')
        except IndexError:
            if dbg:
                print("Can't find the 'sessionId/sessionId' in the initial request, "+
                  'reverting to 6871917207188534706')
            self.req_sessionId = '6871917207188534706'
#        print(self.req_sessionId)
        
        # Find clickTrackingParams -- "clickTrackingParams"
        try:
            match = re.findall('"clickTrackingParams":"[aA0-zZ9_]+"',resp_html)[0]
            self.req_clickTrackingParams = match.replace('"','').replace(':','').replace('clickTrackingParams','')
        except IndexError:
            if dbg:
                print("Can't find the 'clickTrackingParams/clickTrackingParams' in the initial request, " + 
                  'reverting to CB0QtSwYACITCNvViKL25esCFUW8VQodD_8N5w==')
            self.req_clickTrackingParams = 'CB0QtSwYACITCNvViKL25esCFUW8VQodD_8N5w=='
#        print(self.req_clickTrackingParams)
                
        # find visitorData -- in VISITOR_DATA
        try:
            match = re.findall('"VISITOR_DATA":"[aA0-zZ9_]+"',resp_html)[0]
            self.req_visitorData = match.replace('"','').replace(':','').replace('VISITOR_DATA','')
        except IndexError:
            if dbg:
                print("Can't find the 'VISITOR_DATA/visitorData' in the initial request, " +
                  'reverting to CgtQMm9EN0ctb1RDSSjcvfj6BQ%3D%3D')
            self.req_visitorData = 'CgtQMm9EN0ctb1RDSSjcvfj6BQ%3D%3D'
#        print(self.req_visitorData)
            
        # find channelId-- in channelId
        try:
            match = re.findall('"channelId":"[aA0-zZ9]+"',resp_html)[0]            
            self.channel_id = match.replace('"','').replace(':','').replace('channelId','')
        except IndexError:
            if dbg:
                print("Can't find the 'channelId/channelId' in the initial request, " +
                  'reverting to NO_CHANNEL')
            self.channel_id = 'NO_CHANNEL'
#        print(self.req_visitorData)

        # find channelId-- in channelId
        try:
            match = re.findall('"channelId":"[aA0-zZ9]+"',resp_html)[0]            
            self.channel_id = match.replace('"','').replace(':','').replace('channelId','')
        except IndexError:
            if dbg:
                print("Can't find the number of likes, reverting to 0")
            self.channel_id = 'NO_CHANNEL'
#        print(self.req_visitorData)
        
        # find likes in HTML
        try:
            match = re.findall('[aA0-zZ9,]+ likes',resp_html)[0]            
            self.num_og_likes = match.replace(' likes','').replace(',','')
            if 'No' in self.num_og_likes:
                self.num_og_likes = 0
        except IndexError:
            if dbg:
                print("Can't find the number of likes, reverting to 0")
            self.num_og_likes = 0
#        print(self.num_og_likes)
        
        # find dislikes in HTML
        try:
            match = re.findall('[aA0-zZ9,]+ dislikes',resp_html)[0]            
            self.num_og_dislikes = match.replace(' dislikes','').replace(',','')
            if 'No' in self.num_og_dislikes:
                self.num_og_dislikes = 0
        except IndexError:
            if dbg:
                print("Can't find the number of dislikes, reverting to 0")
            self.num_og_dislikes = 0
#        print(self.num_og_dislikes)
            
        # find start timestamp in the HTML
        try:
            match = re.findall('startTimestamp":"[0-9\-\:+T]+',resp_html)[0]            
            self.timestamp_start = match.replace('startTimestamp','').replace('"','').replace(':','')
        except IndexError:
            if dbg:
                print("Can't find the number of dislikes, reverting to ''")
            self.timestamp_start = ''
#        print(self.timestamp_start)
        
    def create_csn(self):
        '''
        Port from the 'base.js' file
        '''
        
        rnd = str(random())
        alphabet = 'ABCDEFGHIJKLMOPQRSTUVWXYZabcdefghjijklmnopqrstuvwxyz0123456789'
        jda = [alphabet + '+/=',
               alphabet + '+/',
               alphabet + '-_=',
               alphabet + '-_.',
               alphabet + '-_']
        b = jda[3]
        
        a = [ord(char) for char in rnd]
        
        
        c = ""
        d = 0
        while d < len(a):
            f = a[d]
            g = d + 1 < len(a)
            if g:
                m = a[d+1]
            else:
                m = 0
            n = d + 2 < len(a)
            if n:
                q = a[d+2]
            else:
                q = 0
            r = f >> 2
            f = (f & 3) << 4 | m >> 4
            m = (m & 15) << 2 | q >> 6 
            q &= 63
            if not n:
                q = 64
                if not g:
                    m = 64
            c += "{}{}{}{}".format(b[r],b[f],b[m],b[q])
            d += 3
        return c
    
    def append_stats(self,data):
        self.stats_hist.append(data)
        pass
        
    def request_stats(self):
        # Create headers
        headers = {        
            'Host': 'www.youtube.com',
            'User-Agent': self.user_agent,
            'Accept': '*/*',
            'Accept-Language': 'en-GB,en;q=0.5',
#            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': self.watch_url,
            'Content-Type': 'application/json',
            'X-Goog-Visitor-Id':urlparse(self.req_visitorData).geturl(),
            'Origin': 'https://www.youtube.com',
            'Connection': 'keep-alive',
            'TE': 'Trailers'
            }
#        self.session.headers = headers
        
        url = '{}youtubei/v1/updated_metadata?key={}'.format(self.base_url,self.req_key)
        self.session_stats.headers = headers
        
        
        x = threading.Thread(target=self.stats_worker,args=(url,))
        x.start()

        
    def stats_worker(self,url):
        while 1:
            self.stats_waiting = False
            r = self.session_stats.post(url,json=self.req_json.metadata)
            
            if r.status_code != 200:
                print('YouTube says {} to metadata'.format(r.status_code))
                exit(r.status_code)
            
            resp_json = r.json()
            
            # Update continuation value
            tmp = resp_json['continuation']['timedContinuationData']
            continuation = tmp['continuation']
            self.stats_timeout = tmp['timeoutMs']/1000
            
            self.req_stats_continuation = continuation
            self.req_json.update_metadata(self.req_stats_continuation)
            
            # Extract data
            
            # Number of viewers
            tmp = resp_json['actions'][0]

            if 'isEmpty' in tmp.keys():
                self.num_viewers = 0
            else:
                tmp = tmp['updateViewershipAction']['viewCount']
                try:
                    viewers = tmp['videoViewCountRenderer']['viewCount']['runs'][0]['text']
                    if 'watching' in viewers:
                        self.is_live = True
                    else:
                        self.is_live = False
                    self.num_viewers = viewers.replace(',','').replace(' watching now','').replace(' waiting','')
                except:
                    self.num_viewers = 0
                    self.is_live = False
            
            ## Number of likes
            tmp = resp_json['actions'][1]['updateToggleButtonTextAction']
            self.num_likes = tmp['defaultText']['simpleText']
            
            ## Number of dislikes
            tmp = resp_json['actions'][2]['updateToggleButtonTextAction']
            self.num_dislikes = tmp['defaultText']['simpleText']
            
            ## Video title
            try:
                self.video_name = resp_json['actions'][4]['updateTitleAction']['title']['simpleText']
            except IndexError:
                pass
            
#            print(self.num_likes,self.num_dislikes,self.num_viewers,self.video_name)
            
            if self.stop:
                1/0
                exit(-1)
            
            data = {'likes':self.num_likes,
                    'dislikes':self.num_dislikes,
                    'viewers':self.num_viewers,
                    'og-likes':self.num_og_likes,
                    'og-dislikes':self.num_og_dislikes,
                    'live':self.is_live,
                    'timestamp':time()
                    }
            self.append_stats(data)
            
            self.stats_waiting = True
            # Set timeout
            sleep(self.stats_timeout)
            
    def request_second_continuation(self):
        headers = {
                'Host': 'www.youtube.com',
                'User-Agent': self.user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-GB,en;q=0.5',
#                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': '{}watch?v={}'.format(self.base_url,self.video_id),
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'TE': 'Trailers'
                }
        self.session_comments.headers = headers
        
        url = '{}live_chat?continuation={}'.format(self.base_url,self.req_comment_continuation)
        
        r = self.session_comments.get(url)
        
        if r.status_code != 200:
            print('oh dear... can`t find initial comments continuation... Error {}'.format(r.status_code))
            exit(r.status_code)
        
        resp_html = r.text
        
        # Extract continuation
        matches = re.findall('continuations\":(\[.*?\])',resp_html)
        
        while 1:
            try:
                cont_json = json.loads(matches[0])
                break
            except:
                print('failed to find continuation.. retrying in 5 seconds')
                sleep(5)
                
        
        self.comment_timeout = cont_json[0]['timedContinuationData']['timeoutMs']/1000
        continuation = cont_json[0]['timedContinuationData']['continuation']
        self.update_comment_continuation(continuation)
    def request_comments(self):
        # Make initial comment request
        self.request_second_continuation()
        referer_url = '{}live_chat?continuation={}'.format(self.base_url,self.req_comment_continuation)
        sleep(self.comment_timeout)
        # Set headers
        headers = {
                'Host': 'www.youtube.com',
                'User-Agent': self.user_agent,
                'Accept': '*/*',
                'Accept-Language': 'en-GB,en;q=0.5',
#                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': referer_url,
                'Content-Type': 'application/json',
                'X-Goog-Visitor-Id': urlparse(self.req_visitorData).geturl(),
                'Origin': 'https://www.youtube.com',
                'Connection': 'keep-alive',
                'TE': 'Trailers'
                }
        self.session_comments.headers = headers
        
        part_url = '{}youtubei/v1/live_chat/get_live_chat?{}'
        param_commandMetadata = 'commandMetadata=%5Bobject%20Object%5D'
        param_continuation = 'continuation={}'.format(self.req_comment_continuation)
        param_pbj = 'pbj=1'
        param_key = 'key={}'.format(self.req_key)
        url_params = '{}&{}&{}&{}'.format(param_commandMetadata,param_continuation,
                                      param_pbj,param_key)
        url = part_url.format(self.base_url,url_params)
        x = threading.Thread(target=self.comments_worker,args=(url,))
        x.start()
        
    def comments_worker(self,url):
        while 1:
            self.comments_waiting = False
            r = self.session_stats.post(url,json=self.req_json.stats)
            
            if r.status_code != 200:
                print('YouTube says {} to metadata'.format(r.status_code))
                exit(r.status_code)
            
            resp_json = r.json()
            
            # Find continuation
            liveChatContinuation  = resp_json['continuationContents']['liveChatContinuation']
            tmp_json = liveChatContinuation['continuations'][0]['timedContinuationData']
            self.comment_timeout = tmp_json['timeoutMs']/1000
            continuation = tmp_json['continuation']
            self.update_comment_continuation(continuation)
            
#            comments_json = liveChatContinuation['actions']
#            num_comments = len(comments_json)
            #print('{} new comments'.format(num_comments))
            self.add_comments(parse_response(resp_json))
            if self.stop:
                1/0
            self.comments_waiting = True
            sleep(self.comment_timeout)
            
    def add_comments(self,data):
        for d in data:
            self.comments_hist.append(data)
    
    def get_comments(self):
#        if self.comments_waiting:
#            o = self.comments_hist[:]
#            self.comments_hist = []
#        else:
#            o = []
        o = self.comments_hist
        return o
    
    def get_stats(self):
#        if self.stats_waiting:
#            o = self.stats_hist[:]
#            self.stats_hist = []
#        else:
#            o = []
        o = self.stats_hist
        return o
            
        
L = LiveMachine('vltJw2n6X28')
L.request_stats()
if L.comments_enabled:
    L.request_comments()
else:
    print('Comments aren`t enabled')























#
#
#class LiveChatMachine(LiveMachine):
#    def __init__(self,vid_id,headers=None,user_agent=None):
#        self.visitor_data = None
#        self.session_id = None
#        self.csn = None
#        self.tracking_params = None
#        self.vid_id = vid_id
#        self.s = session()
#        
#        if not headers is None:
#            self.s.headers = headers
#        if user_agent is None:
#            self.s.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36'
#        else:
#            self.s.headers['User-Agent'] = user_agent
#    
#    def get_comment_sect(self,continuation=None):
#        url = 'https://www.youtube.com/live_chat?v={}'.format(self.vid_id)
##        html_resp = self.s.get(url)
##        if continuation is None:
##            # Find continuation
##            pass
##        
##        if self.session_id is None:
##            pass
#            
##        url = 'https://www.youtube.com/live_chat?v={}&pbj=1'.format(vid_id)
#
##        r=self.s.get(url)
#        
#        # Parse JSON
#        #file = r.json()
#    
##        with open("o.txt","w") as f:
##            f.write(json.dumps(file))