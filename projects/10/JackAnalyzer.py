

class JackTokenizer():

    def __init__(self, file):
        self.input = open(file, 'r')
        self.current = None


    def advance(self):
        self.current = self.input.readline()
        while self.current and (self.current[0] == "/" or self.current[0] == "\n"):
            self.current = self.input.readline()
        self.current = self.current.split("//")[0]
        self.current = self.current.strip()