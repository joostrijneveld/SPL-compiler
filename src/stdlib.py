#! /usr/bin/env python

from semanticanalysis import Type, Symbol

functions = {
    'toInt': (Symbol(0, 0, Type('Int'), [Type('t')], True, None),
        ['ldl 1']),
    'toChar': (Symbol(0, 0, Type('Char'), [Type('t')], True, None),
        ['ldl 1']),
    'toBool': (Symbol(0, 0, Type('Bool'), [Type('t')], True, None),
        ['ldl 1', 'brf 4', 'ldc -1', 'bra 2', 'ldc 0']),
    'isEmpty': (Symbol(0, 0, Type('Bool'), [Type([Type('t')])], True, None),
        ['ldl 1', 'ldc 0', 'eq']),
    'print': (Symbol(0, 0, Type('Void'), [Type('t')], True, None),
        ['ldl 1', 'trap 0']),
    'printChar': (Symbol(0, 0, Type('Void'), [Type('Char')], True, None),
        ['ldl 1', 'trap 1']),
    'printBool': (Symbol(0, 0, Type('Void'), [Type('Bool')], True, None),
        ['ldl 1', 'brf 4', 'ldc 128515', 'bra 2', 'ldc 128542', 'trap 1']),
    'readInt': (Symbol(0, 0, Type('Int'), [], True, None),
        ['trap 2']),
    'readChar': (Symbol(0, 0, Type('Char'), [], True, None),
        ['trap 3']),
    'readCharList': (Symbol(0, 0, Type([Type('Char')]), [], True, None),
        ['trap 4', 'brf endemptylist', 'ajs 1', 'ldc 0', 'loopCharList:',
        'sth', 'ajs -1', 'sth', 'ajs -1', 'brf endloopCharList', 'ajs 2',
        'bra loopCharList', 'endloopCharList:', 'ajs 2', 'str RR', 'ajs -1',
        'unlink', 'ret', 'endemptylist:', 'ldc 0'])
}
