"""A partial implementation of Love Live School Idol Festival client.

This is a partial implementation of the game client of Love Live School Idol
Festival, specifically the Japanese Android edition. The
implementation covers registering new accounts, issuing and using transfer
codes, logging in to existing accounts, free and premium drawing and some
deck management.

Note this class is not usable out of the box. At the very least, you have to
provide the correct gen_xmessagecode() function. You should also make sure
Client-Version matches with the server, otherwise you will be prompted to
"update".
Look for # CUSTOMIZATION in the source code.

The API should be compatible for minor version bumps of Client-Version, but
most likely incompatible across major version changes.


To register new account, do something like:
    client = LLSIFClient()
    newloginkey, newloginpasswd = client.gen_new_credentials()
    client.register_new_account(newloginkey, newloginpasswd)

To use a transfer code, do something like:
    client = LLSIFClient()
    newloginkey, newloginpasswd = client.gen_new_credentials()
    client.account_from_transfer_code(newloginkey, newloginpasswd, code)

To simulate launching the game client, do something like:
    client = LLSIFClient()
    userinfo, allinfo, connst = client.startapp(loginkey, loginpasswd)

"""

from collections import OrderedDict
import time
import logging
import http.client
import socket
import zlib
import json
import re
import copy
import random

from . import gen_xmessagecode


logger = logging.getLogger(__name__)


class LLSIFClient:
    """Love Live School Idol Festival client class."""

    # Constants
    SERVER_HOST = 'prod-jp.lovelive.ge.klabgames.net'
    DEF_HEADERS = OrderedDict([
        ('Accept', '*/*'),
        ('Accept-Encoding', 'gzip,deflate'),
        ('API-Model', 'straightforward'),
        ('Debug', '1'),
        ('Bundle-Version', '3.2.1'),
        # CUSTOMIZATION: Must match server version
        ('Client-Version', '17.3'),
        # CUSTOMIZATION: model of the "phone/tablet" you're "playing" on
        ('OS-Version', 'Nexus 6 google shamu 5.0'),
        # ro.product.model, ro.product.brand, ro.product.board, ro.build.version.release
        ('OS', 'Android'),
        ('Platform-Type', '2'),
        ('Application-ID', '626776655'),
        ('Time-Zone', 'JST'),
        ('Region', '392'),
        ('Authorize', None),
        ('User-ID', None),
        ('X-Message-Code', None)])
    DEF_AUTHORIZE = OrderedDict([
        ('consumerKey', 'lovelive_test'),
        ('timeStamp', None),
        ('version', '1.1'),
        ('token', None),
        ('nonce', None)])
    INCENTIVE_ITEM = {1: 'Scouting Ticket',
                      2: 'Friend pt',
                      3: 'G',
                      4: 'Loveca stone',
                      5: 'Assist Voucher'}
    DEF_NAMES = '''幻の学院生 明るい学院生 期待の学院生 純粋な学院生 素直な学院生
        元気な学院生 天然な学院生 勇敢な学院生 気になる学院生 真面目な学院生
        不思議な学院生 癒し系な学院生 心優しい学院生 さわやかな学院生
        頼りになる学院生 さすらいの学院生 正義感あふれる学院生 カラオケ好きの学院生'''.split()

    class LLSIFError(Exception):
        '''Base exception for this module.'''
        pass

    class LLSIFAPIError(LLSIFError):
        '''Exception raised when an API call responded with error_code.

        Attributes:
            error_code
            status_code

        In the docstring of some methods below, known codes are documented.
        '''
        def __init__(self, error_code, status_code):
            self.error_code = error_code
            self.status_code = status_code

        def __str__(self):
            return 'error_code: {:d}, status_code: {:d}'.format(
                self.error_code, self.status_code)

    def __init__(self):
        self.session = {'loginkey': None, 'userid': None, 'token': None,
                        'nonce': 0, 'commandnum': 0, 'wv_header': None,
                        'last_command': None, 'last_login': None}

    def start_session(self):
        '''Start new session by obtaining authorize_token from server.

        The authorize_token is saved to this instance of LLSIFClient, and will
        be used for future API calls.'''

        logger.info('Start new session')

        # Reset self.session
        self.session['loginkey'] = None
        self.session['userid'] = None
        self.session['token'] = None
        self.session['nonce'] = 0
        self.session['commandnum'] = 0
        self.session['wv_header'] = None
        self.session['last_command'] = None
        self.session['last_login'] = None

        respobj = self.api_single_request(None, '/main.php/login/authkey')

        self.session['token'] = respobj['response_data']['authorize_token']
        logger.info('Acquired auth token from server')
        logger.debug(self.session['token'])

        return respobj

    def login(self, login_key, login_passwd):
        '''Login to server with login_key and login_password.

        A new authorize_token will be issued and saved.

        Known error codes:
        If transfer code has been used elsewhere, server returns
        {"response_data":{"error_code":407},"status_code":600}'''

        logger.info('Logging in')

        requestdata = OrderedDict([('login_key', login_key),
                                   ('login_passwd', login_passwd)])
        # CUSTOMIZATION: Optionally, also include ('devtoken', GCM registration ID)

        respobj = self.api_single_request(requestdata, '/main.php/login/login')

        # sanity checks
        if respobj['status_code'] != 200:
            logger.error('Login returned status code: %d',
                         respobj['status_code'])
            if respobj['response_data']['error_code'] == 407:
                logger.error('Reason: transfer code used elsewhere')
            raise self.LLSIFAPIError(respobj['response_data']['error_code'],
                                     respobj['status_code'])

        if respobj['response_data']['review_version']:
            logger.warning('review_version: %s',
                           respobj['response_data']['review_version'])

        self.session['token'] = respobj['response_data']['authorize_token']
        logger.info('Acquired auth token from server')
        logger.debug(self.session['token'])

        self.session['loginkey'] = login_key
        self.session['userid'] = respobj['response_data']['user_id']
        self.session['commandnum'] = 1
        self.session['last_login'] = time.time()

        return respobj

    def lbonus(self):
        '''Get and retrieve information about daily login bonuses.'''

        logger.info('Retrieving daily login bonuses')

        # This request has different order than most others
        requestdata = OrderedDict([('module', 'lbonus'),
                                   ('action', 'execute'),
                                   ('timeStamp', None),
                                   ('commandNum', None)])

        respobj = self.api_single_request(requestdata)

        return respobj

    def get_transfer_code(self):
        '''Retrieve transfer code of current account.'''

        logger.info('Retrieving transfer code')

        respobj = self.api_single_request(('handover', 'start'))

        return respobj

    def use_transfer_code(self, transfercode):
        '''Use transfer code.

        This associates the transferred account with currently used
        login_key and login_passwd.

        Real game client will restart after this operation.

        On success, respobj['response_data'] == True

        Known error codes:
        If incorrect code entered, returns
        {"response_data":{"error_code":4402},"status_code":600}'''

        logger.info('Using transfer code')

        requestdata = OrderedDict([('module', 'handover'),
                                   ('action', 'exec'),
                                   ('timeStamp', None),
                                   ('handover', transfercode),
                                   ('commandNum', None)])

        respobj = self.api_single_request(requestdata)

        return respobj

    def gen_new_credentials(self):
        '''Generate random login_key and login_passwd.'''

        newloginkey = '{:08x}-{:04x}-{:04x}-{:04x}-{:012x}'.format(
            random.randrange(16**8), random.randrange(16**4),
            random.randrange(16**4), random.randrange(16**4),
            random.randrange(16**12))
        newloginpasswd = '{:0128x}'.format(random.randrange(16**128))

        return (newloginkey, newloginpasswd)

    def register_new_account(self, newloginkey, newloginpasswd,
                             nickname=None, leader=None):
        '''Register new game account and complete all setup (tutorials, etc.)

        Returns login_key and login_passwd of the new account.'''

        logger.info('Creating new account')

        self.start_session()
        self.register_new_login(newloginkey, newloginpasswd)
        self.start_without_invite(newloginkey, newloginpasswd)

        self.start_session()
        self.login(newloginkey, newloginpasswd)
        userinfo = self.userinfo()
        tosstate = self.toscheck()

        # Insert wait here: changing name and agreeing to TOS
        logger.debug('Sleep for a bit...')
        time.sleep(random.uniform(1, 3))

        if not tosstate['response_data']['is_agreed']:
            self.tosagree(tosstate['response_data']['tos_id'])
        self.changename(random.choice(self.DEF_NAMES))
        self.tutorialprogress(1)

        self.startup_api_calls()

        self.unit_and_deck()

        unitlist = self.login_unitlist()
        available_units = [x['unit_initial_set_id'] for
                           x in unitlist['response_data']['unit_initial_set']]

        # Insert wait here: selecting leader
        logger.debug('Sleep for a bit...')
        time.sleep(random.uniform(3, 5))

        if leader not in available_units:
            leader = random.choice(available_units)
        self.login_unitselect(leader)
        self.tutorialskip()

        unitinfo = self.unit_and_deck()
        mergebase = unitinfo['response_data'][0]['result'][0]['unit_owning_user_id']
        mergepartners = [unitinfo['response_data'][0]
                                 ['result'][10]['unit_owning_user_id']]
        self.unitmerge(mergebase, mergepartners)

        self.tutorialskip()

        rankupbase = mergebase
        rankuppartner = unitinfo['response_data'][0]['result'][9]['unit_owning_user_id']
        self.unitrankup(rankupbase, rankuppartner)

        self.tutorialskip()

        return (newloginkey, newloginpasswd)

    def account_from_transfer_code(self, newloginkey, newloginpasswd,
                                   transfercode):
        '''Start a new game account by using a transfer code.

        Returns login_key and login_passwd of the new account.'''

        logger.info('Creating account from transfer code')
        logger.debug('Transfer code: %s', transfercode)

        self.start_session()
        self.register_new_login(newloginkey, newloginpasswd)
        self.start_without_invite(newloginkey, newloginpasswd)

        self.start_session()
        self.login(newloginkey, newloginpasswd)
        self.userinfo()
        self.toscheck()

        # Insert wait here: inputting transfer code
        logger.debug('Sleep for a bit...')
        time.sleep(random.uniform(1, 3))

        transferstate = self.use_transfer_code(transfercode)

        if transferstate['status_code'] != 200:
            logger.error('Using transfer code failed')
            logger.error(str(transferstate))
            if transferstate['response_data']['error_code'] == 4402:
                logger.error('Transfer code incorrect')
            raise self.LLSIFAPIError(transferstate['response_data']['error_code'],
                                     transferstate['status_code'])

        return (newloginkey, newloginpasswd)

    def startapp(self, loginkey, loginpasswd):
        '''Simulate starting the game client.

        Returns a 3-tuple of:
            the response to unitInfo
            the response to the bundle of startup API calls
            the response to connected account check'''

        self.start_session()
        self.login(loginkey, loginpasswd)

        userinfo = self.userinfo()
        self.personalnotice()

        tosstate = self.toscheck()
        if not tosstate['response_data']['is_agreed']:
            # Insert wait here: agreeing to TOS
            logger.debug('Sleep for a bit...')
            time.sleep(random.uniform(1, 3))
            self.tosagree(tosstate['response_data']['tos_id'])

        connectstate = self.checkconnectedaccount()
        self.lbonus()

        self.handle_webview_get_request('/webview.php/announce/index?0=')
        self.session['wv_header'] = None

        allinfo = self.startup_api_calls()

        return (userinfo, allinfo, connectstate)

    def register_new_login(self, newloginkey, newloginpasswd):
        '''Register new pair of login_key and login_passwd to the server.

        This is the first step of creating new account / using transfer code
        from fresh install.
        '''

        logger.info('Registering new credentials on server')
        logger.debug('New login_key: %s', newloginkey)
        logger.debug('New login_passwd: %s', newloginpasswd)

        requestdata = OrderedDict([('login_key', newloginkey),
                                   ('login_passwd', newloginpasswd)])
        # CUSTOMIZATION: Optionally, also include ('devtoken', GCM registration ID)

        respobj = self.api_single_request(requestdata, '/main.php/login/startUp')

        if respobj['status_code'] != 200:
            raise RuntimeError('/login/startUp returned status_code: %d',
                               respobj['status_code'])

        # sanity check
        if respobj['response_data']['login_key'] != newloginkey or \
                respobj['response_data']['login_passwd'] != newloginpasswd:
            logger.warning('Server returned different credentials')
            logger.warning(str(respobj))

        self.session['loginkey'] = newloginkey
        self.session['userid'] = respobj['response_data']['user_id']
        self.session['commandnum'] = 1
        self.session['last_login'] = time.time()

        return respobj

    def start_without_invite(self, loginkey, loginpasswd):
        '''Start new account from scratch.

        In real game client, this follows immediately after /login/startUp.
        '''

        logger.info('Starting new account from scratch')

        requestdata = OrderedDict([('login_key', loginkey),
                                   ('login_passwd', loginpasswd)])
        # does not include devtoken

        respobj = self.api_single_request(requestdata,
                                          '/main.php/login/startWithoutInvite')

        return respobj

    def userinfo(self):
        '''Acquire user info.'''

        logger.info('Acquiring user info')

        respobj = self.api_single_request(('user', 'userInfo'))

        if respobj['response_data']['user']['user_id'] != self.session['userid']:
            logger.warning('/user/userInfo returned different user_id %s',
                           respobj['response_data']['user']['user_id'])

        return respobj

    def toscheck(self):
        '''Check TOS agreement state.'''

        logger.info('Checking TOS state')

        respobj = self.api_single_request(('tos', 'tosCheck'))

        return respobj

    def tosagree(self, tosid):
        '''Agree to TOS.'''

        logger.info('Agreeing to TOS id: %d', tosid)

        requestdata = OrderedDict([('module', 'tos'),
                                   ('action', 'tosAgree'),
                                   ('timeStamp', None),
                                   ('tos_id', tosid),
                                   ('commandNum', None)])

        respobj = self.api_single_request(requestdata)

        return respobj

    def changename(self, nickname):
        '''Change nickname.'''

        logger.info('Changing player name to %s', nickname)

        requestdata = OrderedDict([('module', 'user'),
                                   ('action', 'changeName'),
                                   ('timeStamp', None),
                                   ('name', nickname),
                                   ('commandNum', None)])

        respobj = self.api_single_request(requestdata)

        return respobj

    def tutorialprogress(self, tutorialstate):
        '''Report tutorial progress.

        Required even if skipping the tutorial.'''

        logger.info('Tutorial progress %d', tutorialstate)

        requestdata = OrderedDict([('module', 'tutorial'),
                                   ('action', 'progress'),
                                   ('timeStamp', None),
                                   ('tutorial_state', tutorialstate),
                                   ('commandNum', None)])

        respobj = self.api_single_request(requestdata)

        return respobj

    def tutorialskip(self):
        '''Skip tutorial.'''

        logger.info('Skipping tutorial')

        respobj = self.api_single_request(('tutorial', 'skip'))

        return respobj

    def login_unitlist(self):
        '''Get a list of new account starting units(???).'''

        logger.info('Getting unit list')

        respobj = self.api_single_request(('login', 'unitList'))

        return respobj

    def login_unitselect(self, unit):
        '''Select among new account starting units.'''

        logger.info('Selecting unit %s', str(unit))

        requestdata = OrderedDict([('module', 'login'),
                                   ('action', 'unitSelect'),
                                   ('timeStamp', None),
                                   ('unit_initial_set_id', unit),
                                   ('commandNum', None)])

        respobj = self.api_single_request(requestdata)

        return respobj

    def unitmerge(self, base, partners):
        '''Merge player units, or "practice" in game terms.

        base is the "unit_owning_user_id" of the card, and
        partners is a list of "unit_owning_user_id"s of the fodders.'''

        logger.info('Merging units (practicing)')

        requestdata = OrderedDict([('module', 'unit'),
                                   ('unit_owning_user_ids', partners),
                                   ('action', 'merge'),
                                   ('timeStamp', None),
                                   ('base_owning_unit_user_id', base),
                                   ('commandNum', None)])

        respobj = self.api_single_request(requestdata)

        return respobj

    def unitrankup(self, base, partner):
        '''Rank-up player units, or "special practice / awakening" in game terms.

        base is the "unit_owning_user_id" of the card, and
        partners is the "unit_owning_user_id" of the fodder.
        '''

        logger.info('Ranking-up units (awakening)')

        requestdata = OrderedDict([('module', 'unit'),
                                   ('unit_owning_user_ids', [partner]),
                                   ('action', 'rankUp'),
                                   ('timeStamp', None),
                                   ('base_owning_unit_user_id', base),
                                   ('commandNum', None)])

        respobj = self.api_single_request(requestdata)

        return respobj

    def unitsale(self, units):
        '''Sell player units.

        units is a list of "unit_owning_user_id"s.
        '''

        logger.info('Selling units')

        requestdata = OrderedDict([('module', 'unit'),
                                   ('action', 'sale'),
                                   ('timeStamp', None),
                                   ('unit_owning_user_id', units),
                                   ('commandNum', None)])

        respobj = self.api_single_request(requestdata)

        return respobj

    def personalnotice(self):
        '''Not sure what this does.

        Example response:
        {"response_data":{"has_notice":false,"notice_id":0,"type":0,"title":"","contents":""},"status_code":200}'''

        logger.info('Personal Notice')

        respobj = self.api_single_request(('personalnotice', 'get'))

        if respobj['response_data']['has_notice']:
            logger.warning('Personal notice:')
            logger.warning(str(respobj))

        return respobj

    def startup_api_calls(self):
        '''Execute the "startup" API bundle.

        These calls are made right after logging in, and is used to populate
        the states of the actual game client. The client does not re-request
        these during gameplay.'''

        logger.info('Executing "startup" API bundle')

        apirequest = [('login', 'topInfo'),
                      ('live', 'liveStatus'),
                      ('live', 'schedule'),
                      ('marathon', 'marathonInfo'),
                      ('login', 'topInfoOnce'),
                      ('unit', 'unitAll'),
                      ('unit', 'deckInfo'),
                      ('payment', 'productList'),
                      ('scenario', 'scenarioStatus'),
                      ('subscenario', 'subscenarioStatus'),
                      ('user', 'showAllItem'),
                      ('battle', 'battleInfo'),
                      ('banner', 'bannerList'),
                      ('notice', 'noticeMarquee'),
                      ('festival', 'festivalInfo'),
                      ('eventscenario', 'status'),
                      ('navigation', 'specialCutin'),
                      ('album', 'albumAll'),
                      ('award', 'awardInfo'),
                      ('background', 'backgroundInfo'),
                      ('online', 'info'),
                      ('challenge', 'challengeInfo')]

        respobj = self.api_multiple_requests(apirequest)

        return respobj

    def unit_and_deck(self):
        '''Execute /unit/unitAll and unit/deckInfo.

        Common request to retrieve complete deck info.'''

        logger.info('Retrieving complete deck info')

        apirequest = [('unit', 'unitAll'),
                      ('unit', 'deckInfo')]

        respobj = self.api_multiple_requests(apirequest)

        return respobj

    def rewardlist_all(self):
        '''Retrieve list of presents.

        Emulates clicking on the present box in game client.

        order: 0 => date descending(default), 1 => date asc'''

        logger.info('Opening present box')

        apirequest = []

        for cat in range(0, 3):  # 0, 1, 2
            apirequest.append(OrderedDict([('module', 'reward'),
                                           ('action', 'rewardList'),
                                           ('timeStamp', None),
                                           ('order', 0),
                                           ('filter', [0]),
                                           ('category', cat)]))

        respobj = self.api_multiple_requests(apirequest)

        return respobj

    def rewardlist_pagedown(self, incentiveid, category):
        '''Return further parts of the present box contents.'''

        logger.info('Browsing present box')

        requestdata = OrderedDict([('module', 'reward'),
                                   ('filter', [0]),
                                   ('action', 'rewardList'),
                                   ('timeStamp', None),
                                   ('order', 0),
                                   ('category', category),
                                   ('incentive_id', incentiveid),
                                   ('commandNum', None)])

        respobj = self.api_single_request(requestdata)

        return respobj

    def rewardopen(self, incentiveid):
        '''Get a reward from present box.'''

        logger.info('Opening single reward')

        requestdata = OrderedDict([('module', 'reward'),
                                   ('action', 'open'),
                                   ('timeStamp', None),
                                   ('incentive_id', incentiveid),
                                   ('commandNum', None)])

        respobj = self.api_single_request(requestdata)

        return respobj

    def recruitinfo(self):
        '''Get information about all recruitment tabs.'''

        logger.info('Getting recruitment information')

        respobj = self.api_single_request(('secretbox', 'all'))

        return respobj

    def recruit(self, secretboxid, costpriority):
        '''Do a recruit.'''

        logger.info('Recruiting single member')

        requestdata = OrderedDict([('module', 'secretbox'),
                                   ('action', 'pon'),
                                   ('timeStamp', None),
                                   ('cost_priority', costpriority),
                                   ('secret_box_id', secretboxid),
                                   ('commandNum', None)])

        respobj = self.api_single_request(requestdata)

        return respobj

    def multirecruit(self, count, secretboxid, costpriority):
        '''Do a multi recruit.'''

        logger.info('Recruiting multiple members')

        requestdata = OrderedDict([('module', 'secretbox'),
                                   ('action', 'multi'),
                                   ('timeStamp', None),
                                   ('count', count),
                                   ('cost_priority', costpriority),
                                   ('secret_box_id', secretboxid),
                                   ('commandNum', None)])

        respobj = self.api_single_request(requestdata)

        return respobj

    def eventranking(self, rank, eventchildid):
        '''Retrieve event ranking data.

        Only jumping to specific rank is implemented. "Page turning" is not
        implemented.'''

        logger.info('Retrieving event ranking at {:d}'.format(rank))

        requestdata = OrderedDict([('module', 'ranking'),
                                   ('action', 'eventPlayer'),
                                   ('buff', 0),
                                   ('limit', 20),
                                   ('timeStamp', None),
                                   ('commandNum', None),
                                   ('event_child_id', eventchildid),
                                   ('rank', rank)])

        respobj = self.api_single_request(requestdata)

        return respobj

    def checkconnectedaccount(self):
        '''Check whether account is connected with Google+.'''

        logger.info('Checking whether account is connected to G+')

        requestdata = OrderedDict([('module', 'platformAccount'),
                                   ('action', 'isConnectedLlAccount')])

        respobj = self.api_single_request(requestdata)

        return respobj

    def api_single_request(self, request, url=None):
        '''Execute single API request.

        request should be any of the following:
            None, or
            a (module, action) tuple, or
            an (ordered) dictionary.

        Default url is /main.php/module/action.
        Submits requests like {"module":"","commandNum":"","action":"","timeStamp":""}'''

        logger.debug('Submitting API request %s', str(request))
        if url is None:
            try:
                url = '/'.join(['', 'main.php', request[0], request[1]])
            except KeyError:
                url = '/'.join(['', 'main.php', request['module'],
                                request['action']])
        logger.debug('request URL: %s', url)

        timestamp = str(int(time.time()))

        self.session['commandnum'] += 1

        if request is None:
            requestdata = None
        else:
            try:  # duck typing: tuple?
                requestdata = OrderedDict([
                    ('module', request[0]),
                    ('commandNum', self.session['loginkey'] + '.' + timestamp + '.' + str(self.session['commandnum'])),
                    ('action', request[1]),
                    ('timeStamp', timestamp)])
            except KeyError:  # duck typing: dict?
                requestdata = copy.deepcopy(request)
                if 'commandNum' in requestdata:
                    requestdata['commandNum'] = self.session['loginkey'] + '.' + timestamp + '.' + str(self.session['commandnum'])
                if 'timeStamp' in requestdata:
                    requestdata['timeStamp'] = timestamp

            requestjson = json.dumps(requestdata, separators=(',', ':'),
                                     ensure_ascii=False)
            logger.debug('JSON request-data: %s', requestjson)

            requestdata = requestjson.encode('utf-8')

        respstatus, respheaders, respbody, respobj = self.api_post_request(
            url, requestdata=requestdata, timestamp=timestamp)

        return respobj

    def api_multiple_requests(self, requests, url='/main.php/api'):
        '''Execute multiple API requests in one connection.

        requests should be a list of
        either (module, action) tuples, or
        (ordered) dictionaries.
        Submits requests like [{"module":"","action":"","timeStamp":""},...]'''

        logger.debug('Submitting multiple API requests in one connection')

        timestamp = str(int(time.time()))

        requestdata = []

        for request in requests:
            try:
                # logger.debug('module: %s, action: %s', request[0], request[1])
                requestdata.append(OrderedDict([('module', request[0]),
                                                ('action', request[1]),
                                                ('timeStamp', timestamp)]))
            except KeyError:
                temprequest = copy.deepcopy(request)
                if 'timeStamp' in temprequest:
                    temprequest['timeStamp'] = timestamp
                requestdata.append(temprequest)

        requestjson = json.dumps(requestdata, separators=(',', ':'),
                                 ensure_ascii=False)
        logger.debug('JSON request-data: %s', requestjson)

        requestdata = requestjson.encode('utf-8')

        respstatus, respheaders, respbody, respobj = self.api_post_request(
            url, requestdata=requestdata, timestamp=timestamp)

        return respobj

    def build_headers(self, timestamp, requestdata, nonce,
                      userid=None, token=None):
        '''Build HTTP headers and sign request_data for requests.'''

        logger.debug('Building HTTP headers')

        headers = copy.deepcopy(self.DEF_HEADERS)
        authorize_header = copy.deepcopy(self.DEF_AUTHORIZE)

        authorize_header['timeStamp'] = timestamp
        authorize_header['nonce'] = nonce

        if token is None:
            del authorize_header['token']
        else:
            authorize_header['token'] = token

        if userid is None:
            del headers['User-ID']
        else:
            headers['User-ID'] = userid

        headers['Authorize'] = '&'.join('{}={}'.format(*item) for
                                        item in authorize_header.items())
        logger.debug('Authorize header: %s', headers['Authorize'])

        if requestdata is None:
            del headers['X-Message-Code']
        else:
            headers['X-Message-Code'] = self.gen_xmessagecode(requestdata)

        return headers

    def gen_xmessagecode(self, data):
        '''Calculate X-Message-Code.

        The server will discard API calls without the correct X-Message-Code.
        This is one of the security measures of the game.'''

        # CUSTOMIZATION: provide the correct function here, or the client will
        # not work.
        return gen_xmessagecode.gen_xmessagecode(data)

    def multipart_form_data_enc(self, data):
        '''Create snippets for HTTP multipart encoding.

        The actual game client's implementation is different from Python's http
        libraries, and this implementation attempts to emulate the actual game
        client. The server will take any valid implementation, so this isn't
        strictly necessary, but whatever.'''

        boundary = '-' * 28 + \
                   '{:012x}'.format(random.randrange(16**12))
        body = b'--' + boundary.encode('utf-8') + b'\r\n' + \
               b'Content-Disposition: form-data; name="request_data"\r\n\r\n' +\
               data + b'\r\n--' + boundary.encode('utf-8') + b'--\r\n'
        contenttype = 'multipart/form-data; boundary=' + boundary

        return (contenttype, body)

    def api_post_request(self, url, requestdata=None, timestamp=None):
        '''Make HTTP POST request to server.

        Returns:
            HTTP status code,
            HTTP headers in the response as a list of tuples,
            body of the response (gunzipped if necessary), and
            body as decoded JSON objects (dicts, lists, etc)

        Known error codes:
        If transfer code has been used elsewhere, server returns 403 Forbidden
        and {"code":20001,"message":""} '''

        logger.debug('Making HTTP request')
        if not timestamp:
            timestamp = str(int(time.time()))
        self.session['nonce'] += 1

        headers = self.build_headers(
            timestamp, requestdata, self.session['nonce'],
            self.session['userid'], self.session['token'])

        if requestdata is None:
            headers['Content-Length'] = 0
        else:
            contenttype, requestbody = self.multipart_form_data_enc(requestdata)
            headers['Content-Length'] = len(requestbody)
            headers['Content-Type'] = contenttype

        logger.debug('Connecting to server')

        # retry the request 10 times
        for timeout_attempt in range(10):
            try:
                # time.sleep(random.uniform(0.3, 0.5))
                httpconn = http.client.HTTPConnection(self.SERVER_HOST, timeout=10)
                httpconn.connect()
                httpconn.putrequest("POST", url, skip_accept_encoding=True)
                for headeritem in headers.items():
                    httpconn.putheader(headeritem[0], headeritem[1])
                httpconn.endheaders()

                if requestdata is not None:
                    httpconn.send(requestbody)

                logger.debug('Receiving from server')
                httpresp = httpconn.getresponse()

                respheaders = httpresp.getheaders()
                respbody = httpresp.read()

                logger.debug('Server response headers:')
                logger.debug(str(respheaders))
                logger.debug('Server response body:')
                logger.debug(str(respbody))

                httpconn.close()

                if not httpresp.status == 200:
                    logger.warning('HTTP status code: {:d}'.format(httpresp.status))
                    # Check docstring for known error codes
                    logger.warning('HTTP headers: %s', str(respheaders))
                    logger.warning('HTTP response body: %s', str(respbody))
                    if (httpresp.status >= 500 and httpresp.status <= 599) or \
                            httpresp.status == 204:
                        logger.warning('Retry HTTP connection')
                        continue
                    else:
                        raise RuntimeError('HTTP status code {:d}'.format(httpresp.status))
            except socket.timeout:
                logger.info('HTTP request timed out')
                # continue
            else:
                break
        else:
            raise RuntimeError('HTTP request failed 10 times')

        # Some sanity checks for returned data

        if httpresp.getheader('Maintenance') is not None:
            logger.warning('Response header "Maintenance" is {:s}'.format(
                httpresp.getheader('Maintenance')))
            if httpresp.getheader('Maintenance') == '1':
                raise RuntimeError('Server under maintenance')

        if httpresp.getheader('server-version') is not None and \
                httpresp.getheader('server-version') != \
                self.DEF_HEADERS['Client-Version']:
            logger.info('Server-Version %s is different from Client-Version %s!',
                        httpresp.getheader('server-version'),
                        self.DEF_HEADERS['Client-Version'])
            logger.info('This will trigger an update in real game client')

        # This can be written to self.DEF_HEADERS['Client-Version'] so that
        # subsequent requests will be accepted
        self._last_response_server_version = httpresp.getheader('server-version')

        if not httpresp.getheader('version_up') == '0':
            logger.warning('Server returned version_up: %s',
                           httpresp.getheader('version_up'))

        # gunzip response if required
        if httpresp.getheader('Content-Encoding') == 'gzip' or \
           httpresp.getheader('Content-Encoding') == 'deflate':
            respbody = zlib.decompress(respbody, zlib.MAX_WBITS + 32)
            logger.debug('gunzipped server response body:')
            logger.debug(str(respbody))
        elif httpresp.getheader('Content-Encoding') is not None:
            logger.warning('Server returned Content-Encoding: %s',
                           httpresp.getheader('Content-Encoding'))

        # More sanity checks
        if httpresp.getheader('X-Message-Code') is not None and \
           not self.gen_xmessagecode(respbody) == \
           httpresp.getheader('X-Message-Code'):
            logger.warning('Server response X-Message-Code incorrect')

        # Decode JSON objects if found
        contenttype = httpresp.getheader('Content-Type')
        if contenttype.find('application/json') == 0:
            contentenc = re.search('charset=([^= ,]*)', contenttype).group(1)
            respobj = json.loads(respbody.decode(encoding=contentenc))
        else:
            logger.warning('Server returned Content-Type: %s', contenttype)
            respobj = None

        if 'status_code' in respobj and respobj['status_code'] != 200:
            logger.warning('JSON response status_code: %s',
                           str(respobj['status_code']))
            logger.warning('Full response: %s', str(respbody))

        try:
            if 'response_data' in respobj and \
                    'authorize_token' in respobj['response_data']:
                logger.info('Auth token found in current response')
        except TypeError:
            pass

        self._last_response_headers = respheaders
        self._last_response_body = respbody
        self._last_response_object = respobj

        return (httpresp.status, respheaders, respbody, respobj)

    def handle_webview_get_request(self, url):
        '''Retrieve a webview HTTP page at url.

        Returns HTTP status, headers, and body.

        This method reuses headers when possible. To clear existing headers,
        set LLSIFClient.session['wv_header'] = None.'''

        if self.session['wv_header'] is None:
            timestamp = str(int(time.time()))

            authorize_header = copy.deepcopy(self.DEF_AUTHORIZE)
            # headers = copy.deepcopy(self.DEF_HEADERS)
            headers = {
                'Connection': 'keep-alive',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'User-Agent': 'Mozilla/5.0 (Linux; Android 4.4.4; XT830C Build/KXC21.5-40) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/33.0.0.0 Mobile Safari/537.36',
                'authorize': None,
                'time-zone': self.DEF_HEADERS['Time-Zone'],
                'os-version': self.DEF_HEADERS['OS-Version'],
                'region': self.DEF_HEADERS['Region'],
                'user-id': None,
                'client-version': self.DEF_HEADERS['Client-Version'],
                'os': self.DEF_HEADERS['OS'],
                'api-model': self.DEF_HEADERS['API-Model'],
                'bundle-version': self.DEF_HEADERS['Bundle-Version'],
                'application-id': self.DEF_HEADERS['Application-ID'],
                'Accept-Encoding': 'gzip,deflate',
                'Accept-Language': 'en-US',
                'X-Requested-With': 'klb.android.lovelive'}

            authorize_header['token'] = self.session['token']
            authorize_header['nonce'] = 'WV0'

            headers['authorize'] = '&'.join('{}={}'.format(*item) for
                                            item in authorize_header.items())
            headers['user-id'] = self.session['userid']

            logger.debug(str(headers))
            self.session['wv_header'] = headers
        else:
            headers = self.session['wv_header']

        try:
            httpconn = http.client.HTTPConnection(self.SERVER_HOST, timeout=20)
            httpconn.request("GET", url, headers=headers)
            httpresp = httpconn.getresponse()

            respstatus = httpresp.status
            respheaders = httpresp.getheaders()
            respbody = httpresp.read()

            httpconn.close()

            return (respstatus, respheaders, respbody)
        except socket.timeout:
            return (504, [], b'')
