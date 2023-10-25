import glob
import sys
from SymbolTable import SymbolTable
from VMWriter import VMWriter


class JackTokenizer:

    def __init__(self, file):
        self.input = open(file, 'r')
        self.line = None
        self.token = 'init'
        self.symbols = {k: True for k in '{}()[].,;+-*/&|<>=-~'}
        self.kws = {k: k.upper() for k in ['class', 'constructor', 'function', 'method', 'field', 'static', 'var',
                                           'int', 'char', 'boolean', 'void', 'true', 'false', 'null', 'this', 'let',
                                           'do', 'if', 'else', 'while', 'return']}
        self.parseLine()
        self.advance()

    def parseLine(self):
        self.line = self.input.readline()
        if not self.line:
            return
        self.line = self.line.strip()
        if not self.line or (len(self.line) >= 2 and self.line[:2] == "//"):
            self.parseLine()
        elif len(self.line) >= 2 and self.line[:2] == "/*":
            cursor = 2
            while self.line[cursor:cursor+2] != "*/":
                if cursor == len(self.line)-1:
                    self.line = self.input.readline()
                    cursor = -1
                cursor += 1
            self.parseLine()
        else:
            tokens = []
            left = 0
            while left < len(self.line):
                right = left + 1
                if self.line[left] == " ":
                    left += 1
                elif self.line[left] == '"':
                    while self.line[right] != '"':
                        right += 1
                    tokens.append(self.line[left:right+1])
                    left = right + 1
                elif self.symbols.get(self.line[left], None):
                    if len(self.line) >= 2 and self.line[left:left+2] == "//":
                        left = len(self.line)
                    else:
                        tokens.append(self.line[left])
                        left += 1
                else:
                    while right < len(self.line):
                        if self.line[right] == ' ' or self.symbols.get(self.line[right], None):
                            break
                        right += 1
                    tokens.append(self.line[left:right])
                    left = right
            self.line = tokens

    def advance(self):
        if self.line:
            # set token
            self.token = self.line.pop(0)
        else:
            self.token = None

    def hasMoreTokens(self):
        # if current token popped the last item in a line, prep the next line
        if len(self.line) == 0:
            self.parseLine()

        if self.token:
            return True
        else:
            self.input.close()
            return False

    def tokenType(self) -> str:
        if self.kws.get(self.token, None):
            return 'keyword'
        elif self.symbols.get(self.token, None):
            return 'symbol'
        else:
            try:
                if 0 <= int(self.token) <= 32767:
                    return 'integerConstant'
            except ValueError:
                pass
        if len(self.token) > 1 and ((self.token[0] and self.token[-1]) == '"'):
            return 'stringConstant'
        else:
            return 'identifier'

    def tokenValue(self, tok_type):
        match tok_type:
            case 'integerConstant':
                return int(self.token)
            case 'stringConstant':
                return self.token[1:-1]
            case _:
                return self.token


class CompilationEngine:

    def __init__(self, file):
        self.tk = JackTokenizer(file)
        self.class_name = file.split('.jack')[0].split('/')[-1]
        self.writer = VMWriter(file)
        # self.output = open(f"{file.split('.jack')[0]}Mine.xml", 'a')
        self.label_count = 1
        self.tab = 0
        self.tok = {'type': '', 'value': ''}
        self.check = {'ops': {x for x in '+-*/&|<>='}, 'unary': {y for y in '-~'}, 'kws': {z for z in ['true', 'false', 'null', 'this']}}
        self.ids = SymbolTable()
        self.context = 'defined'
        self.compileClass()

    def nextToken(self):
        if self.tk.hasMoreTokens():
            self.tok['type'] = self.tk.tokenType()
            self.tok['value'] = self.tk.tokenValue(self.tok['type'])
            self.tk.advance()

    # def writeTok(self):
    #     self.output.write(('  '*self.tab)+f'<{self.tok["type"]}> {self.tok["value"]} </{self.tok["type"]}>\n')
    #     self.nextToken()

    def checkTok(self, check_type: str = None, check_val: str = None):
        if check_type and self.tok['type'] != check_type:
            raise SyntaxError(f"Unexpected token type: {self.tok['value']} of type {self.tok['type']}")
        if check_val and self.tok['value'] != check_val:
            raise SyntaxError(f"Unexpected token value: {self.tok['value']} of type {self.tok['type']}")
        else:
            self.nextToken()
        # if self.tok['type'] == 'identifier':
        #     self.writeID()
        # else:
            # # self.writeTok()

    # def writeID(self):
    #     self.output.write(('  ' * self.tab) + f'<{self.tok["type"]}> {self.tok["value"]} </{self.tok["type"]}>\n')
    #     self.output.write(('  ' * self.tab) + f'<context> {self.context} </context>\n')
    #     if not self.ids.kindOf(self.tok['value']):
    #         self.nextToken()
    #         if self.tok['value'] == '.' or self.tok['value'] == '{' or self.tok['type'] == 'identifier':
    #             self.output.write(('  ' * self.tab) + f'<kind> class </kind>\n')
    #         else:
    #             self.output.write(('  ' * self.tab) + f'<kind> subroutine </kind>\n')
    #     else:
    #         self.output.write(('  ' * self.tab) + f'<kind> {self.ids.kindOf(self.tok["value"])} </kind>\n')
    #         self.output.write(('  ' * self.tab) + f'<index> {self.ids.indexOf(self.tok["value"])} </index>\n')
    #         self.nextToken()

    # def writeTag(self, tag: str, start: bool):
    #     if start:
    #         self.output.write(('  '*self.tab) + f'<{tag}>\n')
    #         self.tab += 1
    #     else:
    #         self.tab -= 1
    #         self.output.write(('  '*self.tab) + f'</{tag}>\n')

    def compileClass(self):
        # self.writeTag('class', True)
        self.nextToken()
        self.checkTok(check_val='class')
        self.checkTok(check_type='identifier')
        self.checkTok(check_val='{')
        self.context = 'used'
        
        while self.tok['value'] in {'static', 'field'}:
            self.compileClassVarDec()          
            
        while self.tok['value'] in {'constructor', 'function', 'method'}:
            self.compileSubroutine()

        self.checkTok(check_val='}')
        # self.writeTag('class', False)
        # self.output.close()

    def compileClassVarDec(self):
        # self.writeTag('classVarDec', True)
        kind = self.tok['value']
        self.nextToken()
        # self.writeTok()  # checked this was field or static before calling this method
        tp = self.tok['value']
        self.checkTok()  # call with no check since this could be keyword OR identifier
        # var name
        name = self.tok['value']
        self.context = 'defined'
        self.ids.define(name, tp, kind)
        self.checkTok(check_type='identifier')

        # if there is a comma + more var names
        while self.tok['value'] == ',':
            # self.writeTok()
            self.nextToken()
            name = self.tok['value']
            self.ids.define(name, tp, kind)
            self.checkTok(check_type='identifier')

        self.checkTok(check_val=';')
        # list of var names ended
        # self.writeTag('classVarDec', False)
        self.context = 'used'

    def compileSubroutine(self):
        # self.writeTag('subroutineDec', True)
        self.ids.startSubroutine()
        special = ""
        match self.tok['value']:
            case 'constructor':
                special = "con"
            case 'method':
                special = "meth"
            case _:
                special = None
        # self.writeTok()
        self.nextToken()  # checked for constructor, method, function, before calling
        self.nextToken()  # return type
        # subroutine name and optional params
        self.context = 'defined'
        name = self.class_name + "." + self.tok['value']
        self.checkTok(check_type='identifier')
        self.context = 'used'
        self.checkTok(check_val='(')
        if special == "meth":
            self.ids.define("this", self.class_name, "argument")
        self.compileParameterList()
        self.checkTok(check_val=')')
        
        # self.writeTag('subroutineBody', True)
        self.checkTok(check_val='{')
        while self.tok['value'] == 'var':
            self.compileVarDec()
        self.writer.writeFunction(name, self.ids.varCount('var'))
        if special == "con":
            self.writer.writePush('constant', self.ids.varCount('field'))
            self.writer.writeCall("Memory.alloc", 1)
            self.writer.writePop('pointer', 0)
        elif special == "meth":
            self.writer.writePush('argument', 0)
            self.writer.writePop('pointer', 0)
        self.compileStatements()
        self.checkTok(check_val='}')

        # self.writeTag('subroutineBody', False)
        # self.writeTag('subroutineDec', False)
    
    def compileParameterList(self):
        # self.writeTag('parameterList', True)
        kind = 'argument'
        while self.tok['value'] != ')':
            while True:
                tp = self.tok['value']
                self.checkTok()  # parameter type
                name = self.tok['value']
                self.context = 'defined'
                self.ids.define(name, tp, kind)
                self.checkTok(check_type='identifier')  # parameter name
                self.context = 'used'
                # if there are no more parameters, break the loop
                if self.tok['value'] != ',':
                    break
                # self.writeTok()
                self.nextToken()
                
        # self.writeTag('parameterList', False)
    
    def compileVarDec(self):
        # self.writeTag('varDec', True)
        kind = 'var'
        # self.writeTok()
        self.nextToken() # already checked this was 'var'
        tp = self.tok['value']
        self.checkTok()  # var type
        # var name
        name = self.tok['value']
        self.context = 'defined'
        self.ids.define(name, tp, kind)
        self.checkTok(check_type='identifier')
        # write commas and var names if they exist
        while self.tok['value'] == ',':
            # self.writeTok()
            self.nextToken()
            name = self.tok['value']
            self.ids.define(name, tp, kind)
            self.checkTok(check_type='identifier')
        # end declaration
        self.checkTok(check_val=';')
        self.context = 'used'
        # self.writeTag('varDec', False)

    def compileStatements(self):
        # self.writeTag('statements', True)
        while self.tok['value'] != '}':
            match self.tok['value']:
                case 'let':
                    self.compileLet()
                case 'if':
                    self.compileIf()
                case 'do':
                    self.compileDo()
                case 'while':
                    self.compileWhile()
                case 'return':
                    self.compileReturn()
        # self.writeTag('statements', False)

    def compileDo(self):
        # self.writeTag('doStatement', True)
        # self.writeTok()
        self.nextToken()

        id = self.tok['value']
        self.nextToken()
        self.compileFuncCall(id)

        # self.checkTok(check_type='identifier')
        # if self.tok['value'] == '.':
        #     # self.writeTok()
        #     self.nextToken()
        #     self.checkTok(check_type='identifier')
        # self.checkTok(check_val='(')
        # self.compileExpressionList()
        # self.checkTok(check_val=')')
        self.checkTok(check_val=';')
        self.writer.writePop('temp', 0)
        # self.writeTag('doStatement', False)

    def compileLet(self):
        # self.writeTag('letStatement', True)
        # self.writeTok()
        self.nextToken()
        # self.checkTok(check_type='identifier')
        if not self.ids.kindOf(self.tok['value']):
            raise SyntaxError(f"{self.tok['value']} is not declared in scope.")
        assign = self.tok['value']
        self.nextToken()
        if self.tok['value'] == '[':
            # self.writeTok()
            self.writer.writePush(self.ids.kindOf(assign), self.ids.indexOf(assign))
            self.nextToken()
            self.compileExpression()
            self.checkTok(check_val=']')
            self.writer.writeArithmetic('add')
            self.writer.writePop('pointer', 1)
            self.checkTok(check_val='=')
            self.compileExpression()
            self.checkTok(check_val=';')
            self.writer.writePop('that', 0)
        else:
            self.checkTok(check_val='=')
            self.compileExpression()
            self.checkTok(check_val=';')
            self.writer.writePop(self.ids.kindOf(assign), self.ids.indexOf(assign))

        # self.writeTag('letStatement', False)

    def compileWhile(self):
        label1 = "Loop" + str(self.label_count)
        label2 = "Break" + str(self.label_count)
        self.label_count += 1
        # self.writeTag('whileStatement', True)
        # self.writeTok()
        self.nextToken()
        self.writer.writeLabel(label1)
        self.checkTok(check_val='(')
        self.compileExpression()
        self.checkTok(check_val=')')
        self.writer.writeArithmetic("not")
        self.writer.writeIf(label2)

        self.checkTok(check_val='{')
        self.compileStatements()
        self.checkTok(check_val='}')
        self.writer.writeGoto(label1)
        self.writer.writeLabel(label2)

        # self.writeTag('whileStatement', False)

    def compileReturn(self):
        # self.writeTag('returnStatement', True)
        # self.writeTok()
        self.nextToken()
        if self.tok['value'] == ';':
            self.writer.writePush('constant', 0)
        else:
            self.compileExpression()
        self.checkTok(check_val=';')
        self.writer.writeReturn()

        # self.writeTag('returnStatement', False)

    def compileIf(self):
        l1 = "NotCond" + str(self.label_count)
        l2 = "YesCond" + str(self.label_count)
        self.label_count += 1

        # self.writeTag('ifStatement', True)
        # self.writeTok()
        self.nextToken()

        self.checkTok(check_val='(')
        self.compileExpression()
        self.checkTok(check_val=')')
        self.writer.writeArithmetic('not')
        self.writer.writeIf(l1)

        self.checkTok(check_val='{')
        self.compileStatements()
        self.checkTok(check_val='}')

        if self.tok['value'] == 'else':
            self.writer.writeGoto(l2)
            self.writer.writeLabel(l1)
            # self.writeTok()
            self.nextToken()
            self.checkTok(check_val='{')
            self.compileStatements()
            self.checkTok(check_val='}')
            self.writer.writeLabel(l2)
        else:
            self.writer.writeLabel(l1)

        # self.writeTag('ifStatement', False)

    def compileExpression(self):
        # self.writeTag('expression', True)

        self.compileTerm()
        while self.tok['value'] in self.check['ops']:
            op = self.tok['value']
            # match self.tok['value']:
            #     case '<':
            #         self.tok['value'] = '&lt;'
            #     case '>':
            #         self.tok['value'] = '&gt;'
            #     case '&':
            #         self.tok['value'] = '&amp;'
            # self.writeTok()
            self.nextToken()
            self.compileTerm()
            match op:
                case "*":
                    self.writer.writeCall("Math.multiply", 2)
                case "/":
                    self.writer.writeCall("Math.divide", 2)
                case _:
                    self.writer.writeArithmetic(op)

        # self.writeTag('expression', False)

    def compileTerm(self):
        # self.writeTag('term', True)

        if self.tok['value'] == '(':
            # self.writeTok()
            self.nextToken()
            self.compileExpression()
            self.checkTok(check_val=')')

        elif self.tok['value'] in self.check['unary']:
            op = ''
            match self.tok['value']:
                case '-':
                    op = 'neg'
                case'~':
                    op = 'not'
            # self.writeTok()
            self.nextToken()
            self.compileTerm()
            self.writer.writeArithmetic(op)
        elif self.tok['type'] == 'integerConstant':
            self.writer.writePush('constant', int(self.tok['value']))
            self.nextToken()
        elif self.tok['type'] == 'stringConstant':
            self.writer.writePush('constant', len(self.tok['value']))
            self.writer.writeCall("String.new", 1)
            for char in self.tok['value']:
                self.writer.writePush('constant', ord(char))
                self.writer.writeCall('String.appendChar', 2)
            self.nextToken()
        elif self.tok['value'] in self.check['kws']:
            match self.tok['value']:
                case 'true':
                    self.writer.writePush('constant', 1)
                    self.writer.writeArithmetic('neg')
                case 'false' | 'null':
                    self.writer.writePush('constant', 0)
                case 'this':
                    self.writer.writePush('pointer', 0)
            self.nextToken()

        elif self.tok['type'] == 'identifier':
            # self.checkTok(check_type='identifier')
            id = self.tok['value']
            self.nextToken()
            if self.tok['value'] == '[':
                # self.writeTok()
                self.writer.writePush(self.ids.kindOf(id), self.ids.indexOf(id))
                self.nextToken()
                self.compileExpression()
                self.checkTok(check_val=']')
                self.writer.writeArithmetic('+')
                self.writer.writePop('pointer', 1)
                self.writer.writePush('that', 0)

            elif self.tok['value'] in {".", "("}:
                # self.writeTok()
                # self.nextToken()
                # self.checkTok(check_type='identifier')
                self.compileFuncCall(id)
            else:
                self.writer.writePush(self.ids.kindOf(id), self.ids.indexOf(id))

        # self.writeTag('term', False)

    def compileExpressionList(self):
        # self.writeTag('expressionList', True)
        nargs = 0
        while self.tok['value'] != ')':
            self.compileExpression()
            nargs += 1
            if self.tok['value'] != ',':
                break
            # self.writeTok()
            self.nextToken()  # continue the loop to compile the next expression

        return nargs

        # self.writeTag('expressionList', False)

    def compileFuncCall(self, id):
        call = "!error"
        nargs = -1

        if self.tok['value'] == ".":
            self.nextToken()
            if self.ids.kindOf(id):
                call = "".join([self.ids.typeOf(id), ".", self.tok['value']])
                self.writer.writePush(self.ids.kindOf(id), self.ids.indexOf(id))
                self.nextToken()
                self.checkTok(check_val='(')
                nargs = self.compileExpressionList() + 1
                self.checkTok(check_val=')')
            else:
                call = f"{id}.{self.tok['value']}"
                self.nextToken()
                self.checkTok(check_val="(")
                nargs = self.compileExpressionList()
                self.checkTok(check_val=')')
        elif self.tok['value'] == "(":
            call = "".join([self.class_name, ".", id])
            if self.ids.kindOf('this'):
                self.writer.writePush(self.ids.kindOf('this'), self.ids.indexOf('this'))
            else:
                self.writer.writePush('pointer', 0)
            self.nextToken()
            nargs = self.compileExpressionList() + 1
            self.checkTok(check_val=')')
        self.writer.writeCall(call, nargs)


if __name__ == '__main__':
    source = sys.argv[1]
    jacks = [x for x in glob.glob(source + '/*.jack')]
    # print(jacks)
    for jack in jacks:
        parser = CompilationEngine(jack)
