#coding: utf-8

from functools import wraps


FULL_EXTERNALID_CACHE={}

def has(key):
    return key in FULL_EXTERNALID_CACHE.keys()

def insert(key,value):
    FULL_EXTERNALID_CACHE[key]=value
    
def get(key,default=None):
    if has(key):
        return FULL_EXTERNALID_CACHE[key]
    return default

def clear(key=None):
    if key is not None and has(key):
        del FULL_EXTERNALID_CACHE[key]
    elif not key:
        for cached_key in [k for k in FULL_EXTERNALID_CACHE.keys()]:
            del FULL_EXTERNALID_CACHE[cached_key]
            
def storecache(func):
    @wraps(func)
    def func_wrapper(self,*args, **kwargs):
        value=func(self,*args, **kwargs)
        if not has(value[0]):
            insert(value[0],value[2])
        return value
    return func_wrapper
            
def fetchcache(func):
    @wraps(func)
    def func_wrapper(self,*args, **kwargs):
        key = args[0]
        if has(key):
            return get(key)
        value = func(self,*args, **kwargs)
        return value
    return func_wrapper