def Cache(baseCacheId, timeout, cache=None):
    if not cache:
        from django.core.cache import cache
    def decorate(f):
        async def method(self ,d):
            objCacheId = getattr(self, 'cacheId', '')
            try:
                cacheId = baseCacheId.format(cacheId=objCacheId)
            except KeyError:
                cacheId = baseCacheId
            cacheId = f'{cacheId}_{str(d)}'
            result = await cache.aget(cacheId, None)
            if result is not None:
                return result
            result = await f(self, d)
            await cache.aset(cacheId, result, timeout)
            return result
        return method
    return decorate