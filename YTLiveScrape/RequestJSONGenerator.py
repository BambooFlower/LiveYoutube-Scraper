# -*- coding: utf-8 -*-
class RequestJSONGenerator():
    def __init__(self,data):
        self.clickTrackingParams = data['clickTrackingParams']
        self.visitordata = data['visitorData']
        self.clientScreenNonce = data['clientScreenNonce']
        self.sessionId = data['sessionId']
        self.userAgent = data['userAgent']
        self.videoId = data['videoId']
        self.stats_continuation = data['stats-continuation']
        self.comm_continuation = data['comm-continuation']
        
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
                
        self.comments_running = False
        self.stats_running = False
        
        self.metadata = self.gen_metadata_json()
        self.comments = self.gen_good_comments_json()
    
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
    
    def gen_good_comments_json(self):
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
        context = {'adSignalsInfo':adSignalsInfo,
                   'clickTracking':clickTracking,
                   'client':client,
                   'clientScreenNonce':self.clientScreenNonce,
                   'request':request,
                   'user':{}
                   }
        o= {'context':context,
            'continuation':self.comm_continuation,'webClientInfo':{'isDocumentHidden':False}}
        return o
    
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
    
    def update_comments(self,continuation):
        self.comments['continuation'] = continuation
    
    def update_metadata(self,continuation):
        try:
            self.metadata.pop('videoId')
        except KeyError:
            pass
        self.metadata['continuation'] = continuation