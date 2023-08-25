import re
import glob
import sys

regleft = re.compile(r'(?<=\S)([.{}()\[\]+\-|=<>,;&~]|(?<![*/])[/*])')
regright = re.compile(r'([.{}()\[\]+\-|=<>,;&~]|[/*](?![*/]))(?=\S)')


class JackTokenizer:

    def __init__(self, file):
        self.input = open(file, 'r')
        self.output = open(f"{file.split('.jack')[0]}Tmine.xml", 'a')
        self.output.write('<tokens>\n')
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
            self.output.write('</tokens>\n')
            self.output.close()
            return False

    def tokenType(self) -> str:
        if self.kws.get(self.token, None):
            self.output.write(f'<keyword> {self.token} </keyword>\n')
            return 'KEYWORD'
        elif self.symbols.get(self.token, None):
            match self.token:
                case "<":
                    self.output.write('<symbol> &lt; </symbol>\n')
                case ">":
                    self.output.write('<symbol> &gt; </symbol>\n')
                case "&":
                    self.output.write('<symbol> &amp; </symbol>\n')
                case _:
                    self.output.write(f'<symbol> {self.token} </symbol>\n')
            return 'SYMBOL'
        else:
            try:
                if 0 <= int(self.token) <= 32767:
                    self.output.write(f'<integerConstant> {self.token} </integerConstant>\n')
                    return 'INT_CONST'
            except ValueError:
                pass
        if len(self.token) > 1 and (self.token[0] == '"' and self.token[-1] == '"'):
            self.output.write(f'<stringConstant> {self.token[1:-1]} </stringConstant>\n')
            return "STRING_CONST"
        else:
            self.output.write(f'<identifier> {self.token} </identifier>\n')
            return "IDENTIFIER"


if __name__ == '__main__':
    source = sys.argv[1]
    jacks = [x for x in glob.glob(source + "/*.jack")]
    print(jacks)
    for jack in jacks:
        tokenizer = JackTokenizer(jack)
        while tokenizer.hasMoreTokens():
            tokenizer.tokenType()
            tokenizer.advance()
