import functools
import unittest
import bottle
from .tools import api
from bottle import _re_flatten


class TestReFlatten(unittest.TestCase):

    def test_re_flatten(self):
        self.assertEqual(_re_flatten(r"(?:aaa)(_bbb)"), '(?:aaa)(?:_bbb)')
        self.assertEqual(_re_flatten(r"(aaa)(_bbb)"), '(?:aaa)(?:_bbb)')
        self.assertEqual(_re_flatten(r"aaa)(_bbb)"), 'aaa)(?:_bbb)')
        self.assertEqual(_re_flatten(r"aaa(_bbb)"), 'aaa(?:_bbb)')
        self.assertEqual(_re_flatten(r"aaa_bbb"), 'aaa_bbb')


class TestRoute(unittest.TestCase):

    @api('0.12')
    def test_callback_inspection(self):
        def x(a, b): pass
        def d(f):
            @functools.wraps(f)
            def w():
                return f()
            return w
        route = bottle.Route(bottle.Bottle(), None, None, d(x))
        self.assertEqual(route.get_undecorated_callback(), x)
        self.assertEqual(set(route.get_callback_args()), set(['a', 'b']))

        def d2(foo):
            def d(f):
                @functools.wraps(f)
                def w():
                    return f()
                return w
            return d

        route = bottle.Route(bottle.Bottle(), None, None, d2('foo')(x))
        self.assertEqual(route.get_undecorated_callback(), x)
        self.assertEqual(set(route.get_callback_args()), set(['a', 'b']))

    def test_callback_inspection_multiple_args(self):
        # decorator with argument, modifying kwargs
        def d2(f="1"):
            def d(fn):
                @functools.wraps(fn)
                def w(*args, **kwargs):
                    # modification of kwargs WITH the decorator argument
                    # is necessary requirement for the error
                    kwargs["a"] = f
                    return fn(*args, **kwargs)
                return w
            return d

        @d2(f='foo')
        def x(a, b):
            return

        route = bottle.Route(bottle.Bottle(), None, None, x)

        # triggers the "TypeError: 'foo' is not a Python function"
        self.assertEqual(set(route.get_callback_args()), set(['a', 'b']))

    def test_callback_inspection_newsig(self):
        env = {}
        eval(compile('def foo(a, *, b=5): pass', '<foo>', 'exec'), env, env)
        route = bottle.Route(bottle.Bottle(), None, None, env['foo'])
        self.assertEqual(set(route.get_callback_args()), set(['a', 'b']))

    def test_unwrap_wrapped(self):
        import functools
        def func(): pass
        @functools.wraps(func)
        def wrapped():
            return func()

        route = bottle.Route(bottle.Bottle(), None, None, wrapped)
        self.assertEqual(route.get_undecorated_callback(), func)

    @api("0.12", "0.14")
    def test_unwrap_closure(self):
        def func(): pass
        wrapped = _null_decorator(func, update_wrapper=False)
        route = bottle.Route(bottle.Bottle(), None, None, wrapped)
        self.assertEqual(route.get_undecorated_callback(), func)

    # @api("0.15")
    # def test_not_unwrap_closure(self):
    #     def other(): pass
    #     def func():
    #         return other()
    #     route = bottle.Route(bottle.Bottle(), None, None, func)
    #     self.assertEqual(route.get_undecorated_callback(), func)

    @api("0.13", "0.14")
    def test_unwrap_closure_callable(self):
        class Foo:
            def __call__(self): pass

        func = Foo()
        wrapped = _null_decorator(func, update_wrapper=False)
        route = bottle.Route(bottle.Bottle(), None, None, wrapped)
        self.assertEqual(route.get_undecorated_callback(), func)
        repr(route) # Raised cause cb has no '__name__'

    def test_unwrap_method(self):
        def func(self): pass

        class Foo:
            test = _null_decorator(func)

        wrapped = Foo().test
        route = bottle.Route(bottle.Bottle(), None, None, wrapped)
        self.assertEqual(route.get_undecorated_callback(), func)


def _null_decorator(func, update_wrapper=True):
    def wrapper():
        return func()
    if update_wrapper:
        functools.update_wrapper(wrapper, func)
    return wrapper
