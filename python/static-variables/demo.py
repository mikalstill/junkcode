#!/usr/bin/python3


class Base(object):
    objtype = 'base'

    def instance_method_print_type(self):
        print(type(self).objtype)

    @classmethod
    def class_method_print_type(cls):
        print(cls.objtype)


class Foo(Base):
    objtype = 'foo'


a = Base()
a.instance_method_print_type()
Base.class_method_print_type()


b = Foo()
b.instance_method_print_type()
Foo.class_method_print_type()
