

class VMWriter:
    def __init__(self, file):
        self.output = open(f"{file.split('.jack')[0]}.vm", 'w')
        self.math = {'+': 'add', '-': 'sub', '&': 'and', '|': 'or', '>': 'gt', '<': 'lt', '=': 'eq', '~': 'not'}

    def writePush(self, segment: str, index: int):
        segment = 'local' if segment == "var" else segment
        self.output.write(" ".join(["push", segment, str(index)+"\n"]))

    def writePop(self, segment: str, index: int):
        segment = 'local' if segment == "var" else segment
        self.output.write(" ".join(["pop", segment, str(index)+"\n"]))

    def writeArithmetic(self, command: str):
        command = self.math[command] if len(command) == 1 else command
        self.output.write(command+"\n")

    def writeLabel(self, label: str):
        self.output.write("label " + label + "\n")

    def writeGoto(self, label: str):
        self.output.write("goto " + label + "\n")

    def writeIf(self, label: str):
        self.output.write("if-goto " + label + "\n")

    def writeCall(self, name: str, nArgs: int):
        self.output.write(" ".join(["call", name, str(nArgs)+"\n"]))

    def writeFunction(self, name: str, nLocals: int):
        self.output.write(" ".join(["function", name, str(nLocals) + "\n"]))

    def writeReturn(self):
        self.output.write("return\n")

    def closeOutput(self):
        self.output.close()

    def comment(self, text: str):
        self.output.write(text+"\n")
