# -*- coding: utf-8 -*-
"""
Worker class which immitates the browser behaviour

1) LiveStats
2) LiveComments
"""
import os
from requests import session
import re
from random import random
from urllib.parse import urlparse
from time import sleep
from time import time
import json
import threading
from YTLiveScrape.CommentsParser import parse_response
from YTLiveScrape.RequestJSONGenerator import RequestJSONGenerator
#from RequestJSONGenerator import RequestJSONGenerator
#from CommentsParser import parse_response

class LiveMachine():
    def __init__(self,video_id,cookies=None):
        print('Initialising LiveMachine for {}'.format(video_id))
        self.initialised = False
        self.cookies = cookies
        self.session = session()
                
        self.base_url = 'https://www.youtube.com/'
        self.video_id = video_id
        self.watch_url = '{}watch?v={}'.format(self.base_url,self.video_id)        
        
        self.user_agent = self.get_user_agent()
        self.check_config()
        
        self.status = {'code':0,'text':'all is good','warnings':[]}
        self.req_key = None
        self.req_serializedEventId = None
        self.req_sessionId = None
        self.req_clickTrackingParams = None
        self.req_CSN = self.create_csn()
        self.req_comment_continuation = None
        self.req_stats_continuation = None
        self.req_visitorData = None

        self.channel_id = ''
        self.video_author = ''
        self.video_name = ''
        self.is_live = False
        self.is_a_stream = False
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
        self.comments_running = False
        self.stats_running = False
        
        self.get_initial_data()
        if self.status['code'] == 6:
            print(self.status['text'])
            self.has_data = False
            return
        else:
            self.has_data = True
        
        if not self.cookies is None:
            self.session.cookies = self.cookies
        
        self.session_stats = self.session
        self.session_comments = self.session
        
#        self.get_initial_comment_continuation()
        
        
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
                'stats-continuation':self.req_stats_continuation,
                'comm-continuation':self.req_comment_continuation
                }
        
        self.req_json = RequestJSONGenerator(dataForJSON)
        self.initialised = True
        
    def stop_scrape(self):
        print('Stopping scrape')
        self.stop = True
        
                
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
                'Referer': '{}watch?v={}'.format(self.base_url,self.video_id),
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'TE': 'Trailers'
                }
        #url = self.base_url + 'live_chat?v={}'.format(self.video_id)
        print(self.req_comment_continuation)
        url = self.base_url + 'live_chat?continuation={}'.format(self.req_comment_continuation)
        self.session_comments.headers = headers
        r = self.session_comments.get(url)
        
        if r.status_code != 200:
            print('YouTube says {}. bad user!'.format(r.status_code))
            self.status['code'] = r.status_code
            self.status['text'] = 'failed to get initial comment continuation.'
            self.stop_scrape()
            return
        
        resp_html = r.text
        
        # with open('o.html','w',encoding='utf8') as f:
        #     f.write(resp_html)
    
    def check_config(self):
        if os.path.exists('browserdetails.config'):
            self.config_exists = True
            with open('browserdetails.config','r',encoding='utf-8') as f:
                details = json.loads(f.read())
                # self.req_key = details['req_key']
                # self.req_serializedEventId = details['req_serializedEventId']
                # self.req_sessionId = details['req_sessionId']
                # self.req_clickTrackingParams = details['req_clickTrackingParams']
                self.req_visitorData = details['req_visitorData']
        else:
            self.config_exists = False
    
    def get_initial_data(self,dbg=False):
        dbg = True
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
        user_details = {}
        self.session.headers = headers
        
        r = self.session.get(self.watch_url)
                
        if r.status_code != 200:
            print('YouTube frowns with Error {} on its face'.format(r.status_code))
            self.status['code'] = r.status_code
            self.status['text'] = 'YouTube frowns with Error {} on its face'.format(r.status_code)
            self.stop_scrape()
            return
                
        resp_html = r.text
        
#        with open('o.html','w',encoding='utf8') as f:
#            f.write(resp_html)
        
        # Find liveChat continuation parameter in HTML
        try:
            match = re.findall('"liveChatRenderer"(.*?)continuation":"(.*?)"',resp_html)
            self.update_comment_continuation(match[-1][1])
            self.comments_enabled = True
        except:
            self.comments_enabled = False
            print('{} comments aren`t enabled'.format(self.video_id))
        
        # Find key parameter -- "innertubeApiKey"
        try:
            match = re.findall('"isLiveContent":[truefalse]+',resp_html)[0]
            tmp = match.replace('"','').replace(':','').replace('isLiveContent','')
            if tmp == 'true':
                self.is_a_stream = True
            elif tmp == 'false':
                self.is_a_stream = False
                return
            else:
                print('cannot decide whether {} is a stream'.format(self.video_id))
                self.status['code'] = 7
                self.status['text'] = 'cannot decide whether video is a stream'
                return
        except IndexError:
            if dbg:
                print("Can't find the 'isLiveContent' in the initial request, " +
                  'reverting to False')
            self.status['warnings'].append('Can\'t find the \'isLiveContent\' in the initial request')
            self.is_a_stream = False
        
        try:
            match = re.findall('"isLiveContent":[truefalse]+',resp_html)[0]
        except:
            self.status['code'] = 6
            self.status['text'] = 'cannot load the page {} probably wrong url'.format(self.video_id)
            return
        tmp = match.replace('"','').replace(':','').replace('isLiveContent','')
        
        # user_details['isLive'] = tmp
        
        if 'endTimestamp' in resp_html:
            self.status['code'] = 6
            self.status['text'] = 'no live data'
            self.is_live = False
            return
                
        # Find channel Id -- browseId
        try:
            match = re.findall('"browseId":"(.*?)"',resp_html)[0]
            self.channel_id = match.replace('"','').replace(':','').replace('browseId','')
        except IndexError:
            if dbg:
                print("Can't find the 'browseId/channel_id' in the initial request, " +
                  '')
            self.status['warnings'].append('failed to find the channel id')
            self.channel_id = 'AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8'

            # user_details['channel_id'] = self.channel_id
        
        # if not self.config_exists:
        # Find key parameter -- "innertubeApiKey"
        try:
            match = re.findall('"innertubeApiKey":"[aA0-zZ9_]+"',resp_html)[0]
            self.req_key = match.replace('"','').replace(':','').replace('innertubeApiKey','')
        except IndexError:
            if dbg:
                print("Can't find the 'innertubeApiKey/key' in the initial request, " +
                  'reverting to AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8')
            self.status['warnings'].append('Can\'t find the \'innertubeApiKey/key\' in the initial request')
            self.req_key = 'AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8'
        
        # user_details['req_key'] = self.req_key
    
        # Find EVENT_ID -- "serializedEventId"
        try:
            match = re.findall('"EVENT_ID":"[aA0-zZ9_]+"',resp_html)[0]
            self.req_serializedEventId = match.replace('"','').replace(':','').replace('EVENT_ID','')
        except IndexError:
            if dbg:
                print("Can't find the 'EVENT_ID/serializedEventId' in the initial request, "+
                  'reverting to 5_NdX_76Mczj0wXb26bwCA')
            self.status['warnings'].append('Can\'t find the \'EVENT_ID/serializedEventId\' in the initial request')
            self.req_serializedEventId = '5_NdX_76Mczj0wXb26bwCA'
        
        # user_details['req_serializedEventId'] = self.req_serializedEventId
        
        # Find sessionId -- "sessionId"
        try:
            match = re.findall('"sessionId":"[aA0-zZ9_]+"',resp_html)[0]
            self.req_sessionId = match.replace('"','').replace(':','').replace('sessionId','')
        except IndexError:
            if dbg:
                print("Can't find the 'sessionId/sessionId' in the initial request, "+
                  'reverting to 6871917207188534706')
            self.status['warnings'].append('Can\'t find the \'sessionId/sessionId\' in the initial request')
            self.req_sessionId = '6871917207188534706'
        
        # user_details['req_sessionId'] = self.req_sessionId
        
        # Find clickTrackingParams -- "clickTrackingParams"
        try:
            match = re.findall('"clickTrackingParams":"[aA0-zZ9_]+"',resp_html)[0]
            self.req_clickTrackingParams = match.replace('"','').replace(':','').replace('clickTrackingParams','')
        except IndexError:
            if dbg:
                print("Can't find the 'clickTrackingParams/clickTrackingParams' in the initial request, " + 
                  'reverting to CB0QtSwYACITCNvViKL25esCFUW8VQodD_8N5w==')
            self.status['warnings'].append('Can\'t find the \'clickTrackingParams/clickTrackingParams\' in the initial request')
            self.req_clickTrackingParams = 'CB0QtSwYACITCNvViKL25esCFUW8VQodD_8N5w=='
        
        # user_details['req_clickTrackingParams'] = self.req_clickTrackingParams
                
        # find visitorData -- in VISITOR_DATA
        if not self.config_exists:
            try:
                match = re.findall('"VISITOR_DATA":"[aA0-zZ9_]+"',resp_html)[0]
                self.req_visitorData = match.replace('"','').replace(':','').replace('VISITOR_DATA','')
            except IndexError:
                if dbg:
                    print("Can't find the 'VISITOR_DATA/visitorData' in the initial request, " +
                      'reverting to CgtQMm9EN0ctb1RDSSjcvfj6BQ%3D%3D')
                self.status['warnings'].append('Can\'t find the \'VISITOR_DATA/visitorData\' in the initial request')
                self.req_visitorData = 'CgtQMm9EN0ctb1RDSSjcvfj6BQ%3D%3D'
            
            user_details['req_visitorData'] = self.req_visitorData

        # find channelId-- in channelId
        try:
            match = re.findall('author":"(.*?)"',resp_html)[0]            
            self.video_author = match.replace('"','').replace(':','').replace('author','')
        except IndexError:
            if dbg:
                print("Can't find the author, reverting to 'NO_CHANNEL'")
            self.status['warnings'].append('Can\'t find the channelId, reverting to \'NO_CHANNEL\'')
            self.video_author = 'NO_CHANNEL'
        
        # find likes in HTML
        try:
            match = re.findall('[aA0-zZ9,]+ likes',resp_html)[0]            
            self.num_og_likes = match.replace(' likes','').replace(',','')
            if 'No' in self.num_og_likes:
                self.num_og_likes = 0
        except IndexError:
            if dbg:
                print("Can't find the number of likes, reverting to 0")
            self.status['warnings'].append('Can\'t find the number of likes, reverting to 0')
            self.num_og_likes = 0
        
        # find dislikes in HTML
        try:
            match = re.findall('[aA0-zZ9,]+ dislikes',resp_html)[0]            
            self.num_og_dislikes = match.replace(' dislikes','').replace(',','')
            if 'No' in self.num_og_dislikes:
                self.num_og_dislikes = 0
        except IndexError:
            if dbg:
                print("Can't find the number of dislikes, reverting to 0")
            self.status['warnings'].append('Can\'t find the number of dislikes, reverting to 0')
            self.num_og_dislikes = 0
            
        # find start timestamp in the HTML
        try:
            match = re.findall('startTimestamp":"[0-9\-\:+T]+',resp_html)[0]            
            self.timestamp_start = match.replace('startTimestamp','').replace('"','').replace(':','')
        except IndexError:
            if dbg:
                print("Can't find the startTimestamp, reverting to ''")
            self.status['warnings'].append('Can\'t find the startTimestamp, reverting to \'\'')
            self.timestamp_start = ''

        if not self.config_exists:
            with open('browserdetails.config','w') as f:
                f.write(json.dumps(user_details))
        
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
        if not self.is_a_stream:
            print('{} is not a stream. cannot track live stats'.format(self.video_id))
            return
        if not self.has_data:
            raise NotImplementedError('I will implement scraping of old streams later. for now only works with `L.has_data==True`')
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
        x.daemon = True
        x.start()

        
    def stats_worker(self,url):
        while 1:
            if self.stop:
                self.stats_running = False
                self.status['code'] = -1
                self.status['text'] = 'stopped'
                break
            
            self.stats_running = True
            self.stats_waiting = False
            r = self.session_stats.post(url,json=self.req_json.metadata)
            
            if r.status_code != 200:
                print('YouTube says {} to metadata'.format(r.status_code))
                exit(r.status_code)
            
            resp_json = r.json()
            
            try:
                # Update continuation value
                tmp = resp_json['continuation']['timedContinuationData']
                continuation = tmp['continuation']
                self.stats_timeout = tmp['timeoutMs']/1000
            except:
                self.stats_running = False
                self.comments_running = False
                self.stop_scrape()
                self.status['code'] = 2
                self.status['text'] = 'stream is offline'
                return
            
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
            
            
            # find whether stream has finished
            try:
                #f.write(resp_json)
                ttt = resp_json['actions'][3]
                if ttt != '':
                    if 'Streamed' in ttt['updateDateTextAction']['dateText']['simpleText']:
                        print('{} stopped streaming... quiting...'.format(self.video_id))
                        self.stop_scrape()
                        break
            except:
                pass
            
            ## Video title
            try:
                self.video_name = resp_json['actions'][4]['updateTitleAction']['title']['simpleText']
            except:
                pass
            
#            print(self.num_likes,self.num_dislikes,self.num_viewers,self.video_name)
                        
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
            msg = 'oh dear... can`t find initial comments continuation... Error {}'.format(r.status_code)
            print(msg)
            self.status['code'] = r.status_code
            self.status['text'] = msg
            return
#            exit(r.status_code)
        
        resp_html = r.text
        
#        with open('o.html','w',encoding='utf8') as f:
#            f.write(resp_html)
        
        # Extract continuation
#        matches = re.findall('continuations\":(\[.*?\])',resp_html)
#        matches =
        
#        while 1:
#            try:
#                cont_json = json.loads(matches[0])
#                break
#            except:
#                print('failed to find continuation.. retrying in 5 seconds')
#                sleep(5)
       
        try:
            matches = re.findall('\"(timeoutMs.*?")\,"clickTrackingParam',resp_html)
            cont_json = json.loads(matches[0])
            self.comment_timeout = cont_json['timeoutMs']/1000
            continuation = cont_json['continuation']
            self.update_comment_continuation(continuation)
        except:
            self.status['code'] = 3
            self.status['can`t find second continuation for comments..']
            return
#            continuation = '0ofMyAPGARpyQ2pnS0RRb0xTSEJtTmxRd1gzQllWRlVxSndvWVZVTm5lRlJRVkVaaVNXSkRWMlpVVWpsSk1pMDFVMlZSRWd0SWNHWTJWREJmY0ZoVVZSb1Q2cWpkdVFFTkNndEljR1kyVkRCZmNGaFVWU0FCS0FJJTNEKOmavZj_6OsCMAA4AEACShsIARAAGAAgADoAQABKAFDZl-Kd_-jrAlgDeABQ48SMmf_o6wJYkciam_3o6wJoBIIBAggEiAEAoAH5_-Wd_-jrAg%3D%3D'
#            self.update_comment_continuation(continuation)
#            self.comment_timeout = 5
    
    def request_first_continuation(self):
        headers = {
                'Host': 'www.youtube.com',
                'User-Agent': self.user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-GB,en;q=0.5',
#                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'TE': 'Trailers'
                }
        self.session_comments.headers = headers
        url = '{}live_chat?v={}'.format(self.base_url,self.video_id)
        
        
        r = self.session_comments.get(url)
        
        if r.status_code != 200:
            msg = 'YouTube says {}, goodluck!'
            print(msg)
            self.status['code'] = r.status_code
            self.status['text'] = msg
            return r.status_code
        
        # Get continuation
        resp_html = r.text
        
        matches = re.findall('("timeoutMs.*?")\,"clickTrackingParam',resp_html)
        
        out_dict = eval('{'+matches[0]+'}')
                
        self.comment_timeout = out_dict['timeoutMs']/1000
        self.update_comment_continuation(out_dict['continuation'])
        
        return 0
    
    def request_comments(self):
        if not self.is_a_stream:
            print('{} is not a stream. cannot track live comments'.format(self.video_id))
            return
        if not self.comments_enabled:
            print('{} comments aren`t enabled'.format(self.video_id))
            return
        if not self.has_data:
            raise NotImplementedError('I will implement scraping of old streams later. for now only works with `L.has_data==True`')
        # Make initial comment request
#        self.request_second_continuation()
        #if self.request_first_continuation() != 0:
        #    return -1
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
        
        
        x = threading.Thread(target=self.comments_worker)
        x.daemon = True
        x.start()
        
    def comments_worker(self):
#        part_url = '{}youtubei/v1/live_chat/get_live_chat?{}'
#        param_commandMetadata = 'commandMetadata=%5Bobject%20Object%5D'
#        param_pbj = 'pbj=1'
#        param_key = 'key={}'.format(self.req_key)
        
        while 1:
            if self.stop:
                self.comments_running = False
                self.status['code'] = -1
                self.status['text'] = 'stopped'
                break
            
#            param_continuation = 'continuation={}'.format(self.req_comment_continuation)
#            url_params = '{}&{}&{}&{}'.format(param_commandMetadata,param_continuation,
#                                      param_pbj,param_key)
#            
#            url = part_url.format(self.base_url,url_params)
            
            url = '{}youtubei/v1/live_chat/get_live_chat?key={}'.format(self.base_url,self.req_key)
            
            self.comments_running = True
            self.comments_waiting = False
            r = self.session_stats.post(url,json=self.req_json.comments)
                        
            if r.status_code != 200:
                print('YouTube says {} to comments'.format(r.status_code))
                exit(r.status_code)
            
            resp_json = r.json()
            
            
            try:
                # Find continuation
                liveChatContinuation  = resp_json['continuationContents']['liveChatContinuation']['continuations'][0]
                if 'invalidationContinuationData' in liveChatContinuation.keys():
                    tmp_json = liveChatContinuation['invalidationContinuationData']
                elif 'timedContinuationData' in liveChatContinuation.keys():
                    tmp_json = liveChatContinuation['timedContinuationData']
                self.comment_timeout = tmp_json['timeoutMs']/1000
                continuation = tmp_json['continuation']
            except KeyError:
                with open('o.txt','a',encoding='utf8') as f:
                    f.write(json.dumps(resp_json))
                self.status['code'] = 4
                self.status['text'] = 'failed to find continuation in comments worker'
                self.comments_running = False
#                print(resp_json)
                return
            self.update_comment_continuation(continuation)
            
            self.req_json.update_comments(continuation)
            
            #comments_json = liveChatContinuation['actions']
            
            self.add_comments(parse_response(resp_json))
            
            self.comments_waiting = True
            sleep(self.comment_timeout)
            
    def add_comments(self,data):
        if data is None:
            return
#        print(len(data))
        for d in data:
            self.comments_hist.append(d)
            # if d['is-member'] == 'True':
            #     print(d)
    
    def get_comments(self):
        if self.comments_waiting:
            o = self.comments_hist[:]
            self.comments_hist = []
        else:
            o = []
#        o = self.comments_hist
        return o
    
    def get_stats(self):
        if self.stats_waiting:
            o = self.stats_hist[:]
            self.stats_hist = []
        else:
            o = []
#        o = self.stats_hist
        return o
            
        
if __name__ == '__main__':
    L = LiveMachine('RNFByvEPVxo')
    if L.has_data:
        L.request_stats()
        if L.comments_enabled:
            L.request_comments()
            pass
        else:
            print('Comments aren`t enabled')
    
    #L.stop = True
