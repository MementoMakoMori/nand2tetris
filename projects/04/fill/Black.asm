(RESET)
	@16384
	D=A
	@screen
	M=D
(DARK)
	D=-1
	@screen
	A=M
	M=D
	@screen
	M=M+1
	@24576
	D=M
	@RESET
	D;JNE
	@DARK
	0;JMP
