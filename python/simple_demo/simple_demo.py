#!/usr/bin/python
import parastor.node
# from parastor.node import Node

def empty_func():
    """Do nothing"""
    pass

def swap_demo():
    
    print '\nswap_demo'
    # Swap two numbers.
    a = 1
    b = 2
    a, b = b, a
    print a, ',', b

def string_demo():
    """Show how to print a simple string."""

    print 'Hello World1'
    print "Hello World2"
    print """Hello
World3"""
    print "Hello world4",
    print " Hello world5"

def string_demo2():
    """String demo2"""

    str1 = 'sugon'
    print str1 * 2
    print 'the length of str1 is %d' % len(str1)
    if str1.startswith('su'):
        print '%s start with su' % str1
    if str1.find('go'):
        print '%s contains go' % str1

    print "The %(foo)s is %(bar)i." % {'foo': 'answer', 'bar':42}


def list_demo():
    """How to use list."""

    list_a = ['s', 'u', 'g', 'o', 'n']
    print list_a
    print list_a[0: 2]
    print list_a[0:]
    print list_a[-2:]
    if 'g' in list_a:
        print 'g is in list_a'
    list_b = range(0, 10)
    print list_b
    list_c = [x for x in list_b if x % 2 == 0]
    print list_c
    list_d = list_c * 2
    print list_d
    
def list_demo2():
    """How to add and delete an element."""

    print '\nlist_demo2:'
    list_a = ['s', 'u', 'g']
    list_a.append('o')
    list_a.append('n')
    list_a.pop()
    print list_a
    list_a.sort()
    print list_a

def dict_demo1():
    """How to define a dict."""
    
    print '\ndict demo1'
    a = dict(one=1, two=2, three=3)
    b = {'one': 1, 'two': 2, 'three': 3}
    c = dict(zip(['one', 'two', 'three'], [1, 2, 3]))
    d = dict([('two', 2), ('one', 1), ('three', 3)])
    e = dict({'three': 3, 'one': 1, 'two': 2})
    print a == b == c == d == e
    print b['one']
    b['one'] = 'one'
    print b['one']
    for (k, v) in a.items():
        print '%s:%s' % (k, v)

def dict_demo2():
    """Define a complicated dict."""

    print '\n dict demo2'
    
    dict_c = {
        'list_a': ['su', 'gon'],
        'str': 'sugon',
        'dict': {
            'name': 'jiangjiafu',
            'title': 'manong'
        }
    }

    print dict_c['str']
    print dict_c['dict']['name']

def fun2(a, b, c='Hello', d=None, *args, **kwargs):
    """How to define a function with many parameters."""

    print '\nfun2'
    print 'a is ', a
    print 'b is ', b
    print 'c is ', c
    print 'd is ', d
    print 'args is ', args
    print 'kwargs is', kwargs

def class_demo():
    """How to define a class"""

    print '\nclass demo'
    mgrnode = parastor.node.MGRNode('MGR', 1)
    print mgrnode.get_desc()

def oper_reload_demo():
    """"Operation reload demo."""

    print '\noper_reload_demo'
    node_a = parastor.node.MGRNode('MGR', 1)
    node_b = parastor.node.ClientNode(1)
    node_c = parastor.node.ClientNode(2)
    node_d = parastor.node.ClientNode(2)

    print node_a != node_b
    print node_a > node_c
    print node_b < node_c
    print node_c == node_d

def basic_ctrl_flow_demo():
    
    print '\nctrl_flow demo'
    list_a = ['s', 'u', 'g', 'o', 'n']
    for c in list_a:
        print c,
    print

    for i in range(0, 5):
        print i

    i = 2
    while i > 0:
        print i
        i = i - 1
    
    a = 3 
    b = 3
    if a == b == 3:
        print 'a == b == 3'
    x = 5
    print  1 < x <10
    print x < 10 < x * 10 < 100
    print 10 > x <= 9
    print 5 == x > 4
    
    a = ['a', 'b', 'c', 'd']
    for index, item in enumerate(a):
        print index, item


def error_catch_demo():
    
    print '\ncatch_demo'
    try:
        raise Exception('This is an Exception.')
    except Exception as e:
        print e
    finally:
        print 'no matter what happens, this line will be printed.'


def print_args(function):
    def wrapper(*args, **kwargs):
        print 'Arguments:', args, kwargs
        return function(*args, **kwargs)
    return wrapper

@print_args
def write(text):
    print text

def decorator_demo():

    print '\ndecorator_demo'
    write('hello')

def for_else_demo():
    
    print '\nfor_else_demo'
    foo = [1, 2 , 3, 4, 5]
    found = False
    for i in foo:
        if i == 0:
            found = True
            break
    if not found: 
        print("i was never 0")

    # another way
    for i in foo:
        if i == 0:
            break
    else:
        print("i was never 0")

def main():
    empty_func()
    swap_demo()
    string_demo()
    print string_demo.__doc__
    string_demo2()
    list_demo()
    list_demo2()
    dict_demo1()
    dict_demo2()
    fun2(1, 2, 'World', True, 3, 4, 5, 6, name='jiangjiafu', company='sugon')
    class_demo()
    oper_reload_demo()
    basic_ctrl_flow_demo()
    error_catch_demo()
    decorator_demo()
    for_else_demo()

if __name__ == '__main__':
    main()
