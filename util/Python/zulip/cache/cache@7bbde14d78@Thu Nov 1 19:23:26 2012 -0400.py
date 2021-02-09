from functools import wraps

import django.core.cache

def cache_with_key(keyfunc):
    """Decorator which applies Django caching to a function.

       Decorator argument is a function which computes a cache key
       from the original function's arguments.  You are responsible
       for avoiding collisions with other uses of this decorator or
       other uses of caching."""

    def decorator(func):
        djcache = django.core.cache.cache

        @wraps(func)
        def func_with_caching(*args, **kwargs):
            key = keyfunc(*args, **kwargs)
            val = djcache.get(key)

            # Values are singleton tuples so that we can distinguish
            # a result of None from a missing key.
            if val is not None:
                return val[0]

            val = func(*args, **kwargs)
            djcache.set(key, (val,))
            return val

        return func_with_caching

    return decorator

def cache(func):
    """Decorator which applies Django caching to a function.

       Uses a key based on the function's name, filename, and
       the repr() of its arguments."""

    func_uniqifier = '%s-%s' % (func.func_code.co_filename, func.func_name)

    @wraps(func)
    def keyfunc(*args, **kwargs):
        # Django complains about spaces because memcached rejects them
        key = func_uniqifier + repr((args, kwargs))
        return key.replace('-','--').replace(' ','-s')

    return cache_with_key(keyfunc)(func)