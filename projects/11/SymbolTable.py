

class SymbolTable:

    def __init__(self):
        self.class_table = dict()
        self.subr_table = dict()
        self.counts = {'static': 0, 'field': 0, 'argument': 0, 'var': 0}

    def startSubroutine(self):
        self.subr_table = dict()
        self.counts['argument'] = 0
        self.counts['var'] = 0

    def define(self, name, tp, kind):
        match kind:
            case 'static' | 'field':
                self.class_table[name] = {'tp': tp, 'kind': kind, 'ind': self.varCount(kind)}
            case 'argument' | 'var':
                self.subr_table[name] = {'tp': tp, 'kind': kind, 'ind': self.varCount(kind)}
        self.counts[kind] = self.counts.get(kind) + 1

    def varCount(self, kind: str) -> int:
        assert kind in {'static', 'field', 'argument', 'var'}
        return self.counts.get(kind)

    def kindOf(self, name: str):
        if self.subr_table.get(name, None):
            return self.subr_table.get(name)['kind']
        elif self.class_table.get(name, None):
            return 'this' if self.class_table.get(name)['kind'] == 'field' else 'static'
        else:
            return None

    def typeOf(self, name: str):
        if self.subr_table.get(name, None):
            return self.subr_table.get(name)['tp']
        elif self.class_table.get(name, None):
            return self.class_table.get(name)['tp']
        else:
            return None

    def indexOf(self, name: str):
        if self.subr_table.get(name, None):
            return self.subr_table.get(name)['ind']
        elif self.class_table.get(name, None):
            return self.class_table.get(name)['ind']
        else:
            return None
