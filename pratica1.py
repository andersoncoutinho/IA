# Biblioteca pyamaze

from pyamaze import maze,agent,COLOR
from collections import deque
from sys import maxsize

import tkinter as tk

orig_state = tk.Tk.state

def patched_state(self, newstate=None):
    if newstate == "zoomed":
        newstate = "normal"
    return orig_state(self, newstate)

tk.Tk.state = patched_state

def BFS(m,start=None):
    if start is None:
        start=(m.rows,m.cols)
    frontier = deque()
    frontier.append(start)
    bfsPath = {}
    explored = [start]
    bSearch=[]

    while len(frontier)>0:
        currCell=frontier.popleft()
        bSearch.append(currCell)
        if currCell==m._goal:
            break
        for d in 'WNSE':
            if m.maze_map[currCell][d]==True:
                if d=='E':
                    childCell=(currCell[0],currCell[1]+1)
                elif d=='W':
                    childCell=(currCell[0],currCell[1]-1)
                elif d=='S':
                    childCell=(currCell[0]+1,currCell[1])
                elif d=='N':
                    childCell=(currCell[0]-1,currCell[1])
                if childCell in explored:
                    continue
                frontier.append(childCell)
                explored.append(childCell)
                bfsPath[childCell] = currCell
                
    fwdPath={}
    cell=m._goal
    while cell!=start:
        fwdPath[bfsPath[cell]]=cell
        cell=bfsPath[cell]
    return bSearch,bfsPath,fwdPath

def DLS(m, start=None, limit=maxsize):
    if start is None:
        start=(m.rows,m.cols)
    explored=[start]
    frontier=[(start,0)]
    dlsPath={}
    dSearch=[]
    while len(frontier)>0:
        currCell, depth =frontier.pop()
        dSearch.append(currCell)
        if depth > limit:
            continue
        
        if currCell==m._goal:
            break
        for d in 'ESNW':
            if m.maze_map[currCell][d]==True:
                if d=='E':
                    childCell=(currCell[0],currCell[1]+1)
                elif d=='W':
                    childCell=(currCell[0],currCell[1]-1)
                elif d=='S':
                    childCell=(currCell[0]+1,currCell[1])
                elif d=='N':
                    childCell=(currCell[0]-1,currCell[1])
                if childCell in explored:
                    continue
                explored.append((childCell))
                frontier.append((childCell, depth+1))
                dlsPath[childCell]=currCell
                
    fwdPath={}
    cell=m._goal
    while cell!=start and cell in dlsPath:
        fwdPath[dlsPath[cell]]=cell
        cell=dlsPath[cell]
    return dSearch,dlsPath,fwdPath

# Os parâmetros são o comprimento e a largura do mapa, respectivamente
dimensions = (15,15)
m=maze(dimensions[0],dimensions[1])
# x e y são as coordenadas que se deseja chegar
# loopPercent é um parâmetro que quanto mais alto maior é a quantidade
# de caminhos possíveis até o objetivo
m.CreateMaze(x=1, y=7, loopPercent=50) 

start = (dimensions[0],dimensions[1])

# DLS

# a=agent(m, start[0], start[1], footprints=True, color=COLOR.yellow, shape='square') 
# b=agent(m, start[0], start[1], footprints=True, color=COLOR.cyan, shape='square', filled=True) 
# dSearch,dlsPath,dfinalPath=DLS(m, start)
# m.tracePath({a:dSearch},delay=100)
# m.tracePath({b:dfinalPath},delay=100)

# BFS

c=agent(m, start[0], start[1], footprints=True, color=COLOR.yellow, shape='square') 
d=agent(m, start[0], start[1], footprints=True, color=COLOR.cyan, shape='square', filled=True) 
bSearch,bfsPath,bfinalPath=BFS(m, start)
m.tracePath({c:bSearch},delay=100)
m.tracePath({d:bfinalPath},delay=100)

m.run()
