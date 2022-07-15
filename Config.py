#!/usr/bin/env python
# -*- coding: utf-8 -*-

import yaml
import sys
import os
if sys.version < '3':
    reload(sys)
    sys.setdefaultencoding('utf-8')
class obj(object):
    def __init__(self, d):
        for a, b in d.items():
            if isinstance(b, (list, tuple)):
               setattr(self, a, [obj(x) if isinstance(x, dict) else x for x in b])
            else:
               setattr(self, a, obj(b) if isinstance(b, dict) else b)

def getConfig():
    with open('%s/.ENV.yaml' % os.getcwd()) as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
        return obj(data)

if __name__ == '__main__':
    cfg = getConfig()
    print yaml.dump(cfg)
