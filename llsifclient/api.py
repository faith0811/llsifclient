# -*- coding: utf-8 -*-

import time
import logging

from collections import OrderedDict

logger = logging.getLogger(__name__)


class LLSIFAPI(object):
    def __init__(self, module, action, requires=None, options=None, excludes=None):
        self.module = module
        self.action = action
        self.requires = requires
        self.options = options
        self.excludes = excludes

    @property
    def uri(self):
        return '/main.php/{}/{}'.format(self.module, self.action)

    def parse(self, is_single=True, **kwargs):
        res = {
            'module': self.module,
            'action': self.action,
            'timeStamp': int(time.time()),
            'commandNum': None,
        }
        if not is_single:
            del res['commandNum']
        if self.requires is not None:
            assert isinstance(self.requires, list)
            for key in self.requires:
                if key not in kwargs:
                    raise LLSIFAPIException('Required Key {} not included.'.format(key))
                res[key] = kwargs[key]
        if self.options is not None:
            assert isinstance(self.options, list)
            for key in self.options:
                if key in kwargs:
                    res[key] = kwargs[key]
        if self.excludes is not None:
            assert isinstance(self.excludes, list)
            for key in self.excludes:
                if key in res:
                    del res[key]
        logger.debug('module: {}, action: {}, parse result: {}'.format(self.module, self.action, res))
        return res


class LLSIFAPIException(Exception):
    pass
