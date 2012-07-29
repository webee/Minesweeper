import os
os.environ['SDL_VIDEO_WINDOW_POS'] = '%d,%d'%(150,35)

import time
import pygame
from pygame.locals import *
import random
import grid


def load_sound(name):
    class NoneSound:
        def play(self): pass
    if not pygame.mixer:
        return NoneSound()
    fullname = os.path.join('sound', name)
    sound = pygame.mixer.Sound(fullname)
    return sound

def random_color():
    return (random.randint(0,255), random.randint(0,255), random.randint(0,255))

def get_commons(x,y):
    xset = set(x)
    yset = set(y)
    cset = xset.intersection(yset)
    return list(cset)

class Difficulty:
    def __init__(self, name, width, height, mines, cellsize):
        self.name = name
        self.width = width
        self.height = height
        self.mines = mines
        self.cell_size = cellsize

class Box:
    def __init__(self):
        self.pos = (0,0)
        self.ismine = False
        # 0:unflag, 1:flag, 2:not sure, 3:when game over, mines not flaged.
        self.flag_stat = 0
        self.is_open = False
        self.flagged = 0
        self.number = 0
        
        self.arounds = []
        self.arounds2 = []

    # utils
    def not_full(self):
        return self.is_open and self.flagged < self.number

    def is_full(self):
        return self.is_open and self.flagged == self.number

    def count_blanks(self, boxes):
        blanks = []
        for box in boxes:
            if not box.is_open and box.flag_stat == 0:
                blanks.append(box)
        return blanks

    def get_blanks(self):
        return self.count_blanks(self.arounds)

    def common_arounds(self, box):
        return get_commons(self.arounds, box.arounds)

    # functions
    def flag(self):
        add = 0
        if not self.is_open:
            if self.flag_stat == 1:
                self.flag_stat = 2
                add = -1
            elif self.flag_stat == 2:
                self.flag_stat = 0
            else:
                self.flag_stat = 1
                add = 1
            if add:
                for box in self.arounds:
                    if not box.ismine:
                        box.flagged += add
        return add

    def reveal(self):
        if not self.is_open and self.flag_stat == 0:
            if not self.ismine:
                self.is_open = True
            else:
                return -1
        else:
            return 0
        
        multi = 1
        if self.number == 0:
            for box in self.arounds:
                if not box.ismine:
                    multi += box.reveal()
        return multi+1

class Mines:
    def __init__(self):
        self.difficulty = 2
        self.difficulties = []
        self.difficulties.append(Difficulty("Easy"  ,  9,  9, 10, 35))
        self.difficulties.append(Difficulty("Medium", 16, 16, 40, 25))
        self.difficulties.append(Difficulty("Expert", 30, 16, 99, 25))
        self.difficulties.append(Difficulty("More Expert", 40, 25, 200, 20))
        self.difficulties.append(Difficulty("Narrow", 30, 5, 28, 20))
        self.difficulties.append(Difficulty("More Narrow", 40, 4, 35, 18))
        self.difficulties.append(Difficulty("Ridiculous", 50, 30, 320, 18))

        self.stepx=0
        self.stepy=0

        self.SW = 920
        self.SH = 690

        self.w = self.difficulties[self.difficulty].width
        self.h = self.difficulties[self.difficulty].height
        self.cell_size = self.difficulties[self.difficulty].cell_size
        self.mines = self.difficulties[self.difficulty].mines
        self.flagged = 0

        self.grid = grid.Grid(self.w,self.h,Box())

        self.xoff = (self.SW/2)-(self.cell_size*self.w/2)
        self.yoff = (self.SH/2)-(self.cell_size*self.h/2)+10

        self.gameover = False
        self.win = False
        self.started = False
        self.time_start = 0
        self.time_spend = 0

        self.small_font = pygame.font.Font(pygame.font.get_default_font(),12)
        self.medium_font = pygame.font.Font(pygame.font.get_default_font(),18)
        self.large_font = pygame.font.Font(pygame.font.get_default_font(),24)

        self.background = pygame.Surface((self.SW,self.SH))
        self.load_colors()
        self.color_schema=0

        self.sound_boom = load_sound('boomboomuhoh.wav')
        self.sound_boop = load_sound('boop.wav')
        self.sound_beeh = load_sound('beeh.wav')
        self.sound_wsh = load_sound('wsh.wav')
        self.sound_yes = load_sound('yes.wav')
        self.sound_lose = load_sound('ms_lose.wav')
        self.sound_single = load_sound('ms_single.wav')
        self.sound_multi = load_sound('ms_multi.wav')
        self.sound_win = load_sound('ms_win.wav')

        self.screen = pygame.display.set_mode((self.SW, self.SH))
        pygame.display.set_caption('Mines - ' + self.difficulties[self.difficulty].name)


    def update_bg(self):
        self.background.fill((222,222,0))
        self.background.fill(self.colors_bg[0])
        for x in range(int(self.SW/16)):
            for y in range(int(self.SH/12)):
                USW = int(self.SW/16)
                USH = int(self.SH/12)
                SW = int(x*(self.SW/16))
                SH = int(y*(self.SH/12))
                if (x+y)%2:
                    pygame.draw.rect(self.background, self.colors_bg[1], (SW+1, SH+1, USW-2, USH-2))
                else:
                    pygame.draw.rect(self.background, self.colors_bg[2], (SW+1, SH+1, USW-2, USH-2))

    def __check_pos(self, x, y):
        return x>=0 and x<self.w and y>=0 and y<self.h

    def check_win(self):
        self.win = True
        for x in range(self.w):
            for y in range(self.h):
                if not (self.grid.v[x][y].ismine and self.grid.v[x][y].flag_stat == 1):
                    if not (not self.grid.v[x][y].ismine and self.grid.v[x][y].flag_stat != 1):
                        self.win = False
                        break
        if not self.win:
            self.win = True
            for x in range(self.w):
                for y in range(self.h):
                    if not self.grid.v[x][y].ismine and not self.grid.v[x][y].is_open:
                        self.win = False
                        break
        if self.win:
            self.gameover = True
            time.sleep(0.5)
            self.sound_win.play()
                    
    def reveal(self, pos, silent=False):
        x,y = pos
        multi = self.grid.v[x][y].reveal()
        if multi > 1:
            self.sound_multi.play()
        elif multi == 1:
            self.sound_single.play()
        elif multi < 0:
            for x in range(self.w):
                for y in range(self.h):
                    if self.grid.v[x][y].ismine and self.grid.v[x][y].flag_stat != 1:
                        # mines not flaged.
                        self.grid.v[x][y].flag_stat = 3
                        if (x+y)%3:
                            self.draw()
                        if (x+y)%7:
                            self.sound_lose.play()
            self.gameover = True
            return multi
        
        if multi and not silent:
            self.check_win()
        return multi

    def flag(self, pos, silent=False):
        x,y = pos
        ret = self.grid.v[x][y].flag()
        self.flagged += ret
        if ret and not silent:
            self.check_win()
        return ret

    # all auto function must use Mine::flag and Mine:reveal
    # must not refer box.ismine!!!
    # we are not cheating!!!
    def __do_auto_flag(self, pos):
        changes = 0
        x,y=pos
        this_box = self.grid.v[x][y]
        flag_box = []
        for box in this_box.arounds:
            if not box.is_open:
                flag_box.append(box)
        if len(flag_box) == this_box.number:
            for box in flag_box:
                if box.flag_stat == 0:
                    changes += self.flag(box.pos, silent=True)
        return changes
            
    def auto_flag(self):
        changes = 0
        for x in range(self.w):
            for y in range(self.h):
                box = self.grid.v[x][y]
                if box.is_open and box.flagged < box.number:
                    changes += self.__do_auto_flag((x,y))
        if changes:
            self.check_win()
        return changes

    def __do_auto_open(self, pos):
        changes = 0
        x,y=pos
        this_box = self.grid.v[x][y]
        open_box = []
        for box in this_box.arounds:
            if not box.is_open and box.flag_stat == 0:
                changes += self.reveal(box.pos, silent=True)
        return changes

    def auto_open(self):
        changes = 0
        for x in range(self.w):
            for y in range(self.h):
                box = self.grid.v[x][y]
                if box.is_full():
                    changes += self.__do_auto_open((x,y))
        if changes:
            self.check_win()
            self.auto_open()
        return 0

    def __do_anlysis(self, xbox, ybox, silent=True):
        changes = 0
        xblanks = xbox.get_blanks()
        yblanks = ybox.get_blanks()
        cblanks = get_commons(xblanks, yblanks)

        if len(cblanks) == 0:
            return 0

        # flagged + blanks >= number, so min_x_c always < cblanks
        xfree = xbox.number - xbox.flagged
        xother = len(xblanks) - len(cblanks)
        min_x_c = xfree - xother
        yfree = ybox.number - ybox.flagged
        yother = len(yblanks) - len(cblanks)
        min_y_c = yfree - yother
        #max_y_c = yfree > len(cblanks) and len(cblanks) or yfree

        # two categories.
        if len(yblanks) - len(cblanks) > 0:
            if min_x_c == yfree:
                if not silent:
                    print "xbox:%s,ybox:%s,mx:%i, yf:%i"%(xbox.pos, ybox.pos, min_x_c, yfree)
                for box in yblanks:
                    if box not in cblanks:
                        changes += self.reveal(box.pos, silent=True)

            if len(xblanks) == len(cblanks) and min_x_c + yother == yfree:
                if not silent:
                    print "xbox:%s,ybox:%s,mx:%i, yf:%i"%(xbox.pos, ybox.pos, min_x_c, yfree)
                for box in yblanks:
                    if box not in cblanks:
                        changes += self.flag(box.pos, silent=True)

        if len(xblanks) - len(cblanks) > 0:
            if min_y_c == xfree:
                if not silent:
                    print "xbox:%s,ybox:%s,xf:%i, my:%i"%(xbox.pos, ybox.pos, xfree, min_y_c)
                for box in xblanks:
                    if box not in cblanks:
                        changes += self.reveal(box.pos, silent=True)

            if len(yblanks) == len(cblanks) and min_y_c + xother == xfree:
                if not silent:
                    print "xbox:%s,ybox:%s,xf:%i, my:%i"%(xbox.pos, ybox.pos, xfree, min_y_c)
                for box in xblanks:
                    if box not in cblanks:
                        changes += self.flag(box.pos, silent=True)
        return changes

    def __do_auto_anlysis(self, xbox, silent=True):
        changes = 0
        for ybox in xbox.arounds:
            if ybox.not_full():
                changes += self.__do_anlysis(xbox,ybox, silent)
        return changes

    def step_auto_anlysis(self,x=0,y=0):
        print "step into: ",x,y
        while x < self.w:
            while y < self.h:
                box = self.grid.v[x][y]
                if box.not_full():
                    if self.__do_auto_anlysis(box, silent=False):
                        return x,y+1
                y = y+1
            x = x+1
            y = 0
        return 0,0

    def auto_anlysis(self,x=None,y=None):
        changes = 0
        for x in range(self.w):
            for y in range(self.h):
                box = self.grid.v[x][y]
                if box.not_full():
                    changes += self.__do_auto_anlysis(box)
        return changes

    def __set_around(self, pos):
        count = 0
        x,y=pos
        arounds = [(x-1,y-1),(x,y-1),(x+1,y-1),(x-1,y),(x+1,y),(x-1,y+1),(x,y+1),(x+1,y+1)]
        arounds2 = [(x-2,y-2),(x-1,y-2),(x,y-2),(x+1,y-2),(x+2,y-2),
                (x-2,y-1),(x+2,y-1),
                (x-2,y),(x+2,y),
                (x-2,y+1),(x+2,y+1),
                (x-2,y+2),(x-1,y+2),(x,y+2),(x+1,y+2),(x+2,y+2)]
        box = self.grid.v[x][y]
        for i,j in arounds:
            if self.__check_pos(i,j):
                box.arounds.append(self.grid.v[i][j])
                if self.grid.v[i][j].ismine:
                    count += 1
        box.number = count

        for i,j in arounds2:
            if self.__check_pos(i,j):
                box.arounds2.append(self.grid.v[i][j])

    def set_mines(self, pos=None):
        for x in range(self.w):
            for y in range(self.h):
                self.grid.v[x][y].pos = (x,y)

        done = False
        minesset = 0
        
        # set mines
        while not done:
            x = random.randint(0,(self.w-1))
            y = random.randint(0,(self.h-1))
            if not self.grid.v[x][y].ismine and (x,y)!=pos:
                self.grid.v[x][y].ismine = True
                minesset += 1
            if minesset == self.mines:
                done = True
        # set arounds && number
        for x in range(self.w):
            for y in range(self.h):
                self.__set_around((x,y))

        if pos:
            self.reveal((pos))
        self.started = True
        self.time_start = time.time()

    def reset(self):
        self.win = False
        self.gameover = False
        self.started = False
        self.flagged = 0
        self.stepx=0
        self.stepy=0

        self.w = self.difficulties[self.difficulty].width
        self.h = self.difficulties[self.difficulty].height
        self.cell_size = self.difficulties[self.difficulty].cell_size
        self.mines = self.difficulties[self.difficulty].mines

        self.xoff = (self.SW/2)-(self.cell_size*self.w/2)
        self.yoff = (self.SH/2)-(self.cell_size*self.h/2)+10

        self.grid = grid.Grid(self.w,self.h,Box())
        pygame.display.set_caption('Mines - ' + self.difficulties[self.difficulty].name)


    def randomize_colors(self):
        self.colors_bg = list((random_color(), random_color(), random_color()))
        self.colors_text = random_color()
        self.colors_text_win = random_color()
        self.colors_text_lose = random_color()
        self.colors_flag = list((random_color(),random_color()))
        self.colors_flag2 = list((random_color(),random_color()))
        self.colors_unrevealed = random_color()
        self.colors_highlight = random_color()
        self.colors_notouch = random_color()
        self.colors_notouch_win = random_color()
        self.colors_revealed = random_color()
        self.colors_mine = random_color()
        self.colors_back = random_color()
        self.colors_back_win = random_color()
        self.colors_back_lose = random_color()
        self.colors_numbers = random_color()
        self.update_bg()
        

    def load_colors(self, fn = "default.color"):
        if os.path.exists(fn):
            fin = open(fn,"r")
            lines = fin.readlines()
            for line in lines:
                exec("self.colors_"+line)
            self.update_bg()
        else:
            print(fn + " does not exist.\n")

    def print_colors(self):
        print("bg = " + str(self.colors_bg))
        print("text = " + str(self.colors_text))
        print("text_win = " + str(self.colors_text_win))
        print("text_lose = " + str(self.colors_text_lose))
        print("flag = " + str(self.colors_flag))
        print("flag2 = " + str(self.colors_flag2))
        print("unrevealed = " + str(self.colors_unrevealed))
        print("highlight = " + str(self.colors_highlight))
        print("notouch = " + str(self.colors_notouch))
        print("notouch_win = " + str(self.colors_notouch_win))
        print("revealed = " + str(self.colors_revealed))
        print("mine = " + str(self.colors_mine))
        print("back = " + str(self.colors_back))
        print("back_win = " + str(self.colors_back_win))
        print("back_lose = " + str(self.colors_back_lose))
        print("numbers = " + str(self.colors_numbers))
        print("")
    
    def draw(self):
        self.screen.blit(self.background,(0,0))

        if self.win:
            pygame.draw.rect(self.screen, self.colors_back_win,(self.xoff-2, self.yoff-2, self.cell_size*self.w+4, self.cell_size*self.h+4))
        elif self.gameover:
            pygame.draw.rect(self.screen, self.colors_back_lose,(self.xoff-2, self.yoff-2, self.cell_size*self.w+4, self.cell_size*self.h+4))
        else:
            pygame.draw.rect(self.screen, self.colors_back,(self.xoff-2, self.yoff-2, self.cell_size*self.w+4, self.cell_size*self.h+4))

        for x in range(self.w):
            for y in range(self.h):
                box = self.grid.v[x][y]
                if box.is_open:
                    if box.number > 0:                            
                        pygame.draw.rect(self.screen, self.colors_revealed, (self.xoff+x*self.cell_size, self.yoff+y*self.cell_size, self.cell_size-1, self.cell_size-1))
                        self.screen.blit(self.small_font.render(str(box.number),True, self.colors_numbers),
                                         (self.xoff+x*self.cell_size+(self.cell_size/2)-(self.small_font.size(str(box.number))[0]/2)-1,
                                          self.yoff+y*self.cell_size+(self.cell_size/2)-(self.small_font.size(str(box.number))[1]/2)-1))
                    else:
                        if self.win:
                            pygame.draw.rect(self.screen, self.colors_notouch_win, (self.xoff+x*self.cell_size, self.yoff+y*self.cell_size, self.cell_size-1, self.cell_size-1))
                        else:
                            pygame.draw.rect(self.screen, self.colors_notouch, (self.xoff+x*self.cell_size, self.yoff+y*self.cell_size, self.cell_size-1, self.cell_size-1))
                else:
                    p = pygame.mouse.get_pos()
                    if (int((p[0] - self.xoff)/self.cell_size) == x) and (int((p[1] - self.yoff)/self.cell_size) == y):
                        pygame.draw.rect(self.screen, self.colors_highlight, (self.xoff+x*self.cell_size, self.yoff+y*self.cell_size, self.cell_size-1, self.cell_size-1))
                    else:
                        pygame.draw.rect(self.screen,self.colors_unrevealed, (self.xoff+x*self.cell_size, self.yoff+y*self.cell_size, self.cell_size-1, self.cell_size-1))
                    if box.ismine and self.gameover and not self.win:
                        pygame.draw.rect(self.screen, self.colors_mine, (self.xoff+x*self.cell_size, self.yoff+y*self.cell_size, self.cell_size-1, self.cell_size-1))
                    # mines not flaged
                    elif box.flag_stat == 3:
                        pygame.draw.rect(self.screen, self.colors_mine, (self.xoff+x*self.cell_size, self.yoff+y*self.cell_size, self.cell_size-1, self.cell_size-1))
                    if box.flag_stat == 1:
                        if not box.ismine and self.gameover:
                            pygame.draw.rect(self.screen, self.colors_numbers, (self.xoff+x*self.cell_size, self.yoff+y*self.cell_size, self.cell_size-1, self.cell_size-1))
                        else:
                            pygame.draw.rect(self.screen, self.colors_flag[0], (self.xoff+x*self.cell_size+4, self.yoff+y*self.cell_size+4, self.cell_size-1-8, self.cell_size-1-8))
                        pygame.draw.rect(self.screen, self.colors_flag[1], (self.xoff+x*self.cell_size+5, self.yoff+y*self.cell_size+5, self.cell_size-1-10, self.cell_size-1-10))
                    if box.flag_stat == 2:
                        pygame.draw.rect(self.screen, self.colors_flag2[0], (self.xoff+x*self.cell_size+4, self.yoff+y*self.cell_size+4, self.cell_size-1-8, self.cell_size-1-8))
                        pygame.draw.rect(self.screen, self.colors_flag2[1], (self.xoff+x*self.cell_size+5, self.yoff+y*self.cell_size+5, self.cell_size-1-10, self.cell_size-1-10))

        if self.gameover:
            if not self.win:
                self.screen.blit(self.medium_font.render("GAME OVER", True, self.colors_text_lose), ((self.SW/2)-(self.medium_font.size("GAME OVER")[0]/2),10))
            else:
                self.screen.blit(self.medium_font.render("YOU WIN!", True, self.colors_text_win), ((self.SW/2)-(self.medium_font.size("YOU WIN!")[0]/2),10))
        self.screen.blit(self.medium_font.render("Change Difficulty With n/p. Restart with r.",True, self.colors_text), (10,self.SH-25))
        
        pygame.draw.line(self.screen, self.colors_text, (10, 8+self.medium_font.size("Minesweeper")[1]), (10+self.medium_font.size("Minesweeper")[0], 8+self.medium_font.size("Minesweeper")[1]))
        self.screen.blit(self.medium_font.render("Minesweeper", True, self.colors_text), (10,10))
        self.screen.blit(self.medium_font.render("Difficulty: "+self.difficulties[self.difficulty].name, True, self.colors_text), (10,35))
        self.screen.blit(self.medium_font.render("Mines Left:"+str(self.mines-self.flagged), True, self.colors_text), (self.xoff, self.yoff - 25))
        if self.started:
            if not self.gameover:
                self.time_spend = time.time() - self.time_start
            self.screen.blit(self.medium_font.render("Times:"+str(int(self.time_spend)), True, self.colors_text), (self.xoff+400, self.yoff - 25))

        if pygame.mouse.get_pos()[0] >= self.SW-25 and pygame.mouse.get_pos()[1] <= 25:
            pygame.draw.rect(self.screen, self.colors_highlight, (self.SW-25,0,25,25))
        else:
            pygame.draw.rect(self.screen, self.colors_unrevealed, (self.SW-25,0,25,25))
        self.screen.blit(self.medium_font.render("R", True, (50,50,50)), (self.SW-18, 4))
        
        pygame.display.flip()

        
    def play(self):
        
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False
                elif event.type == MOUSEBUTTONDOWN:
                    if event.pos[0] >= self.SW-20 and event.pos[1] <= 20 or self.gameover:
                        self.reset()
                    elif event.pos[0] >= self.xoff and event.pos[0] < self.xoff+(self.cell_size*self.w):
                        if event.pos[1] >= self.yoff and event.pos[1] < self.yoff+(self.cell_size*self.h):
                            x = int((event.pos[0]-self.xoff)/self.cell_size)
                            y = int((event.pos[1]-self.yoff)/self.cell_size)
                            if event.button == 1:
                                if not self.started:
                                    self.set_mines((x,y))
                                else:
                                    self.reveal((x, y))
                            elif event.button == 3:
                                self.flag(x, y)
                elif event.type == KEYDOWN:
                    if event.key == K_f:
                        self.auto_flag()
                    if event.key == K_g:
                        self.auto_open()
                    if event.key == K_d:
                        #self.auto_anlysis()
                        self.stepx,self.stepy=self.step_auto_anlysis(self.stepx,self.stepy)
                    if event.key == K_j:
                        while self.auto_anlysis():
                            pass
                    if event.key == K_k:
                        self.auto_open()
                        while self.auto_flag():
                            self.auto_open()
                    if event.key == K_s:
                        schemas = os.listdir("color")
                        self.color_schema = (self.color_schema + 1)%len(schemas)
                        self.load_colors("color/%s"%(schemas[self.color_schema]))
                    if event.key == K_r:
                        pygame.mixer.stop()
                        self.reset()
                    if event.key == K_z:
                        self.randomize_colors()
                    if event.key == K_x:
                        self.load_colors()
                    if event.key == K_v:
                        self.print_colors()
                    if event.key == K_n:
                        self.difficulty = (self.difficulty + 1)%len(self.difficulties)
                        self.reset()
                    if event.key == K_p:
                        self.difficulty = (self.difficulty - 1)%len(self.difficulties)
                        self.reset()
            self.draw()

def main():
    pygame.init()
    #pygame.display.init()
    #pygame.font.init()
    #pygame.mixer.init()
    game = Mines()
    game.play()
    pygame.quit()

if __name__ == '__main__':
    main()
