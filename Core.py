# Core.py<--Chip8Emulator ;; Zedd Serjeant
"""
This is the core of the Chip-8 Emulation project. It contains all of the
processor stuff.
Websites with information on the chip-8 structure:
http://www.multigesture.net/articles/how-to-write-an-emulator-chip-8-interpreter/
http://www.multigesture.net/wp-content/uploads/mirror/goldroad/chip8.shtml
http://en.wikipedia.org/wiki/CHIP-8#
http://mattmik.com/chip8.html
http://devernay.free.fr/hacks/chip8/
http://s4.zetaboards.com/wow/topic/9663604/1/
http://stackoverflow.com/questions/6619882/decoding-and-matching-chip-8-opcodes-in-c-c
"""

from random import randint
import pygame
from pygame.locals import *

DEBUGGING = 1
def DEBUG(string):
    "Print Verbose data for debugging. Disable with DEBUGGING flag."
    if DEBUGGING:
        print(string)

class CPU():
    #There are 2 versions of opcode 8XY6 and 8XYE. Set this flag
    # for the legacy version
    legacy = 0
    instructions_executed = 0 #Timer counts down every 14 instructions
    #The variables that will be used
    opcode = 0x0000
    memory = bytearray(4095)
    #Graphics
    graphics = [[0]*64 for i in range(32)] #64x32 pixels, for graphics.
    draw_graphics = 0
    V = bytearray(16) #Registers V0..VF
    #Index and preogram counter. Both store 0x000..0xFFF
    I = 0x000
    PC = 0x200
    #Timers
    delay_timer = 0
    sound_timer = 0
    #Stack
    stack = []
    #Key States
    key_states = [0]*16
    key_pressed = 0 #Set to a key if a key has been pressed this cycle
    #The FontSet. Has a sprite for every HEX character
    font_set = [
        0xF0, 0x90, 0x90, 0x90, 0xF0, #0
        0x20, 0x60, 0x20, 0x20, 0x70, #1
        0xF0, 0x10, 0xF0, 0x80, 0xF0, #2
        0xF0, 0x10, 0xF0, 0x10, 0xF0, #3
        0x90, 0x90, 0xF0, 0x10, 0x10, #4
        0xF0, 0x80, 0xF0, 0x10, 0xF0, #5
        0xF0, 0x80, 0xF0, 0x90, 0xF0, #6
        0xF0, 0x10, 0x20, 0x40, 0x40, #7
        0xF0, 0x90, 0xF0, 0x90, 0xF0, #8
        0xF0, 0x90, 0xF0, 0x10, 0xF0, #9
        0xF0, 0x90, 0xF0, 0x90, 0x90, #A
        0xE0, 0x90, 0xE0, 0x90, 0xE0, #B
        0xF0, 0x80, 0x80, 0x80, 0xF0, #C
        0xE0, 0x90, 0x90, 0x90, 0xE0, #D
        0xF0, 0x80, 0xF0, 0x80, 0xF0, #E
        0xF0, 0x80, 0xF0, 0x80, 0x80] #F

    def initialize(self):
        #Load Fontset
        for i in range(0x00, 0x4F):
            self.memory[i] = self.font_set[i]

    def loadFile(self, name):
        file = open(name, "rb", buffering=0)
        data = file.readall()
        self.memory[0x200:len(data)+0x200] = data

    def emulateCycle(self):
        #Fetch opcode
        self.draw_graphics = 0
        opcode = self.memory[self.PC] << 8 | self.memory[self.PC+1]
        nibb1 = (opcode & 0xF000) >> 12 #First 4 bits of opcode
        nibb2 = X = (opcode & 0x0F00) >> 8 #For VX
        nibb3 = Y = (opcode & 0x00F0) >> 4 #For VY
        nibb4 = N = (opcode & 0x000F)
        NNN = (opcode & 0x0FFF)
        NN = (opcode & 0x00FF)
        VX = self.V[nibb2]
        VY = self.V[nibb3]
        #Notes:
        #NI = Next Instruction
        #LSB = Least Significant Bit
        #MSB = Most Significan Bit
        if nibb1 == 0x0:
            if opcode == 0x0000:
                DEBUG("NULL")
                self.PC += 2
            elif nibb2 > 0x0: #0NNN: Execute System Code. Not used
                DEBUG("The confusing opcode was executed")
                self.PC += 2
            elif nibb4 == 0x0: #00E0: Clear the screen
                DEBUG("ClearScreen") ##Debug
                self.graphics = [[0]*64 for i in range(32)]
                self.draw_screen = 1
                self.PC += 2
            elif nibb4 == 0xE: #00EE: Return from subroutine
                DEBUG("Return from subroutine") ##Debug
                try:
                    self.PC = self.stack.pop()
                except IndexError:
                    DEBUG("ERROR: Attempt to return from subroutine when no \
                            call was made.")
                    return "Exit"
            else: DEBUG("unknown opcode")
        elif nibb1 == 0x1: #1NNN: Jumps to NNN
            DEBUG("Jump to {0}".format(NNN)) ##Debug
            self.PC = NNN
        elif nibb1 == 0x2: #2NNN: call subroutine at NNN
            DEBUG("Call {0}".format(hex(NNN))) ##Debug
            self.stack.append(self.PC + 2)
            self.PC = NNN
        elif nibb1 == 0x3: #3XNN: skip NI if VX == NN
            DEBUG("Skip NI if V{0} == {1}".format(hex(X),hex(NN))) ##Debug
            if VX == NN: self.PC += 4 #skip
            else: self.PC += 2
        elif nibb1 == 0x4: #4XNN: skip NI if VX != NN
            DEBUG("Skip NI if V{0} != {1}".format(hex(X),hex(NN))) ##Debug
            if VX != NN: self.PC += 4 #skip
            else: self.PC += 2
        elif nibb1 == 0x5: #5XY0: skip NI if VX == VY
            DEBUG("Skip NI if V{0}[{1}] == V{2}[{3}]".format(hex(X),hex(VX),hex(Y),hex(VY)))
            if VX == VY: self.PC += 4 #skip
            else: self.PC += 2
        elif nibb1 == 0x6: #6XNN: set VX to NN
            DEBUG("Set V{0} to {1}".format(hex(X), hex(NN))) ##Debug
            self.V[X] = NN
            self.PC += 2
        elif nibb1 == 0x7: #7XNN: Adds NN to VX
            DEBUG("Add {0} to V{1}".format(hex(NN), hex(X))) ##Debug
            if VX + NN > 0xFF:
                self.V[X] = NN - (0xFF - VX) #Carry. No flag is set
            else:
                self.V[X] += NN
            self.PC += 2
        elif nibb1 == 0x8:
            if nibb4 == 0x0: #8XY0: sets VX to VY
                DEBUG("Set V{0} to V{1}[{2}]".format(hex(X),hex(Y),hex(VY))) ##Debug
                self.V[X] = VY
                self.PC += 2
            elif nibb4 == 0x1: #8XY1: set VX to (VX or VY)
                DEBUG("Set V{0} to (V{0}[{1}] or V{2}[{3}])".format(hex(X),hex(VX),hex(Y),hex(VY))) ##Debug
                self.V[X] = VX | VY
                self.PC += 2
            elif nibb4 == 0x2: #8XY2: set VX to (VX and VY)
                DEBUG("Set V{0} to (V{0}[{1}] and V{2}[{3}])".format(hex(X),hex(VX),hex(Y),hex(VY))) ##Debug
                self.V[X] = VX & VY
                self.PC += 2
            elif nibb4 == 0x3: #8XY3: set VX to (VX xor VY)
                DEBUG("Set V{0} to (V{0}[{1}] xor V{2}[{3}])".format(hex(X),hex(VX),hex(Y),hex(VY))) ##Debug
                self.V[X] = VX ^ VY
                self.PC += 2
            elif nibb4 == 0x4: #8XY4: add VY to VX. Sets VF for carry
                DEBUG("Add V{0}[{1}] to V{2}[{3}]".format(hex(Y),hex(VY),hex(X),hex(VX))) ##Debug
                total = VX + VY
                if total > 255:
                    self.V[0xF] = 1 # carry
                    total -= 255
                else: self.V[0xF] = 0
                self.V[X] = total
                self.PC += 2
            elif nibb4 == 0x5: #8XY5: minus VY from VX. Unsets VF when borrow
                DEBUG("Minus V{0}[{1}] from V{2}[{3}]".format(hex(Y),hex(VY),hex(X),hex(VX))) ##Debug
                #This code may be wrong, but most likely isn't
                total = VX - VY
                if total < 0:
                    self.V[0xF] = 0 #borrow
                    total += 255
                else: self.V[0xF] = 1
                self.V[X] = total
                self.PC += 2
            elif nibb4 == 0x6: #8XY6: ...
                #Legacy: VF = LSB of VY. VX = (VY >> 1)
                #Modern: VF = LSB of VX. VX = (VX >> 1)
                #Set the legacy flag for the legacy version
                if self.legacy:
                    DEBUG("Shift V{0} to the right. Store in V{1}".format(hex(Y),hex(X)))
                    self.V[0xF] = int(bin(VY)[-1]) #getting LSB. Tricky in Python.
                    self.V[X] = VY >> 1
                else: #Use the modern version
                    DEBUG("Shift V{0} to the right. Store in V{0}".format(hex(X)))
                    self.V[0xF] = int(bin(VX)[-1])
                    self.V[X] >>= 1
                self.PC += 2
            elif nibb4 == 0x7: #8XY7: VX = (VY-VX). VF = 0 when borrow
                #This code may be wrong, but likely isn't
                DEBUG("V{0} = V{1}[{2}] - V{0}[{3}]".format(hex(X),hex(Y),hex(VY),hex(VX)))
                total = VY - VX
                if total < 0:
                    self.V[0xF] = 0 #borrow
                    total += 255
                else: self.V[0xF] = 1
                self.V[X] = total
                self.PC += 2
            elif nibb4 == 0xE: #8XYE: ...
                #Legacy: VF = MSB of VY. VX = (VY << 1)
                #Modern: VF = MSB of VX. VX = (VX << 1)
                #Set the legacy flag for the legacy version
                if self.legacy:
                    DEBUG("Shift V{0} to the left. Store in V{1}".format(hex(Y),hex(X)))
                    self.V[0xF] = int(bin(VY)[0])
                    self.V[X] = VY << 1
                else: #Modern version
                    DEBUG("Shift V{0} to the left. Store in V{0}".format(hex(X)))
                    self.V[0xF] = int(bin(VX)[0])
                    self.V[X] <<= 1
                self.PC += 2
            else:
                DEBUG("unknown Opcode")
                self.PC += 2
        elif nibb1 == 0x9: #9XY0: Skips NI if VX != VY
            DEBUG("Skip NI if V{0}[{1}] != V{2}[{3}]".format(hex(X),hex(VX),hex(Y),hex(VY)))
            if VX != VY: self.PC += 4 #skip
            else: self.PC += 2
        elif nibb1 == 0xA: #ANNN: Sets I to address NNN
            DEBUG("Set I to {0}".format(hex(NNN))) ##Debug
            self.I = NNN
            self.PC += 2
        elif nibb1 == 0xB: #BNNN: Jumps to NNN plus V0
            DEBUG("Jump to {0} plus V0[{1}]".format(hex(NNN),hex(self.V[0x0])))
            address = NNN + self.V[0x0]
            if address > 0xFFF: address -= 0xFFF
            self.PC = address
        elif nibb1 == 0xC: #CXNN: VX = (RandomNumber & NN)
            DEBUG("Set V{0} to RandNumber masked by {1}".format(hex(X),hex(NN)))
            r = randint(0x00, 0xFF) & NN
            self.V[X] = r
            self.PC += 2
        elif nibb1 == 0xD: #DXYN: Draw sprite data at (VX,VY) starting from I
            DEBUG("Draw sprite at V{0}[{3}], V{1}[{4}] :: {2} rows high".format(hex(X),hex(Y),N,VX,VY)) ##Debug
            self.V[0xF] = 0
            for yline in range(N): #N is the height
                pixel = self.memory[self.I + yline]
                for xline in range(8):
                    if pixel & (0x80 >> xline) != 0:
                        try:
                            if self.graphics[VY+yline][VX+xline] == 1:
                                self.V[0xF] = 1
                        except IndexError:
                            continue
                        self.graphics[VY+yline][VX+xline] ^= 1
            self.draw_graphics = 1
            self.PC += 2
            #Old Code:
            """
            self.V[0xF] = 0
            for yline in range(N): #N is height
                pixel_string = bin(self.memory[self.I + yline])[2:] #string of bits
                xline = 0
                for bit in pixel_string:
                    if int(bit):
                        if self.graphics[VY+yline][VX+xline]:
                            self.V[0xF] = 1 #collision
                        self.graphics[VY+yline][VX+xline] ^= int(bit)
                    xline += 1
            self.draw_graphics = 1
            self.PC += 2
            """
        elif nibb1 == 0xE:
            if NN == 0x9E: #EX9E: Skip NI if key stored in VX is pressed
                DEBUG("Skip NI if key V{0}[{1}] is pressed - {2}".format(hex(X),hex(VX),self.key_states[VX]))
                if self.key_states[VX]:
                    self.PC += 4
                else:
                    self.PC += 2
            elif NN == 0xA1: #EXA1: Skip NI if key stored in VX is not pressed
                DEBUG("Skip NI if key V{0}[{1}] is not pressed - {2}".format(hex(X),hex(VX),self.key_states[VX]))
                if not self.key_states[VX]:
                    self.PC += 4
                else:
                    self.PC += 2
            else:
                DEBUG("Opcode Unknown")
                self.PC += 2
        elif nibb1 == 0xF:
            if NN == 0x07: #FX07: Store DelayTimer in VX
                DEBUG("Store DelayTimer[{0}] in V{1}".format(self.delay_timer,hex(X))) ##Debug
                self.V[X] = self.delay_timer
                self.PC += 2
            elif NN == 0x0A: #FX0A: Await keypress, then store result in VX
                #Possibly buggy. Reacts if key has been pressed the same
                # cycle as this instruction. Maybe it should react to keypresses
                # after the cycle this runs.
                DEBUG("Await Keypress")
                if self.key_pressed:
                    self.V[X] = self.key_pressed
                    self.PC += 2
                #Execution is halted until keypress, so nothing else happens.                    
            elif NN == 0x15: #FX15: Set DelayTimer to VX
                DEBUG("Set Delay Timer to V{0}[{1}]".format(hex(X),hex(VX))) ##Debug
                self.delay_timer = VX
                self.PC += 2
            elif NN == 0x18: #FX18: Set SoundTimer to VX
                DEBUG("Set Sound Timer to V{0}[{1}]".format(hex(X),hex(VX))) ##Debug
                self.sound_timer = VX
                self.PC += 2
            elif NN == 0x1E: #FX1E: I += VX
                DEBUG("I += V{0}[{1}]".format(hex(X),hex(VX)))
                if self.I + VX > 0xFFF:
                    self.I = (VX - (0xFFF - self.I)) #rollover
                    self.V[0xF] = 1 #set the carry flag
                else:
                    self.I += VX
                self.PC += 2
            elif NN == 0x29: #FX29: Set I to fontset data at VX
                DEBUG("Set I to sprite V{0}[{1}]".format(hex(X),hex(VX))) ##Debug
                self.I = VX * 5
                self.PC += 2
            elif NN == 0x33: #FX33: Stores VX at [I,I+1,I+2] as BCD
                DEBUG("Store BCD of V{0}[{1}][{2}]".format(hex(X),hex(VX),VX)) ##Debug
                data = str(VX)
                if len(data) == 1:
                    data = "00"+data
                elif len(data) == 2:
                    data = "0"+data
                self.memory[self.I]     = int(data[0])
                self.memory[self.I + 1] = int(data[1])
                self.memory[self.I + 2] = int(data[2])
                DEBUG(str(self.memory[self.I]) +" :: "+ str(self.memory[self.I + 1]) +" :: "+ str(self.memory[self.I + 2]))
                self.PC += 2;
            elif NN == 0x55: #FX55: Stores V0-VX in memory starting with I. I += (X + 1)
                DEBUG("Write {0} to disk".format("V{0}[{1}]".format(hex(i),hex(self.V[i])) for i in range(X))) ##Debug
                for i in range(X+1):
                    self.memory[self.I + i] = self.V[i]
                self.I = self.I+X+1
                self.PC += 2
            elif NN == 0x65: #FX65: Fills V0-VX from memory stating with I. I += (X + 1)
                DEBUG("Read {0} data from disk".format(hex(X)))
                DEBUG(str(self.memory[self.I]) +" :: "+ str(self.memory[self.I + 1]) +" :: "+ str(self.memory[self.I + 2]))
                for i in range(X+1):
                    self.V[i] = self.memory[self.I + i]
                self.I = self.I+X+1
                self.PC += 2
            else:
                DEBUG("Opcode Unknown")
                self.PC += 2
        else:
            DEBUG("Unknown opcode :: {0}".format(opcode))
            self.PC += 2

        #Timers
        if self.delay_timer > 0:
            if self.instructions_executed == 0:
                self.delay_timer -= 1
        if self.sound_timer > 0:
            print("BEEP!")
            if self.instructions_executed == 0:
                self.sound_timer -= 1
        #key_pressed flag is reset
        self.key_pressed = 0
        #Count amount of instructions executed
        self.instructions_executed += 1
        if self.instructions_executed == 14:
            self.instructions_executed = 0

def main(name):
    #Initialize pygame
    pygame.init()
    #64x32 resolution. Each CHIP-8 pixel is a 10x10 PC pixel
    screen = pygame.display.set_mode((640, 320))
    pygame.display.set_caption(name)
    clock = pygame.time.Clock()
    #Initalize CHIP-8
    chip8 = CPU()
    chip8.initialize()
    chip8.loadFile(name)
    while 1:
        for event in pygame.event.get():
            if event.type == KEYDOWN:
                if event.key == K_1: #Key 1
                    chip8.key_states[0x1] = 1
                    chip8.key_pressed = 0x1
                elif event.key == K_2: #Key 2
                    chip8.key_states[0x2] = 1
                    chip8.key_pressed = 0x2
                elif event.key == K_3: #Key 3
                    chip8.key_states[0x3] = 1
                    chip8.key_pressed = 0x3
                elif event.key == K_4: #Key C
                    chip8.key_states[0xC] = 1
                    chip8.key_pressed = 0xC
                elif event.key == K_q: #Key 4
                    chip8.key_states[0x4] = 1
                    chip8.key_pressed = 0x4
                elif event.key == K_w: #Key 5
                    chip8.key_states[0x5] = 1
                    chip8.key_pressed = 0x5
                elif event.key == K_e: #Key 6
                    chip8.key_states[0x6] = 1
                    chip8.key_pressed = 0x6
                elif event.key == K_r: #Key D
                    chip8.key_states[0xD] = 1
                    chip8.key_pressed = 0xD
                elif event.key == K_a: #Key 7
                    chip8.key_states[0x7] = 1
                    chip8.key_pressed = 0x7
                elif event.key == K_s: #Key 8
                    chip8.key_states[0x8] = 1
                    chip8.key_pressed = 0x8
                elif event.key == K_d: #Key 9
                    chip8.key_states[0x9] = 1
                    chip8.key_pressed = 0x9
                elif event.key == K_f: #Key E
                    chip8.key_states[0xE] = 1
                    chip8.key_pressed = 0xE
                elif event.key == K_z: #Key A
                    chip8.key_states[0xA] = 1
                    chip8.key_pressed = 0xA
                elif event.key == K_x: #Key 0
                    chip8.key_states[0x0] = 1
                    chip8.key_pressed = 0x0
                elif event.key == K_c: #Key B
                    chip8.key_states[0xB] = 1
                    chip8.key_pressed = 0xB
                elif event.key == K_v: #Key F
                    chip8.key_states[0xF] = 1
                    chip8.key_pressed = 0xF
            elif event.type == KEYUP:
                if event.key == K_1: #Key 1
                    chip8.key_states[0x1] = 0
                elif event.key == K_2: #Key 2
                    chip8.key_states[0x2] = 0
                elif event.key == K_3: #Key 3
                    chip8.key_states[0x3] = 0
                elif event.key == K_4: #Key C
                    chip8.key_states[0xC] = 0
                elif event.key == K_q: #Key 4
                    chip8.key_states[0x4] = 0
                elif event.key == K_w: #Key 5
                    chip8.key_states[0x5] = 0
                elif event.key == K_e: #Key 6
                    chip8.key_states[0x6] = 0
                elif event.key == K_r: #Key D
                    chip8.key_states[0xD] = 0
                elif event.key == K_a: #Key 7
                    chip8.key_states[0x7] = 0
                elif event.key == K_s: #Key 8
                    chip8.key_states[0x8] = 0
                elif event.key == K_d: #Key 9
                    chip8.key_states[0x9] = 0
                elif event.key == K_f: #Key E
                    chip8.key_states[0xE] = 0
                elif event.key == K_z: #Key A
                    chip8.key_states[0xA] = 0
                elif event.key == K_x: #Key 0
                    chip8.key_states[0x0] = 0
                elif event.key == K_c: #Key B
                    chip8.key_states[0xB] = 0
                elif event.key == K_v: #Key F
                    chip8.key_states[0xF] = 0
            elif event.type == pygame.QUIT:
                pygame.quit()
                return
        if chip8.draw_graphics:
            #Draw the graphics array
            #DEBUG(chip8.graphics)
            screen.fill((0,0,0))
            for y in range(32):
                for x in range(64):
                    if chip8.graphics[y][x]:
                        screen.fill((255, 255, 255), rect=(x*10, y*10, 10, 10))
            pygame.display.flip()
        state = chip8.emulateCycle()
        if state == "Exit":
            return
        clock.tick(840) #currently clocked at 100%
        
main("clock.ch8")
    
        
