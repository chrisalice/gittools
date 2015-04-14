from itertools import count
from lazy import lazy, lazy_invalidation, invalidation_strategy, LazyInvalidation
from utils import staticproperty

def test_function():
  i = [0]
  @lazy
  def foo():
    i[0] += 1
    return i[0]
  assert i[0] == 0
  assert 1 == foo()
  assert i[0] == 1
  assert 1 == foo()
  foo.invalidate()
  assert i[0] == 1
  assert 2 == foo()
  assert i[0] == 2
  assert 2 == foo()

def test_function_type_no_invalidation():
  foo_instances = []
  @lazy
  class foo():
    def __init__(self):
      self.i = 0
      foo_instances.append(self)

    def watch(self, callback):
      self.callback = callback

    def __call__(self):
      self.i += 1
      return self.i
  assert len(foo_instances) == 1
  assert foo_instances[0].i == 0
  assert not hasattr(foo_instances[0], 'callback')
  assert foo() == 1
  assert foo_instances[0].i == 1
  assert not hasattr(foo_instances[0], 'callback')
  assert foo() == 1
  assert len(foo_instances) == 1

def test_function_type_with_invalidation():
  foo_instances = []
  @lazy
  class foo():
    def __init__(self):
      self.i = 0
      foo_instances.append(self)

    def watch(self, callback):
      self.callback = callback

    def __call__(self):
      self.i += 1
      return self.i
  with lazy_invalidation():
    assert len(foo_instances) == 1
    assert foo_instances[0].i == 0
    assert not hasattr(foo_instances[0], 'callback')
    assert foo() == 1
    assert foo_instances[0].i == 1
    assert hasattr(foo_instances[0], 'callback')
    assert foo() == 1
    foo_instances[0].callback()
    assert foo_instances[0].i == 1
    assert foo() == 2
    assert foo_instances[0].i == 2
    assert foo() == 2
    assert foo_instances[0].i == 2
    assert len(foo_instances) == 1

def test_property_cached():
  i = [0]
  class Foo(object):
    @lazy
    @property
    def bar(self):
      i[0] += 1
      return i[0]
  f = Foo()
  assert 1 == f.bar
  assert 1 == f.bar

def test_staticproperty():
  i = [0]
  class Foo(object):
    @staticproperty
    @lazy
    def BAR():
      i[0] += 1
      return i[0]
  assert 1 == Foo.BAR
  assert 1 == Foo.BAR

def test_watchable_property():
  values = count()
  watched = {}
  class Bar(property):
    def __init__(self):
      property.__init__(self, fget = self.getter)

    def getter(self, obj):
      if obj is None:
        return self
      return values.next()

    def watch(self, obj, storage, callback):
      watched[obj] = callback
      storage.obj = obj

    def unwatch(self, storage):
      del watched[storage.obj]

  class Foo(object):
    BAR = lazy(Bar())

  with lazy_invalidation():
    assert hasattr(Foo.BAR, '__get__')
    foo = Foo()
    assert not watched
    assert foo.BAR == 0
    assert watched
    callback = watched.itervalues().next()
    assert foo.BAR == 0
    callback()
    assert foo.BAR == 1
    assert foo.BAR == 1
    callback()
    assert foo.BAR == 2
    assert foo.BAR == 2
    assert watched
  assert not watched

def test_staticproperty_function_type_no_invalidation():
  foo_instances = []
  class Foo():
    @staticproperty
    @lazy
    class FOO():
      def __init__(self):
        self.i = 0
        foo_instances.append(self)

      def watch(self, callback):
        self.callback = callback

      def __call__(self):
        self.i += 1
        return self.i
  assert len(foo_instances) == 1
  assert foo_instances[0].i == 0
  assert not hasattr(foo_instances[0], 'callback')
  foo = Foo()
  assert len(foo_instances) == 1
  assert foo_instances[0].i == 0
  assert not hasattr(foo_instances[0], 'callback')
  assert foo.FOO == 1
  assert foo_instances[0].i == 1
  assert not hasattr(foo_instances[0], 'callback')
  assert foo.FOO == 1
  assert len(foo_instances) == 1

def test_staticproperty_function_type_with_invalidation():
  foo_instances = []
  class Foo():
    @staticproperty
    @lazy
    class FOO():
      def __init__(self):
        self.i = 0
        foo_instances.append(self)

      def watch(self, callback):
        self.callback = callback

      def __call__(self):
        self.i += 1
        return self.i
  with lazy_invalidation():
    assert len(foo_instances) == 1
    assert foo_instances[0].i == 0
    assert not hasattr(foo_instances[0], 'callback')
    foo = Foo()
    assert len(foo_instances) == 1
    assert foo_instances[0].i == 0
    assert not hasattr(foo_instances[0], 'callback')
    assert foo.FOO == 1
    assert foo_instances[0].i == 1
    assert hasattr(foo_instances[0], 'callback')
    assert foo.FOO == 1
    foo_instances[0].callback()
    assert foo_instances[0].i == 1
    assert foo.FOO == 2
    assert foo_instances[0].i == 2
    assert foo.FOO == 2
    assert foo_instances[0].i == 2
    assert len(foo_instances) == 1

def test_method_with_parameters():
  bar_calls = [0]
  class Foo(object):
    def __init__(self, offset):
      self.offset = offset

    @lazy
    def bar(self, value):
      bar_calls[0] += 1
      return value + self.offset
  a = Foo(5)
  b = Foo(10)
  assert 0 == bar_calls[0]
  assert 6 == a.bar(1)
  assert 1 == bar_calls[0]
  assert 6 == a.bar(1)
  assert 1 == bar_calls[0]
  assert 11 == b.bar(1)
  assert 2 == bar_calls[0]
  assert 11 == b.bar(1)
  assert 2 == bar_calls[0]
  assert 8 == a.bar(3)
  assert 3 == bar_calls[0]
  assert 8 == a.bar(3)
  assert 3 == bar_calls[0]

def test_unbound_method_with_parameters():
  bar_calls = [0]
  class Foo(object):
    def __init__(self, offset):
      self.offset = offset

    @lazy
    def bar(self, value):
      bar_calls[0] += 1
      return value + self.offset
  a = Foo(5)
  b = Foo(10)
  assert 0 == bar_calls[0]
  assert 6 == Foo.bar(a, 1)
  assert 1 == bar_calls[0]
  assert 6 == Foo.bar(a, 1)
  assert 1 == bar_calls[0]
  assert 11 == Foo.bar(b, 1)
  assert 2 == bar_calls[0]
  assert 11 == Foo.bar(b, 1)
  assert 2 == bar_calls[0]
  assert 8 == Foo.bar(a, 3)
  assert 3 == bar_calls[0]
  assert 8 == Foo.bar(a, 3)
  assert 3 == bar_calls[0]

