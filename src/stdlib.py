#! /usr/bin/env python

from semanticanalysis import Type, Symbol

functions = {
	'toInt': (Symbol(0, 0, Type('Int'), [Type('t')], True, None),
		['ldl 1']),
	'toChar': (Symbol(0, 0, Type('Char'), [Type('t')], True, None),
		['ldl 1']),
	'isEmpty': (Symbol(0, 0, Type('Bool'), [Type([Type('t')])], True, None),
		['ldl 1', 'ldc 0', 'eq']),
	'print': (Symbol(0, 0, Type('Void'), [Type('t')], True, None),
		['ldl 1', 'trap 0']),
	'printChar': (Symbol(0, 0, Type('Void'), [Type('Char')], True, None),
		['ldl 1', 'trap 1']),
	'readInt': (Symbol(0, 0, Type('Int'), [], True, None),
		['trap 2']),
	'readChar': (Symbol(0, 0, Type('Char'), [], True, None),
		['trap 3']),
	'readCharList': (Symbol(0, 0, Type([Type('Char')]), [], True, None),
		['trap 4', 'brf endemptylist', 'ajs 1', 'ldc 0', 'loop:', 'sth',
		'ajs -1', 'sth', 'ajs -1', 'brf endloop', 'ajs 2', 'bra loop',
		'endloop:', 'ajs 2', 'str RR', 'ajs -1', 'unlink', 'ret',
		'endemptylist:', 'ldc 0'])  # str RR, unlink and ret added by generator
}