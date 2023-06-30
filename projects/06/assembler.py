import sys


class Parser:
    def __init__(self, file):
        self.path = file
        self.table = SymbolTable()
        self.code = Code()
        self.file = None
        self.current = None

    def Pass1(self):
        ROM = 0
        self.file = open(self.path, 'r')
        self.advance()
        while self.hasMoreCommands():
            if self.commandType() == "L_COMMAND":
                self.table.addEntry(self.symbol(), ROM)
            else:
                ROM += 1
            self.advance()
        self.file.close()

    def Pass2(self):
        self.file = open(self.path, "r")
        self.advance()
        with open("Prog.hack", "w") as out:
            avail = 16
            while self.hasMoreCommands():
                if self.commandType() == "A_COMMAND":
                    try:
                        out.write("".join(["0", "{0:015b}".format(int(self.symbol())), "\n"]))
                    except ValueError:
                        if self.table.contains(self.symbol()):
                            out.write("".join(["0", "{0:015b}".format(self.table.getAddress(self.symbol())), "\n"]))
                        else:
                            self.table.addEntry(self.symbol(), avail)
                            out.write("".join(["0", "{0:015b}".format(int(avail)), "\n"]))
                            avail += 1
                if self.commandType() == "C_COMMAND":
                    out.write("".join(["111", self.code.comp(self.comp()), self.code.dest(self.dest()),
                                       self.code.jump(self.jump()), "\n"]))
                self.advance()
        self.file.close()

    def hasMoreCommands(self):
        if self.current:
            return True
        else:
            return False

    def advance(self):
        self.current = self.file.readline()
        while self.current and (self.current[0] == "/" or self.current[0] == "\n"):
            self.current = self.file.readline()
        self.current = self.current.split("//")[0]
        self.current = self.current.strip()

    def commandType(self):
        match self.current[0]:
            case "@":
                return "A_COMMAND"
            case "(":
                return "L_COMMAND"
            case _:
                return "C_COMMAND"

    def symbol(self):
        symb = self.current[1:]
        if symb[-1] == ")":
            return symb[:-1]
        else:
            return symb

    def dest(self):
        if "=" not in self.current:
            return "null"
        else:
            d = self.current.split("=")
            assert d[0] in ["M", "D", "MD", "A", "AM", "AD", "AMD"]
            return d[0]

    def comp(self):
        c = self.current.split(";")
        if self.dest() == "null":
            c = c[0]
        else:
            c = c[0].split("=")[1]
        assert c in ["0", "1", "-1", "D", "A", "!D", "!A", "-D", "-A", "D+1", "A+1", "D-1", "A-1", "D+A", "D-A", "A-D",
                     "D&A", "D|A", "M", "!M", "-M", "M+1", "M-1", "D+M", "D-M", "M-D", "D&M", "D|M"]
        return c

    def jump(self):
        if ";" not in self.current:
            return "null"
        else:
            j = self.current.split(';')[1]
            assert j in ["null", "JGT", "JEQ", "JGE", "JLT", "JNE", "JLE", "JMP"]
            return j


class Code:
    def __init__(self):
        pass

    def dest(self, mne: str):
        return "".join(['1' if char in mne else '0' for char in 'ADM'])  # thanks Aaron!

    def comp(self, mne: str):
        comps = {
            '0': '0101010', '1': '0111111', '-1': '0111010', 'D': '0001100', 'A': '0110000', '!D': '0001101',
            '!A': '0110001', '-D': '0001111', '-A': '0110011', 'D+1': '0011111', 'A+1': '0110111', 'D-1': '0001110',
            'A-1': '0110010', 'D+A': '0000010', 'D-A': '0010011', 'A-D': '0000111', 'D&A': '0000000',
            'D|A': '0010101', 'M': '1110000', '!M': '1110001', '-M': '1110011', 'M+1': '1110111', 'M-1': '1110010',
            'D+M': '1000010', 'D-M': '1010011', 'M-D': '1000111', 'D&M': '1000000', 'D|M': '1010101'
        }
        return comps[mne]

    def jump(self, mne: str):
        jumps = {'null': '000', 'JGT': '001', 'JEQ': '010', 'JGE': '011', 'JLT': '100', 'JNE': '101', 'JLE': '110',
                 'JMP': '111'}
        return jumps[mne]


class SymbolTable:
    def __init__(self):
        self.table = {"SP": 0, "LCL": 1, "ARG": 2, "THIS": 3, "THAT": 4, "R0": 0, "R1": 1, "R2": 2, "R3": 3, "R4": 4,
                      "R5": 5, "R6": 6, "R7": 7, "R8": 8, "R9": 9, "R10": 10, "R11": 11, "R12": 12, "R13": 13, "R14":
                          14, "R15": 15, "SCREEN": 16384, "KBD": 24576}

    def addEntry(self, symbol: str, address: int):
        self.table[symbol] = address

    def contains(self, symbol: str) -> bool:
        # return symbol in self.table.keys()
        return self.table.get(symbol) is not None

    def getAddress(self, symbol: str) -> int:
        return self.table.get(symbol)


if __name__ == '__main__':
    parse = Parser(sys.argv[1])
    parse.Pass1()
    parse.Pass2()
