import copy

class Grid:
    def __init__(self, w, h, val):
        self.w = w
        self.h = h
        self.v = []
        
        temp = []
        for y in range(h):
            temp.append(copy.deepcopy(val))
        for x in range(w):
            self.v.append(copy.deepcopy(temp))

    def addrow(self, val):
        self.h += 1
        for x in range(self.w):
            self.v[x].append(copy.deepcopy(val))
    def subrow(self):
        if self.h > 1:
            self.h -= 1
            for x in range(self.w):
                self.v[x].pop()
    def addcol(self, val):
        temp = []
        self.w += 1
        for y in range(self.h):
            temp.append(copy.deepcopy(val))
        self.v.append(copy.deepcopy(temp))
    def subcol(self):
        if self.w > 1:
            self.w -= 1
            self.v.pop()

    def setv(self, x, y, val):
        self.v[x][y] = val

    def getv(self, x, y):
        return self.v[x][y]
