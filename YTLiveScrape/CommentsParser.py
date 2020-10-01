# -*- coding: utf-8 -*-
"""
Parse YoutTube comments JSON
"""

def parse_response(json_data):
    count = 0
    
    # Try to extract messages
    
    if not 'continuationContents' in json_data:
        return
    
    try:
        tmp = json_data['continuationContents']['liveChatContinuation']
    except KeyError:
        print(json_data)
        return
    
    try:
        chats = tmp['actions']
    except KeyError:
        return
        
    
    lines = []
    # Actions ...
    # 1) addLiveChatTickerItemAction
    # 2) addChatItemAction
    # 3) markChatItemAsDeletedAction
    for entry in chats:
        if 'addChatItemAction' in entry.keys():
            action = 'addChatItemAction'
            #print('addChatItemAction')
            child = entry['addChatItemAction']
        elif 'addLiveChatTickerItemAction' in entry.keys():
            action = 'addLiveChatTickerItemAction'
            #print('addLiveChatTickerItemAction')
            child = entry['addLiveChatTickerItemAction']
        elif 'markChatItemsByAuthorAsDeletedAction' in entry.keys():
            action = 'markChatItemsByAuthorAsDeletedAction'
            child = entry['markChatItemsByAuthorAsDeletedAction']
        elif 'markChatItemAsDeletedAction' in entry.keys():
            action = 'markChatItemAsDeletedAction'
            #print('markChatItemAsDeletedAction')
            child = entry['markChatItemAsDeletedAction']
        elif 'addBannerToLiveChatCommand' in entry.keys():
            continue
        elif 'showLiveChatTooltipCommand' in entry.keys():
            continue
        elif 'replaceChatItemAction' in entry.keys():
            continue
        else:
            print(entry.keys())
        #print(child)
        keys = child.keys()
        
        clientId = ''
        timestamp = ''
        photo = ''
        authorName = ''
        message = ''
        value = ''
        channelId = ''
        is_member = 'False'
        
        if 'clientId' in keys:
            clientId = child['clientId']
            count += 1
        elif 'deletedStateMessage' in keys or 'liveChatViewerEngagementMessageRenderer' in keys:
            continue
        else:
            count += 1
            
#        print("\n\n")
#        print(child.keys())
#        print(child)
        
        c1 = child['item']
        
        if 'liveChatTextMessageRenderer' in c1.keys():
            c2 = c1['liveChatTextMessageRenderer']
#            print("\n\n")
#            print(c2.keys())
#            print(c2)
            
            if 'authorBadges' in c2.keys():
                is_member = 'True'
            
            timestamp = c2['timestampUsec']
            authorName = c2['authorName']['simpleText']
            
            msg_runs = c2['message']['runs']
            
            for msg in msg_runs:
                msg_keys = msg.keys()
                if 'text' in msg_keys:
                    message += msg['text'] + ' '
                if 'emoji' in msg:
                    message += msg['emoji']['shortcuts'][0] + ' '
#                    print(msg_runs)
#                    1/0
#            for msg in c2['message']['runs']:
#                message += '**__**' + msg['text']
            photo = c2['authorPhoto']['thumbnails'][0]['url']
#            print(timestamp,authorName,message)
        elif 'liveChatPlaceholderItemRenderer' in c1.keys():
            # Not interesting
            continue
        elif 'liveChatTickerSponsorItemRenderer' in c1.keys():
            # Someone joined 1st, 2nd, etc tier message
            
            c2 = c1['liveChatTickerSponsorItemRenderer']
            if 'authoBadges' in c2.keys():
                is_member = 'True'
#            print("\n\n")
            channelId = c2['authorExternalChannelId']
            photo = c2['sponsorPhoto']['thumbnails'][0]['url']
            
            c3 = c2['showItemEndpoint']['showLiveChatItemEndpoint']
            c4 = c3['renderer']['liveChatMembershipItemRenderer']
            
            timestamp = c4['timestampUsec']
            authorName = c4['authorName']['simpleText']
            
#            print(timestamp,authorName)
#            print(c2)
#            print(c2.keys())
        elif 'liveChatPaidMessageRenderer' in c1.keys():
            # Paid message banner
            
            c2 = c1['liveChatPaidMessageRenderer']
            
            if 'authorBadges' in c2.keys():
                is_member = 'True'
            
            timestamp = c2['timestampUsec']
            authorName = c2['authorName']['simpleText']
            value = c2['purchaseAmountText']['simpleText']
            photo = c2['authorPhoto']['thumbnails'][0]['url']
            channelId = c2['authorExternalChannelId']
            
            
            if 'message' in c2.keys():
                msg_runs = c2['message']['runs']
                
                for msg in msg_runs:
                    msg_keys = msg.keys()
                    if 'text' in msg_keys:
                        message += msg['text'] + ' '
                    if 'emoji' in msg:
                        message += msg['emoji']['shortcuts'][0] + ' '
            
#            print("\n\n")
#            print(value)
        elif 'liveChatViewerEngagementMessageRenderer' in c1.keys():
            # Not interesting. YouTube welcome message
            continue
        elif 'liveChatTickerPaidMessageItemRenderer'  in c1.keys():
            c2 = c1['liveChatTickerPaidMessageItemRenderer']
            
            if 'authorBadges' in c2.keys():
                is_member = 'True'
            
            #timestamp = 
            channelId = c2['authorExternalChannelId']
            value = c2['amount']['simpleText']
            photo = c2['authorPhoto']['thumbnails'][0]['url']
            
            c3 = c2['showItemEndpoint']['showLiveChatItemEndpoint']['renderer']
            c4 = c3['liveChatPaidMessageRenderer']
            
            authorName = c4['authorName']['simpleText']
            timestamp = c4['timestampUsec']
            
            if 'message' in c4.keys():
                msg_runs = c4['message']['runs']
                
                for msg in msg_runs:
                    msg_keys = msg.keys()
                    if 'text' in msg_keys:
                        message += msg['text'] + ' '
                    if 'emoji' in msg:
                        message += msg['emoji']['shortcuts'][0] + ' '
#            
#            print("\n\n")
#            print(c2)
#            print(c1.keys())
        elif 'liveChatMembershipItemRenderer' in c1.keys():
            c2 = c1['liveChatMembershipItemRenderer']
            
            if 'authorBadges' in c2.keys():
                is_member = 'True'
            
            timestamp = c2['timestampUsec']
            channelId = c2['authorExternalChannelId']
            authorName = c2['authorName']['simpleText']
            photo = c2['authorPhoto']['thumbnails'][0]['url']
#            print("\n\n")
#            print(c2)
#            print(c1.keys())
        elif 'liveChatPaidStickerRenderer' in c1.keys():
            c2 = c1['liveChatPaidStickerRenderer']
            
            if 'authorBadges' in c2.keys():
                is_member = 'True'
            
            timestamp = c2['timestampUsec']
            channelId = c2['authorExternalChannelId']
            authorName = c2['authorName']['simpleText']
            photo = c2['authorPhoto']['thumbnails'][0]['url']
            value = c2['purchaseAmountText']['simpleText']
            
#            print("\n\n")
#            print(c2)
#            print(c1.keys())
        elif 'liveChatTickerPaidStickerItemRenderer' in c1.keys():
            c2 = c1['liveChatTickerPaidStickerItemRenderer']
            
            if 'authorBadges' in c2.keys():
                is_member = 'True'
            
            channelId = c2['authorExternalChannelId']
            photo = c2['authorPhoto']['thumbnails'][0]['url']
            
            c3 = c2['showItemEndpoint']['showLiveChatItemEndpoint']['renderer']['liveChatPaidStickerRenderer']
            timestamp = c3['timestampUsec']
            value = c3['purchaseAmountText']['simpleText']
            authorName = c3['authorName']['simpleText']
        elif 'liveChatModeChangeMessageRenderer' in c1.keys():
            # Not interesting
            continue
        else:
            print("\n\n")
            print(c1.keys())
            print(c1)
            1/0
        
        # pass
        
        
        line = {'clientId':clientId,
                'timestamp':timestamp,
                'photo':photo,
                'authorName':authorName,
                'message':message,
                'value':value,
                'is-member':is_member,
                'channelId':channelId}
        lines.append(line)
    return lines
