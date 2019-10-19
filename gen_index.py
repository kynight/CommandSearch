#!/usr/bin/env python
# -*- coding: utf-8 -*-
from mysql_db import GetAllCommand
from jieba_1 import Participle
from collections import defaultdict
from redis_cache import client

def genIndex():
    res = defaultdict(set)
    participle = Participle()
    # id code description
    for row in GetAllCommand().send(None):
        for word in participle.cut(row[1]):
            res[word].add(row[0])
        for word in participle.cut(row[2]):
            res[word].add(row[0])
    return res


def pushRedis(index):
    with client.pipeline() as pipe:
        for key, value in res.items():
            pipe.rpush(key, *value)
        pipe.execute()


print(genIndex())
