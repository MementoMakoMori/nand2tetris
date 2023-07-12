// push constant 7
@7
D=A     // hold value  in D
@SP
A=M     // go to stack pointer address in RAM[0]
M=D     // set RAM[SP] = 7
@SP
M=M+1    // RAM[0] ++

// push constant 8
@8
D=A
@SP
A=M
M=D
@SP
M=M+1

// add
@SP
M=M-1   // decrement stack pointer
A=M
D=M     // hold top stack value in D
@SP
M=M-1   // decrement stack pointer
A=M     // go to top of stack
M=D+M   // add value with that held in D
