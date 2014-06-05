#! /usr/bin/env python

from semanticanalysis import Type, Symbol

functions = {
	'isEmpty': (Symbol(0, 0, Type('Bool'), [Type([Type('t')])], True, None),
		['ldl 1', 'ldc 0', 'eq']),
	'print': (Symbol(0, 0, Type('Void'), [Type('t')], True, None),
		['ldl 1', 'trap 0']),
	'printChar': (Symbol(0, 0, Type('Void'), [Type('Char')], True, None),
		['ldl 1', 'trap 1'])
}