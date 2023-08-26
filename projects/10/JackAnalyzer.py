import re
import glob
import sys

regleft = re.compile(r'(?<=\S)([.{}()\[\]+\-|=<>,;&~]|(?<![*/])[/*])')
regright = re.compile(r'([.{}()\[\]+\-|=<>,;&~]|[/*](?![*/]))(?=\S)')


class JackTokenizer:

    def __init__(self, file):
        self.input = open(file, 'r')
        # self.output = open(f"{file.split('.jack')[0]}T2.xml", 'a')
        # self.output.write('<tokens>\n')
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
            # print(self.line)

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
            # self.output.write('</tokens>\n')
            # self.output.close()
            return False

    def tokenType(self) -> str:
        if self.kws.get(self.token, None):
            # self.output.write(f'<keyword> {self.token} </keyword>\n')
            return 'keyword'
        elif self.symbols.get(self.token, None):
            # match self.token:
            #     case '<':
            #         self.output.write('<symbol> &lt; </symbol>\n')
            #     case '>':
            #         self.output.write('<symbol> &gt; </symbol>\n')
            #     case '&':
            #         self.output.write('<symbol> &amp; </symbol>\n')
            #     case _:
            #         self.output.write(f'<symbol> {self.token} </symbol>\n')
            return 'symbol'
        else:
            try:
                if 0 <= int(self.token) <= 32767:
                    # self.output.write(f'<integerConstant> {self.token} </integerConstant>\n')
                    return 'integerConstant'
            except ValueError:
                pass
        if len(self.token) > 1 and ((self.token[0] and self.token[-1]) == '"'):
            # self.output.write(f'<stringConstant> {self.token[1:-1]} </stringConstant>\n')
            return 'stringConstant'
        else:
            # self.output.write(f'<identifier> {self.token} </identifier>\n')
            return 'identifier'

    def keyWord(self):
        return self.token

    def symbol(self):
        match self.token:
            case '<':
                return '&lt;'
            case '>':
                return '&gt;'
            case '&':
                return '&amp;'
        return self.token

    def identifier(self):
        return self.token

    def intVal(self):
        return int(self.token)

    def stringVal(self):
        return self.token[1:-1]


class CompilationEngine:

    def __init__(self, file):
        self.tk = JackTokenizer(file)
        self.output = open(f"{file.split('.jack')[0]}Mine.xml", 'a')
        self.tab = 0
        self.tok = {'type': '', 'token': ''}
        self.compileClass()

    def nextToken(self):
        if self.tk.hasMoreTokens():
            self.tok['type'] = self.tk.tokenType()
            match self.tok['type']:
                case 'keyword':
                    self.tok['token'] = self.tk.keyWord()
                case 'symbol':
                    self.tok['token'] = self.tk.symbol()
                case 'identifier':
                    self.tok['token'] = self.tk.identifier()
                case 'integerConstant':
                    self.tok['token'] = self.tk.intVal()
                case 'stringConstant':
                    self.tok['token'] = self.tk.stringVal()
            self.tk.advance()

    def writeTok(self):
        self.output.write(('  '*self.tab)+f'<{self.tok["type"]}> {self.tok["token"]} </{self.tok["type"]}>\n')
        self.nextToken()

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
        assert self.tok['token'] == 'class'
        self.writeTok()
        
        assert self.tok['type'] == 'identifier'
        self.writeTok()
        
        assert self.tok['token'] == '{'
        self.writeTok()
        
        while self.tok['token'] in ['static', 'field']:
            self.compileClassVarDec()          
            
        while self.tok['token'] in ['constructor', 'function', 'method']:
            self.compileSubroutine()
            
        assert self.tok['token'] == '}'
        self.writeTok()
        self.writeTag('class', False)
        self.output.close()

    def compileClassVarDec(self):
        self.writeTag('classVarDec', True)
        self.writeTok()  # checked this was field or static before calling this method
        
        self.writeTok()  # no checking on the type because it could be a custom identifier
        # var name
        assert self.tok['type'] == 'identifier'
        self.writeTok()
        # if there is a comma + more var names
        while self.tok['token'] == ',':
            self.writeTok()
            assert self.tok['type'] == 'identifier'
            self.writeTok()
        # list of var names ended (or never existed)
        assert self.tok['token'] == ';'
        self.writeTok()
        self.writeTag('classVarDec', False)

    def compileSubroutine(self):
        self.writeTag('subroutineDec', True)
        self.writeTok()  # checked for constructor, method, function, before calling
        
        # later: check this is void, int, char, boolean, or type == 'identifier'
        self.writeTok()
        
        assert self.tok['type'] == 'identifier'
        self.writeTok()
        
        assert self.tok['token'] == '('
        self.writeTok()
        
        self.compileParameterList()
        assert self.tok['token'] == ')'
        self.writeTok()
        
        self.writeTag('subroutineBody', True)
        assert self.tok['token'] == '{'
        self.writeTok()
        while self.tok['token'] == 'var':
            self.compileVarDec()

        self.compileStatements()
        assert self.tok['token'] == '}'
        self.writeTok()
        self.writeTag('subroutineBody', False)
        self.writeTag('subroutineDec', False)
    
    def compileParameterList(self):
        self.writeTag('parameterList', True)
        while self.tok['token'] != ')':
            while True:
                self.writeTok()  # parameter type
                # parameter name
                assert self.tok['type'] == 'identifier'
                self.writeTok()
                # if there are no more parameters, break the loop
                if self.tok['token'] != ',':
                    break
                self.writeTok()
                
        self.writeTag('parameterList', False)
    
    def compileVarDec(self):
        self.writeTag('varDec', True)
        self.writeTok()  # already checked this was 'var'
        self.writeTok()  # var type
        # var name
        assert self.tok['type'] == 'identifier'
        self.writeTok()
        # write commas and var names if they exist
        while self.tok['token'] == ',':
            self.writeTok()
            assert self.tok['type'] == 'identifier'
            self.writeTok()
        # end declaration
        assert self.tok['token'] == ';'
        self.writeTok()
        self.writeTag('varDec', False)

    def compileStatements(self):
        self.writeTag('statements', True)
        while self.tok['token'] != '}':
            match self.tok['token']:
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
        assert self.tok['type'] == 'identifier'
        self.writeTok()
        if self.tok['token'] == '.':
            self.writeTok()
            assert self.tok['type'] == 'identifier'
            self.writeTok()
        assert self.tok['token'] == '('
        self.writeTok()
        self.compileExpressionList()
        assert self.tok['token'] == ')'
        self.writeTok()
        assert self.tok['token'] == ';'
        self.writeTok()
        self.writeTag('doStatement', False)

    def compileLet(self):
        self.writeTag('letStatement', True)
        self.writeTok()
        assert self.tok['type'] == 'identifier'
        self.writeTok()
        # HERE: ADD EXPRESSION HANDLING
        assert self.tok['token'] == '='
        self.writeTok()
        self.compileExpression()
        assert self.tok['token'] == ';'
        self.writeTok()
        self.writeTag('letStatement', False)

    def compileWhile(self):
        self.writeTag('whileStatement', True)
        self.writeTok()
        assert self.tok['token'] == '('
        self.writeTok()
        self.compileExpression()
        assert self.tok['token'] == ')'
        self.writeTok()
        assert self.tok['token'] == '{'
        self.writeTok()
        self.compileStatements()
        assert self.tok['token'] == '}'
        self.writeTok()
        self.writeTag('whileStatement', False)

    def compileReturn(self):
        self.writeTag('returnStatement', True)
        self.writeTok()
        if self.tok['token'] != ';':
            self.compileExpression()
        assert self.tok['token'] == ';'
        self.writeTok()
        self.writeTag('returnStatement', False)

    def compileIf(self):
        self.writeTag('ifStatement', True)
        self.writeTok()
        assert self.tok['token'] == '('
        self.writeTok()
        self.compileExpression()
        assert self.tok['token'] == ')'
        self.writeTok()
        assert self.tok['token'] == '{'
        self.writeTok()
        self.compileStatements()
        assert self.tok['token'] == '}'
        self.writeTok()
        if self.tok['token'] == 'else':
            self.writeTok()
            assert self.tok['token'] == '{'
            self.writeTok()
            self.compileStatements()
            assert self.tok['token'] == '}'
            self.writeTok()
        self.writeTag('ifStatement', False)

    def compileExpression(self):
        self.writeTag('expression', True)
        self.compileTerm()
        self.writeTag('expression', False)

    def compileTerm(self):
        self.writeTag('term', True)
        self.writeTok()
        self.writeTag('term', False)

    def compileExpressionList(self):
        self.writeTag('expressionList', True)
        while self.tok['token'] != ')':
            self.compileExpression()
            if self.tok['token'] != ',':
                break
            self.writeTok()  # write the comma and continue the loop to compile the next expression
        self.writeTag('expressionList', False)


if __name__ == '__main__':
    source = sys.argv[1]
    jacks = [x for x in glob.glob(source + '/*.jack')]
    print(jacks)
    for jack in jacks:
        parser = CompilationEngine(jack)
