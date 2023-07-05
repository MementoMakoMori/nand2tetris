// RAM[0]/SP = 256
// RAM[1]/LCL = 300

// push constant 10
@10
D=A
@SP      // RAM[SP] = 10
A=M
M=D
@SP
M=M+1    // RAM[0] ++

// pop local 0
@0
D=A     // hold offset in D
@LCL
D=D+M
@R13
M=D     // RAM[13] = LCL + OFFSET
@SP     // RAM[0] = 257
M=M-1   // RAM[0] = 256
A=M
D=M
@R13
A=M
M=D

// push constant 7
@7
D=A
@SP      // RAM[SP] = 7
A=M
M=D
@SP
M=M+1    // RAM[0] ++

// pop local 1
@1
D=A
@LCL
D=D+M
@R13
M=D     // RAM[13] = LCL + OFFSET
@SP     // RAM[0] = 257
M=M-1   // RAM[0] = 256
A=M
D=M
@R13
A=M
M=D

// push local 1     // value 7 from local 1 to stack SP
@1
D=A
@LCL
A=D+M
D=M
@SP
A=M
M=D  // RAM[SP] = RAM[LCL+OFFSET]
@SP
M=M+1

// push local 0     // value 10 from local 0 to stack SP
@0
D=A
@LCL
A=D+M
D=M
@SP
A=M
M=D     // RAM[SP] = MEM[LCL+OFFSET]
@SP
M=M+1
