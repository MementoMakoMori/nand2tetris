import re
import glob
import sys

# regleft = re.compile(r'(?<=\S)([.{}()\[\]+\-|=<>,;&~]|(?<![*/])[/*])')
# regright = re.compile(r'([.{}()\[\]+\-|=<>,;&~]|[/*](?![*/]))(?=\S)')


class JackTokenizer:

    def __init__(self, file):
        self.input = open(file, 'r')
        self.line = None
        self.token = 'init'
        self.symbols = {k: True for k in '{}()[].,;+-*/&|<>=-~'} # replace with hash set
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
        self.output = open(f"{file.split('.jack')[0]}Mine.xml", 'a')
        self.tab = 0
        self.tok = {'type': '', 'value': ''}
        self.check = {'ops': {x for x in '+-*/&|<>='}, 'unary': {y for y in '-~'}, 'kws': {z for z in ['true', 'false', 'null', 'this']}}
        self.compileClass()

    def nextToken(self):
        if self.tk.hasMoreTokens():
            self.tok['type'] = self.tk.tokenType()
            self.tok['value'] = self.tk.tokenValue(self.tok['type'])
            self.tk.advance()

    def writeTok(self):
        self.output.write(('  '*self.tab)+f'<{self.tok["type"]}> {self.tok["value"]} </{self.tok["type"]}>\n')
        self.nextToken()

    def checkTok(self, check_type: str = None, check_val: str = None):
        if check_type and self.tok['type'] != check_type:
            raise SyntaxError(f"Unexpected token type: {self.tok['value']} of type {self.tok['type']}")
        if check_val and self.tok['value'] != check_val:
            raise SyntaxError(f"Unexpected token value: {self.tok['value']} of type {self.tok['type']}")
        self.writeTok()

    def writeTag(self, tag: str, start: bool):
        if start:
            self.output.write(('  '*self.tab) + f'<{tag}>\n')
            self.tab += 1
        else:
            self.tab -= 1
            self.output.write(('  '*self.tab) + f'</{tag}>\n')

    def compileClass(self):
        self.writeTag('class', True)
        self.nextToken()
        self.checkTok(check_val='class')
        self.checkTok(check_type='identifier')
        self.checkTok(check_val='{')
        
        while self.tok['value'] in ['static', 'field']:
            self.compileClassVarDec()          
            
        while self.tok['value'] in ['constructor', 'function', 'method']:
            self.compileSubroutine()

        self.checkTok(check_val='}')
        self.writeTag('class', False)
        self.output.close()

    def compileClassVarDec(self):
        self.writeTag('classVarDec', True)
        self.writeTok()  # checked this was field or static before calling this method
        
        self.writeTok()  # no checking on the type because it could be a custom identifier
        # var name
        self.checkTok(check_type='identifier')

        # if there is a comma + more var names
        while self.tok['value'] == ',':
            self.writeTok()
            self.checkTok(check_type='identifier')

        # list of var names ended (or never existed)
        self.checkTok(check_val=';')
        self.writeTag('classVarDec', False)

    def compileSubroutine(self):
        self.writeTag('subroutineDec', True)
        self.writeTok()  # checked for constructor, method, function, before calling
        
        # return type
        self.writeTok()
        # subroutine name and optional params
        self.checkTok(check_type='identifier')
        self.checkTok(check_val='(')
        self.compileParameterList()
        self.checkTok(check_val=')')
        
        self.writeTag('subroutineBody', True)
        self.checkTok(check_val='{')
        while self.tok['value'] == 'var':
            self.compileVarDec()
        self.compileStatements()
        self.checkTok(check_val='}')

        self.writeTag('subroutineBody', False)
        self.writeTag('subroutineDec', False)
    
    def compileParameterList(self):
        self.writeTag('parameterList', True)

        while self.tok['value'] != ')':
            while True:
                self.writeTok()  # parameter type
                # parameter name
                self.checkTok(check_type='identifier')
                # if there are no more parameters, break the loop
                if self.tok['value'] != ',':
                    break
                self.writeTok()
                
        self.writeTag('parameterList', False)
    
    def compileVarDec(self):
        self.writeTag('varDec', True)
        self.writeTok()  # already checked this was 'var'
        self.writeTok()  # var type
        # var name
        self.checkTok(check_type='identifier')
        # write commas and var names if they exist
        while self.tok['value'] == ',':
            self.writeTok()
            self.checkTok(check_type='identifier')
        # end declaration
        self.checkTok(check_val=';')
        self.writeTag('varDec', False)

    def compileStatements(self):
        self.writeTag('statements', True)
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
        self.writeTag('statements', False)

    def compileDo(self):
        self.writeTag('doStatement', True)
        self.writeTok()

        self.checkTok(check_type='identifier')
        if self.tok['value'] == '.':
            self.writeTok()
            self.checkTok(check_type='identifier')
        self.checkTok(check_val='(')
        self.compileExpressionList()
        self.checkTok(check_val=')')
        self.checkTok(check_val=';')
        self.writeTag('doStatement', False)

    def compileLet(self):
        self.writeTag('letStatement', True)
        self.writeTok()

        self.checkTok(check_type='identifier')
        if self.tok['value'] == '[':
            self.writeTok()
            self.compileExpression()
            self.checkTok(check_val=']')
        self.checkTok(check_val='=')
        self.compileExpression()
        self.checkTok(check_val=';')

        self.writeTag('letStatement', False)

    def compileWhile(self):
        self.writeTag('whileStatement', True)
        self.writeTok()

        self.checkTok(check_val='(')
        self.compileExpression()
        self.checkTok(check_val=')')

        self.checkTok(check_val='{')
        self.compileStatements()
        self.checkTok(check_val='}')

        self.writeTag('whileStatement', False)

    def compileReturn(self):
        self.writeTag('returnStatement', True)
        self.writeTok()

        if self.tok['value'] != ';':
            self.compileExpression()
        self.checkTok(check_val=';')

        self.writeTag('returnStatement', False)

    def compileIf(self):
        self.writeTag('ifStatement', True)
        self.writeTok()

        self.checkTok(check_val='(')
        self.compileExpression()
        self.checkTok(check_val=')')

        self.checkTok(check_val='{')
        self.compileStatements()
        self.checkTok(check_val='}')

        if self.tok['value'] == 'else':
            self.writeTok()
            self.checkTok(check_val='{')
            self.compileStatements()
            self.checkTok(check_val='}')

        self.writeTag('ifStatement', False)

    def compileExpression(self):
        self.writeTag('expression', True)

        self.compileTerm()
        while self.tok['value'] in self.check['ops']:
            match self.tok['value']:
                case '<':
                    self.tok['value'] = '&lt;'
                case '>':
                    self.tok['value'] = '&gt;'
                case '&':
                    self.tok['value'] = '&amp;'
            self.writeTok()
            self.compileTerm()

        self.writeTag('expression', False)

    def compileTerm(self):
        self.writeTag('term', True)

        if self.tok['value'] == '(':
            self.writeTok()
            self.compileExpression()
            self.checkTok(check_val=')')

        elif self.tok['value'] in self.check['unary']:
            self.writeTok()
            self.compileTerm()
        elif self.tok['type'] in ['integerConstant', 'stringConstant'] or self.check['value'] in self.check['kws']:
            self.writeTok()
        elif self.tok['type'] == 'identifier':
            self.writeTok()
            if self.tok['value'] == '[':
                self.writeTok()
                self.compileExpression()
                self.checkTok(check_val=']')

            elif self.tok['value'] == '.':
                self.writeTok()
                self.checkTok(check_type='identifier')

            if self.tok['value'] == '(':
                self.writeTok()
                self.compileExpressionList()
                self.checkTok(check_val=')')

        self.writeTag('term', False)

    def compileExpressionList(self):
        self.writeTag('expressionList', True)

        while self.tok['value'] != ')':
            self.compileExpression()
            if self.tok['value'] != ',':
                break
            self.writeTok()  # write the comma and continue the loop to compile the next expression

        self.writeTag('expressionList', False)


if __name__ == '__main__':
    source = sys.argv[1]
    jacks = [x for x in glob.glob(source + '/*.jack')]
    # print(jacks)
    for jack in jacks:
        parser = CompilationEngine(jack)
