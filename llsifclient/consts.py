# -*- coding: utf-8 -*-

from collections import OrderedDict

from .api import LLSIFAPI


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
    'user_info': LLSIFAPI('user', 'userInfo'),
    'user_items': LLSIFAPI('user', 'showAllItem'),

    'auth_key': LLSIFAPI('login', 'authkey'),
    'login': LLSIFAPI('login', 'login', requires=['login_key', 'login_password'], excludes=['module', 'action', 'timeStamp', 'commandNum']),
    'top_info': LLSIFAPI('login', 'topInfo'),
    'top_info_once': LLSIFAPI('login', 'topInfoOnce'),

    'tos': LLSIFAPI('tos', 'tosCheck'),
    'agree_tos': LLSIFAPI('tos', 'tosAgree'),

    'handover_start': LLSIFAPI('handover', 'start'),
    'handover_exec': LLSIFAPI('handover', 'exec'),

    'reward_list': LLSIFAPI('reward', 'rewardList'),
    'reward_open': LLSIFAPI('reward', 'open'),
    'reward_openall': LLSIFAPI('reward', 'openAll'),

    'event_player_rank': LLSIFAPI('ranking', 'eventPlayer'),
    'general_player_rank': LLSIFAPI('ranking', 'player'),

    'friend_variety': LLSIFAPI('notice', 'noticeFriendVariety'),
    'friend_greetings': LLSIFAPI('notice', 'noticeFriendGreeting'),
    'friend_greetings_from_user': LLSIFAPI('notice', 'noticeUserGreetingHistory'),
    'notice_marquee': LLSIFAPI('notice', 'noticeMarquee'),

    'secretbox_list': LLSIFAPI('secretbox', 'all'),
    'secretbox_pull': LLSIFAPI('secretbox', 'pon'),

    'unit_merge': LLSIFAPI('unit', 'merge'),
    'unit_sale': LLSIFAPI('unit', 'sale'),
    'unit_rankup': LLSIFAPI('unit', 'rankUp'),
    'unit_favorite': LLSIFAPI('unit', 'favorite'),
    'unit_all': LLSIFAPI('unit', 'unitAll'),
    'unit_deck': LLSIFAPI('unit', 'deckInfo'),

    'product_list': LLSIFAPI('payment', 'productList'),
    'payment_month': LLSIFAPI('payment', 'month'),
    'payment_monthly_history': LLSIFAPI('payment', 'history'),

    'background_set': LLSIFAPI('background', 'set'),
    'background_info': LLSIFAPI('background', 'backgroundInfo'),

    'award_info': LLSIFAPI('award', 'awardInfo'),
    'award_set': LLSIFAPI('award', 'set'),

    'unaccomplished_achievement': LLSIFAPI('achievement', 'unaccomplishList'),

    'live_friend_list': LLSIFAPI('live', 'partyList', requires=['live_difficulty_id']),
    'live_deck_list': LLSIFAPI('live', 'deckList', requires=['party_user_id']),
    'live_start': LLSIFAPI('live', 'play', requires=['party_user_id', 'unit_deck_id', 'live_difficulty_id']),
    'live_finish': LLSIFAPI('live', 'reward', requires=['good_cnt', 'miss_cnt', 'great_cnt', 'love_cnt', 'max_combo',
                                                        'score_smile', 'perfect_cnt', 'bad_cnt', 'event_point', 'live_difficulty_id',
                                                        'score_cute', 'score_cool', 'event_id']),
    'live_status': LLSIFAPI('live', 'liveStatus'),
    'live_schedule': LLSIFAPI('live', 'liveSchedule'),

    'friend_list': LLSIFAPI('friend', 'list'),
    'friend_cancel_request': LLSIFAPI('friend', 'requestCancel'),
    'friend_req_response': LLSIFAPI('friend', 'response'),
    'friend_expel': LLSIFAPI('friend', 'expel'),

    'scenario_status': LLSIFAPI('scenario', 'scenarioStatus'),
    'scenario_reward': LLSIFAPI('scenario', 'reward', requires=['scenario_id']),
    'scenario_start': LLSIFAPI('scenario', 'startUp', requires=['scenario_id']),
    'subscenario_status': LLSIFAPI('subscenario', 'subscenarioStatus'),
    'eventscenario_status': LLSIFAPI('eventscenario', 'status'),

    'is_connected_llaccount': LLSIFAPI('platformAccount', 'isConnectedLlAccount', excludes=['timeStamp', 'commandNum']),
    'marathon_info': LLSIFAPI('marathon', 'marathonInfo'),
    'lbonus': LLSIFAPI('lbouns', 'execute'),
    'personal_notice': LLSIFAPI('personalnotice', 'get'),
    'battle_info': LLSIFAPI('battle', 'battleInfo'),
    'banner_list': LLSIFAPI('banner', 'bannerList'),
    'festival_info': LLSIFAPI('festival', 'festivalInfo'),
    'navigation_special_cutin': LLSIFAPI('navigation', 'specialCutin'),
    'all_album': LLSIFAPI('album', 'albumAll'),
    'online_info': LLSIFAPI('online', 'info'),
    'challenge_info': LLSIFAPI('challenge', 'challengeInfo'),

}

WEBVIEW_URL_TEMPLATE = '/webview.php/{}/index?0='
