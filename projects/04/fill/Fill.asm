// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Fill.asm

// Runs an infinite loop that listens to the keyboard input.
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel;
// the screen should remain fully black as long as the key is pressed. 
// When no key is pressed, the program clears the screen, i.e. writes
// "white" in every pixel;
// the screen should remain fully clear as long as no key is pressed.
(RESET)
	@16384
	D=A
	@screen //pointer toward screen word to draw on
	M=D
	@24576 //check for keyboard input
	D=M
	@DARK
	D;JNE
(LIGHT)
	@screen 
	A=M //load pointer to A
	M=0 //paint location white
	@screen
	M=M+1 //increment screen word
	D=M
	@24576 
	D=D-A //check that screen is within bounds, reset if not
	@RESET
	D;JEQ
	@24576 //check for keyboard input, reset if yes
	D=M
	@RESET 
	D;JNE
	@LIGHT
	0;JMP
(DARK)
	@screen
	A=M
	M=-1
	@screen
	M=M+1
	D=M
	@24576
	D=D-A
	@RESET
	D;JEQ
	@24576
	D=M
	@RESET
	D;JEQ
	@DARK
	0;JMP
