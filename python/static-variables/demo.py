#!/usr/bin/python3


class Base(object):
    objtype = 'base'

    def print_type(self):
        print(type(self).objtype)


class Foo(Base):
    objtype = 'foo'


a = Base()
a.print_type()


b = Foo()
b.print_type()
