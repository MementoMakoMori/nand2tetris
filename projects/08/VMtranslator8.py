import sys
import os
import glob


def path_info(full_path: str):
    split_path = full_path.split("/")
    if os.path.isdir(full_path):
        dir_path = full_path
        files = [x for x in glob.glob(full_path + "/*.vm")]
        out_name = split_path[-1]
        return dir_path, files, out_name
    else:
        dir_path = "/".join(split_path[:-1])
        files = [full_path]
        out_name = split_path[-2]
        return dir_path, files, out_name


def get_filename(file_path):
    return file_path.split('/')[-1].split(".")[0]


class Parser:
    def __init__(self, path: str):
        self.dir, self.files, self.name = path_info(path)
        self.input = open(self.files.pop(0), 'r')
        self.current = None
        self.advance()
        self.writer = CodeWriter(self.name, self.dir)
        self.writer.set_static_label(get_filename(self.input.name))
        self.writer.writeInit()
        math = {k: "C_ARITHMETIC" for k in ["add", "sub", "neg", "eq", "gt", "lt", "and", "or", "not"]}
        coms = {"push": "C_PUSH", "pop": "C_POP", "label": "C_LABEL", "goto": "C_GOTO", "if-goto": "C_IF",
                "function": "C_FUNCTION", "return": "C_RETURN", "call": "C_CALL"}
        self.commands = coms | math

    def advance(self):
        self.current = self.input.readline()
        while self.current and (self.current[0] == "/" or self.current[0] == "\n"):
            self.current = self.input.readline()
        self.current = self.current.split("//")[0]
        self.current = self.current.strip()

    def hasMoreCommands(self):
        if self.current:
            return True
        elif len(self.files) > 0:
            self.input.close()
            self.input = open(self.files.pop(0), 'r')
            self.writer.set_static_label(get_filename(self.input.name))
            self.advance()
            self.hasMoreCommands()
            return True
        else:
            self.input.close()
            return False

    def commandType(self):
        return self.commands[self.current.split()[0]]

    def arg1(self) -> str:
        match self.commandType():
            case "C_ARITHMETIC":
                return self.current.split()[0]
            case _:
                return self.current.split()[1]

    def arg2(self) -> int:
        return int(self.current.split()[-1])


class CodeWriter:
    def __init__(self, name: str, loc: str):
        self.file = open("{}/{}.asm".format(loc, name), 'w')
        self.static_label = ""
        self.function_label = ""
        self.num = 0
        self.defs = {'inc': "\n".join(["@SP", "M=M+1"]), 'dec': "\n".join(["@SP", "M=M-1"]),
                     'yes': "\n".join(["@SP", "A=M", "M=-1"]), 'no': "\n".join(["@SP", "A=M", "M=0"])}
        self.defs.update({'push': "\n".join(["@SP", "A=M", "M=D", self.defs['inc']]),
                          'pop': "\n".join([self.defs['dec'], "A=M", "D=M"])})

    def set_static_label(self, static_name: str):
        self.static_label = static_name + "."

    def writeInit(self):
        self.file.write("\n".join(["//set pointer to 256", "@256", "D=A", "@SP", "M=D", ""]))
        self.writeCall('Sys.init', 0)

    def writeLabel(self, label: str, func: bool = False):
        if not func:
            self.file.write("".join(["(", self.function_label, label, ")\n"]))
        else:
            self.file.write("".join(["(", label, ")\n"]))

    def writeGoto(self, label: str):
        self.file.write("".join(["@", self.function_label, label, "\n0;JMP\n"]))

    def writeIf(self, label: str):
        self.file.write("\n".join([self.defs['pop'], "@" + self.function_label + label, "D;JNE\n"]))

    def writeCall(self, functionName: str, numArgs: int):
        """
        0. create return-address label
        1. push return-address label, LCL address, ARG, THIS, THAT onto stack
        3. set LCL to SP
        4. set ARG to LCL-numArgs-5
        5. jump to function
        6. write return-address label
        """
        return_label = self.function_label + "return-address." + str(self.num)
        self.num += 1
        push_label = "\n".join(["@" + return_label, "D=A", self.defs['push']])
        copy_state = f"\n{self.defs['push']}\n".join(["@LCL\t//start copy_state\nD=M", "@ARG\nD=M", "@THIS\nD=M",
                                                      "@THAT\nD=M", "//end copy_state"])
        set_arg = "\n".join(["\n".join(["D=D-1" for i in range(numArgs + 5)]), "@ARG", "M=D"])
        go_to = "\n".join(["@" + functionName + "\t//goto function", "0;JMP"])
        asm = "\n".join([push_label, copy_state, "D=M", "@LCL", "M=D", set_arg, go_to, ""])
        self.file.write(asm)
        self.file.write("".join(["(", return_label, ")\n"]))

    def writeReturn(self):
        """
        1. put return value in correct mem location
        2. put arg+1 (pre-call pointer location) and return address in temp variables
        3. set pointer to LCL, pop down the list to reset LCL ARG THIS THAT
        4. restore pointer location
        5. jump to return address
        """
        temp1 = "".join(["@", self.function_label, "POINT", str(self.num)])
        temp2 = "".join(["@", self.function_label, "RET", str(self.num)])
        val = "".join(["@", self.function_label, "VAL", str(self.num)])
        arg_point = "".join(["@", self.function_label, "ARG_POINT", str(self.num)])
        save_return = "\n".join([self.defs['pop'], val, "M=D", "@ARG", "D=M", arg_point, "M=D", temp1, "M=D+1"])
        # save_return = "\n".join([self.defs['pop'], "@ARG\t//put return value in ARG 0", "A=M", "M=D",
        #                          "@ARG\t//save ARG 1 address as pointer location", "D=M", "D=D+1", temp1, "M=D"])
        get_add = "\n".join(["@LCL", "D=M", "\n".join(["D=D-1" for i in range(5)]),
                             "A=D\t//go to address where return-address was stored", "D=M", temp2,
                             "M=D\t//put return-address in temp"])
        ignore_local = "\n".join(["@LCL", "D=M", "@SP", "M=D"])
        reset_state = f"{self.defs['pop']}\n".join(["", "@THAT\nM=D\n", "@THIS\nM=D\n", "@ARG\nM=D\n", "@LCL\nM=D"])
        set_return = "\n".join([val, "D=M", arg_point, "A=M", "M=D"])
        reset_point = "\n".join([temp1, "D=M", "@SP\t//restore pointer to pre-function spot", "M=D"])
        go_return = "\n".join([temp2, "A=M", "0;JMP"])
        self.file.write("\n".join([save_return, get_add, ignore_local, reset_state, set_return, reset_point, go_return, ""]))
        self.num += 1

    def writeFunction(self, functionName: str, numLocals: int):
        self.writeLabel(functionName, True)
        for i in range(numLocals):
            self.writePushPop('push', 'constant', 0)
        self.function_label = functionName + "$"
        self.num = 0

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
                    yes_label = "".join([self.function_label, "EQ", str(self.num)])
                    inc_label = "".join([self.function_label, "EQINC", str(self.num)])
                    asm = "\n".join([asm, "D=D-M", "@" + yes_label, "D;JEQ", self.defs['no'], "@" + inc_label,
                                     "0;JMP", "(" + yes_label + ")", self.defs['yes'], "(" + inc_label + ")"])
                    self.num += 1
                case "gt":
                    yes_label = "".join([self.function_label, "GT", str(self.num)])
                    inc_label = "".join([self.function_label, "GTINC", str(self.num)])
                    asm = "\n".join([asm, "D=M-D", "@" + yes_label, "D;JGT", self.defs['no'], "@" + inc_label,
                                     "0;JMP", "(" + yes_label + ")", self.defs['yes'], "(" + inc_label + ")"])
                    self.num += 1
                case "lt":
                    yes_label = "".join([self.function_label, "LT", str(self.num)])
                    inc_label = "".join([self.function_label, "LTINC", str(self.num)])
                    asm = "\n".join([asm, "D=M-D", "@" + yes_label, "D;JLT", self.defs['no'], "@" + inc_label,
                                     "0;JMP", "(" + yes_label + ")", self.defs['yes'], "(" + inc_label + ")"])
                    self.num += 1
                case "and":
                    asm = "\n".join([asm, "M=D&M"])
                case "or":
                    asm = "\n".join([asm, "M=D|M"])
        assert asm is not None
        self.file.write("\n".join([asm, self.defs['inc'], ""]))

    def writePushPop(self, command: str, segment: str, index):
        asm = None
        address = {"local": "@LCL", "argument": "@ARG", "this": "@THIS", "that": "@THAT",
                   "pointer": "@R" + str(3 + index), "temp": "@R" + str(5 + index), "constant": "@" + str(index),
                   "static": "@" + self.static_label + str(index)}
        if segment in ["local", "argument", "this", "that"]:
            match command:
                case "push":
                    asm = "\n".join(["@" + str(index), "D=A", address[segment], "A=D+M", "D=M", self.defs['push']])
                case "pop":
                    asm = "\n".join(
                        ["@" + str(index), "D=A", address[segment], "D=D+M", "@R13", "M=D", self.defs['pop'],
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
        self.file.write(asm + "\n")


if __name__ == "__main__":
    file = sys.argv[1]
    parse = Parser(file)
    while parse.hasMoreCommands():
        match parse.commandType():
            case "C_LABEL":
                parse.writer.writeLabel(parse.arg1())
            case "C_IF":
                parse.writer.writeIf(parse.arg1())
            case "C_GOTO":
                parse.writer.writeGoto(parse.arg1())
            case "C_CALL":
                parse.writer.writeCall(parse.arg1(), parse.arg2())
            case "C_FUNCTION":
                parse.writer.writeFunction(parse.arg1(), parse.arg2())
            case "C_RETURN":
                parse.writer.writeReturn()
            case "C_ARITHMETIC":
                parse.writer.writeArithmetic(parse.arg1())
            case _:
                parse.writer.writePushPop(parse.current.split()[0], parse.arg1(), parse.arg2())
        parse.advance()
    parse.writer.file.close()
