# -*- coding: utf-8 -*-
'''
Define various decarators for:

    singleton,
    lazy properties,
    cached function evaluation
'''

_missing = object()

__all__ = ['singleton', 'once', 'lazy_property']


class singleton:
    """ Decorator for defining a singleton-like object instanciated at the first call """
    def __init__(self, decorated):
        self._decorated = decorated

    def __call__(self, *args, **kwargs):
        try:
            return self._instance
        except AttributeError:
            self._instance = self._decorated(*args, **kwargs)
            return self._instance


class once:
    """ Evaluate the function only once """
    def __init__(self, f):
        self.f = f

    def __call__(self, *args, **kwargs):
        if not hasattr(self, "value"):
            self.value = self.f(*args, **kwargs)
        return self.value


class lazy_property:
    """ A decorator that converts a function into a lazy property. The
        function wrapped is called the first time to retrieve the result
        and then that calculated result is used the next time you access
        the value::

            class Foo(object):

            @lazy_property
            def foo(self):
                # calculate something important here
                return 42

        The class has to have a `__dict__` in order for this property to
        work.
    """

    # implementation detail: this property is implemented as non-data
    # descriptor. non-data descriptors are only invoked if there is
    # no entry with the same name in the instance's __dict__.
    # this allows us to completely get rid of the access function call
    # overhead. If one choses to invoke __get__ by hand the property
    # will still work as expected because the lookup logic is replicated
    # in __get__ for manual invocation.

    def __init__(self, func, name=None, doc=None):
        self.__name__ = name or func.__name__
        self.__module__ = func.__module__
        self.__doc__ = doc or func.__doc__
        self.func = func

    def __get__(self, obj, klass=None):
        if obj is None:
            return self
        value = obj.__dict__.get(self.__name__, _missing)
        if value is _missing:
            value = self.func(obj)
            obj.__dict__[self.__name__] = value
        return value
