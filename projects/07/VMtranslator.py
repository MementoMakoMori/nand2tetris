import sys
import os
import glob


def get_filename(path: str):
#    i = -1
#    while path[i] != "/":
#    	i -= 1
#    return path[:i+1], path[i+1:].split(".")[0]    
    path = path.split("/")[-1]
    return path.split(".")[0]


class Parser:
    def __init__(self, path: str):
        self.files = [x for x in glob.glob(path+"/*.vm")] if os.path.isdir(path) else [path]
        self.input = open(self.files.pop(0), 'r')
        self.current = None
        self.advance()
        self.writer = CodeWriter(get_filename(path))
        self.writer.set_curr_file(self.input.name)

    def advance(self):
        self.current = self.input.readline()
        while self.current and (self.current[0] == "/" or self.current[0] == "\n"):
            self.current = self.input.readline()
        self.current = self.current.split("//")[0]
        self.current = self.current.strip()

    def hasMoreCommands(self):
        if self.current:
            return True
        else:
            if len(self.files) > 0:
                self.input.close()
                self.input = open(self.files.pop(0), 'r')
                self.writer.set_curr_file(self.input.name)
                self.advance()
                self.hasMoreCommands()
        self.input.close()
        return False

    def commandType(self):
        math = {k: "C_ARITHMETIC" for k in ["add", "sub", "neg", "eq", "gt", "lt", "and", "or", "not"]}
        commands = {"push": "C_PUSH", "pop": "C_POP", "label": "C_LABEL", "goto": "C_GOTO", "if": "C_IF",
                    "function": "C_FUNCTION", "return": "C_RETURN", "call": "C_CALL"}
        commands = commands | math
        return commands[self.current.split()[0]]

    def arg1(self) -> str:
        match self.commandType():
            case "C_ARITHMETIC":
                return self.current.split()[0]
            case _:
                return self.current.split()[1]

    def arg2(self) -> int:
        return int(self.current.split()[-1])


class CodeWriter:
    def __init__(self, name):
        self.file = open("{}.asm".format(name), 'w')
        self.curr_file = None
        self.num = 1
        self.defs = {'inc': "\n".join(["@SP", "M=M+1"]), 'dec': "\n".join(["@SP", "M=M-1"]),
                     'yes': "\n".join(["@SP", "A=M", "M=-1"]), 'no': "\n".join(["@SP", "A=M", "M=0"])}
        self.defs.update({'push': "\n".join(["@SP", "A=M", "M=D", self.defs['inc']]), 'pop': "\n".join([self.defs['dec'], "A=M", "D=M"])})

    def set_curr_file(self, file: str):
        self.curr_file = get_filename(file)

    def writeArithmetic(self, command: str):
        asm = None
        if command == "neg":
            asm = "\n".join([self.defs['dec'], "A=M", "M=-M"])
        elif command == "not":
            asm = "\n".join([self.defs['dec'], "A=M", "M=!M"])
        else:
            asm = "\n".join([self.defs['dec'], "A=M", "D=M", self.defs['dec'], "A=M"])
            match command:
                case "add":
                    asm = "\n".join([asm, "M=D+M"])
                case "sub":
                    asm = "\n".join([asm, "M=M-D"])
                case "eq":
                    asm = "\n".join([asm, "D=D-M", f"@EQ{self.num}", "D;JEQ", self.defs['no'], f"@EQINC{self.num}", "0;JMP", f"(EQ{self.num})", self.defs['yes'], f"(EQINC{self.num})"])
                    self.num += 1
                case "gt":
                    asm = "\n".join([asm, "D=M-D", f"@GT{self.num}", "D;JGT", self.defs['no'], f"@GTINC{self.num}", "0;JMP", f"(GT{self.num})", self.defs['yes'], f"(GTINC{self.num})"])
                    self.num += 1
                case "lt":
                    asm = "\n".join([asm, "D=M-D", f"@LT{self.num}", "D;JLT", self.defs['no'], f"@LTINC{self.num}", "0;JMP", f"(LT{self.num})", self.defs['yes'], f"(LTINC{self.num})"])
                    self.num += 1
                case "and":
                    asm = "\n".join([asm, "M=D&M"])
                case "or":
                    asm = "\n".join([asm, "M=D|M"])
        assert asm is not None
        self.file.write("\n".join([asm, self.defs['inc'], ""]))

    def writePushPop(self, command: str, segment: str, index: int):
        asm = None
        address = {"local": "@LCL", "argument": "@ARG", "this": "@THIS", "that": "@THAT",
                   "pointer": "@R"+str(3+index), "temp": "@R"+str(5+index), "constant": "@"+str(index),
                   "static": "@"+self.curr_file+"."+str(index)}
        if segment in ["local", "argument", "this", "that"]:
            match command:
                case "push":
                    asm = "\n".join(["@"+str(index), "D=A", address[segment], "A=D+M", "D=M", self.defs['push']])
                case "pop":
                    asm = "\n".join(["@"+str(index), "D=A", address[segment], "D=D+M", "@R13", "M=D", self.defs['pop'],
                                     "@R13", "A=M", "M=D"])
        if segment in ["pointer", "temp", "static"]:
            match command:
                case "push":
                    asm = "\n".join([address[segment], "D=M", self.defs['push']])
                case "pop":
                    asm = "\n".join([self.defs['pop'], address[segment], "M=D"])
        if segment == "constant":
            asm = "\n".join([address[segment], "D=A", self.defs['push']])
        assert asm is not None
        self.file.write(asm+"\n")


if __name__ == "__main__":
    file = sys.argv[1]
    parse = Parser(file)
    while parse.hasMoreCommands():
        if parse.commandType() == "C_ARITHMETIC":
            parse.writer.writeArithmetic(parse.arg1())
        else:
            parse.writer.writePushPop(parse.current.split()[0], parse.arg1(), parse.arg2())
        parse.advance()
    parse.writer.file.close()

