# -*- coding: utf-8 -*-

from collections import OrderedDict


class LLSIFAPI(object):
    def __init__(self, module, action):
        self.module = module
        self.action = action

    @property
    def uri(self):
        return '/main.php/{}/{}'.format(self.module, self.action)


IOS_HEADER = OrderedDict([
    ('UserAgent', '%E3%83%A9%E3%83%95%E3%82%99%E3%83%A9%E3%82%A4%E3%83%95%E3%82%99%EF%BC%81/3.2.2 CFNetwork/758.2.8 Darwin/15.0.0'),
    ('Client-Version', '17.7'),
    ('API-Model', 'straightforward'),
    ('Region', '392'),
    ('Time-Zone', 'GMT+8'),
    ('Bundle-Version', '3.2.2'),
    ('OS', 'iOS'),
    ('Content-Length', None),
    ('Platform-Type', 1),
    ('Application-ID', '626776655'),
    ('Authorize', None),
    ('Connection', 'keep-alive'),
    ('Accept-Language', 'zh-cn'),
    ('Debug', '1'),
    ('X-Message-Code', None),
    ('User-ID', None),
    ('Accept', '*/*'),
    ('Content-Type', None),
    ('Accept-Encoding', 'gzip, deflate'),
    ('OS-Version', 'iPhone8_1 iPhone 9.2'),
])

IOS_HEADER_AUTHKEY = OrderedDict([
    ('Accept', '*/*'),
    ('Time-Zone', 'GMT+8'),
    ('Authorize', None),
    ('API-Model', 'straightforward'),
    ('Client-Version', '17.7'),
    ('OS', 'iOS'),
    ('Accept-Language', 'zh-cn'),
    ('Accept-Encoding', 'gzip, deflate'),
    ('Debug', '1'),
    ('Content-Length', None),
    ('Region', '392'),
    ('UserAgent', '%E3%83%A9%E3%83%95%E3%82%99%E3%83%A9%E3%82%A4%E3%83%95%E3%82%99%EF%BC%81/3.2.2 CFNetwork/758.2.8 Darwin/15.0.0'),
    ('Bundle-Version', '3.2.2'),
    ('Connection', 'keep-alive'),
    ('OS-Version', 'iPhone8_1 iPhone 9.2'),
    ('Application-ID', '626776655'),
    ('Platform-Type', 1),
])

IOS_HEADER_WEBVIEW = OrderedDict([
    ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
    ('Time-Zone', 'GMT+8'),
    ('Authorize', None),
    ('API-Model', 'straightforward'),
    ('Client-Version', '17.7'),
    ('User-ID', None),
    ('OS', 'iOS'),
    ('Accept-Language', 'zh-cn'),
    ('Accept-Encoding', 'gzip, deflate'),
    ('Application-ID', '626776655'),
    ('Region', '392'),
    ('UserAgent', 'Mozilla/5.0 (iPhone; CPU iPhone OS 9_2_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Mobile/13D15'),
    ('Bundle-Version', '3.2.2'),
    ('Connection', 'keep-alive'),
    ('OS-Version', 'iPhone8_1 iPhone 9.2'),
])

AUTHORIZE_BASE = OrderedDict([
    ('consumerKey', 'lovelive_test'),
    ('timeStamp', None),
    ('version', '1.1'),
    ('token', None),
    ('nonce', None),
])

AUTHORIZE_BASE_WEBVIEW = OrderedDict([
    ('consumerKey', 'lovelive_test'),
    ('token', None),
    ('version', '1.1'),
    ('timeStamp', None),
    ('nonce', None),
])

AUTHORIZE_BASE_AUTHKEY = OrderedDict([
    ('consumerKey', 'lovelive_test'),
    ('timeStamp', None),
    ('version', '1.1'),
    ('nonce', None),
])

MAIN_ROUTER_MAP = {
    'auth_key': LLSIFAPI('login', 'authkey'),
    'login': LLSIFAPI('login', 'login'),
    'user_info': LLSIFAPI('user', 'userInfo'),
    'personal_notice': LLSIFAPI('personalnotice', 'get'),
    'tos': LLSIFAPI('tos', 'tosCheck'),
    'agree_tos': LLSIFAPI('tos', 'tosAgree'),
    'is_connected_llaccount': LLSIFAPI('platformAccount', 'isConnectedLlAccount'),
    'lbonus': LLSIFAPI('lbouns', 'execute'),
    'handover_start': LLSIFAPI('handover', 'start'),
    'handover_exec': LLSIFAPI('handover', 'exec'),
    'reward_list': LLSIFAPI('reward', 'rewardList'),
    'event_player_rank': LLSIFAPI('ranking', 'eventPlayer'),
    'general_player_rank': LLSIFAPI('ranking', 'player'),
    'friend_variety': LLSIFAPI('notice', 'noticeFriendVariety'),
    'friend_greetings': LLSIFAPI('notice', 'noticeFriendGreeting'),
    'friend_greetings_from_user': LLSIFAPI('notice', 'noticeUserGreetingHistory'),
    'secretbox_list': LLSIFAPI('secretbox', 'all'),
    'secretbox_pull': LLSIFAPI('secretbox', 'pon'),
    'unit_merge': LLSIFAPI('unit', 'merge'),
    'unit_sale': LLSIFAPI('unit', 'sale'),
    'unit_rankup': LLSIFAPI('unit', 'rankUp'),
    'unit_favorite': LLSIFAPI('unit', 'favorite'),
    'product_list': LLSIFAPI('payment', 'productList'),
    'background_list': LLSIFAPI('background', 'set'),
    'award_set': LLSIFAPI('award', 'set'),
    'unaccomplished_achievement': LLSIFAPI('achievement', 'unaccomplishList'),
    'payment_month': LLSIFAPI('payment', 'month'),
    'payment_monthly_history': LLSIFAPI('payment', 'history'),
    'live_friend_list': LLSIFAPI('live', 'partyList'),
    'live_deck_list': LLSIFAPI('live', 'deckList'),
    'live_start': LLSIFAPI('live', 'play'),
    'live_finish': LLSIFAPI('live', 'reward'),
}

WEBVIEW_URL_TEMPLATE = '/webview.php/{}/index?0='
