from functools import reduce

DIMS = {
    'F': frozenset('F'),
    'T': frozenset('012'),
    '*': frozenset('F012'),
    '0': frozenset('0'),
    '1': frozenset('1'),
    '2': frozenset('2'),
    }

def pattern(pattern_string):
    return Pattern(pattern_string)

class Pattern(object):
    def __init__(self, pattern_string):
        self.pattern = tuple(pattern_string.upper())
    def __str__(self):
        return ''.join(self.pattern)
    def __repr__(self):
        return "DE-9IM pattern: '%s'" % str(self)
    def matches(self, matrix_string):
        matrix = tuple(matrix_string.upper())
        def onematch(p, m):
            return m in DIMS[p]
        return bool(
            reduce(lambda x, y: x * onematch(*y), zip(self.pattern, matrix), 1)
            )

class AntiPattern(object):
    def __init__(self, anti_pattern_string):
        self.anti_pattern = tuple(anti_pattern_string.upper())
    def __str__(self):
        return '!' + ''.join(self.anti_pattern)
    def __repr__(self):
        return "DE-9IM anti-pattern: '%s'" % str(self)
    def matches(self, matrix_string):
        matrix = tuple(matrix_string.upper())
        def onematch(p, m):
            return m in DIMS[p]
        return not (
            reduce(lambda x, y: x * onematch(*y),
                   zip(self.anti_pattern, matrix),
                   1)
            )

class NOrPattern(object):
    def __init__(self, pattern_strings):
        self.patterns = [tuple(s.upper()) for s in pattern_strings]
    def __str__(self):
        return '||'.join([''.join(list(s)) for s in self.patterns])
    def __repr__(self):
        return "DE-9IM or-pattern: '%s'" % str(self)
    def matches(self, matrix_string):
        matrix = tuple(matrix_string.upper())
        def onematch(p, m):
            return m in DIMS[p]
        for pattern in self.patterns:
            val = bool(
                reduce(lambda x, y: x * onematch(*y), zip(pattern, matrix), 1))
            if val is True:
                break
        return val


# Familiar names for patterns or patterns grouped in logical expression
# ---------------------------------------------------------------------
contains = Pattern('T*****FF*')
crosses_lines = Pattern('0********')   # cross_lines is only valid for pairs of lines and/or multi-lines
crosses_1 = Pattern('T*T******')       # valid for mixed types (dim(a) < dim(b))
crosses_2 = Pattern('T*****T**')       # valid for mixed types (dim(a) > dim(b))
disjoint = Pattern('FF*FF****')
equal = Pattern('T*F**FFF*')
intersects = AntiPattern('FF*FF****')
overlaps1 = Pattern('T*T***T**')   # points and regions share an overlap pattern
overlaps2 = Pattern('1*T***T**')   # valid for lines only
touches = NOrPattern(['FT*******', 'F**T*****', 'F***T****'])
within = Pattern('T*F**F***')
covered_by = NOrPattern(['T*F**F***','*TF**F***','**FT*F***','**F*TF***'])
covers =  NOrPattern(['T*****FF*',	'*T****FF*',	'***T**FF*',	'****T*FF*'])
