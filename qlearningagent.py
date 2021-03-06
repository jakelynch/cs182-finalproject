import random,util,math
import cPickle as pickle
import tetris
from tetris import TetrisApp
from random import randrange as rand
import pygame, sys, copy
import  random,util,math
import matplotlib.pyplot as plt
import time
from copy import deepcopy
import pickle
import cProfile
import re
cell_size = 18
cols =    10 
rows =    22
maxfps =  2000000

# Variables setting amount of times each part of program runs
value_iter_rounds = 1000 
total_iterations = 11000

colors = [
(0,   0,   0  ),
(255, 85,  85),
(100, 200, 115),
(120, 108, 245),
(255, 140, 50 ),
(50,  120, 52 ),
(146, 202, 73 ),
(150, 161, 218 ),
(35,  35,  35) # Helper color for background grid
]

# Define the shapes of the single parts
tetris_shapes = [
  [[0, 1, 0],
   [1, 1, 1]],
  
  [[0, 2, 2],
   [2, 2, 0]],
  
  [[3, 3, 0],
   [0, 3, 3]],
  
  [[4, 0, 0],
   [4, 4, 4]],
  
  [[0, 0, 5],
   [5, 5, 5]],
  
  [[6, 6, 6, 6]],
  
  [[7, 7],
   [7, 7]]
]


def rotate_clockwise(shape):
  return [ [ shape[y][x]
      for y in xrange(len(shape)) ]
    for x in xrange(len(shape[0]) - 1, -1, -1) ]

rotdict ={}
for stone in tetris_shapes:
  rots = 0
  rotdict[str(stone)]= 0
  while str(rotate_clockwise(stone)) not in rotdict:
    stone = rotate_clockwise(stone)
    rots+=1
    rotdict[str(stone)]= rots

def check_collision(board, shape, offset):
  off_x, off_y = offset
  for cy, row in enumerate(shape):
    for cx, cell in enumerate(row):
      try:
        if cell and board[ cy + off_y ][ cx + off_x ]:
          return True
      except IndexError:
        return True
  return False

def remove_row(board, row):
  del board[row]
  return [[0 for i in xrange(cols)]] + board
  
def join_matrixes(mat1, mat2, mat2_off):
  off_x, off_y = mat2_off
  for cy, row in enumerate(mat2):
    for cx, val in enumerate(row):
      mat1[cy+off_y-1 ][cx+off_x] += val
  return mat1

def new_board():
  board = [ [ 0 for x in xrange(cols+1) ]
      for y in xrange(rows) ]
  board += [[ 9 for x in xrange(cols)] for i in xrange(1)]
  return board

class QLearningAgent(TetrisApp):
    def __init__(self, alpha = 0.01, gamma = .5, epsilon = 1):
        self.qval=util.Counter()
        self.alpha=alpha
        self.epsilon=epsilon
        self.discount=gamma
        self.Tetris= TetrisApp()
        self.boardprev=0.

    def observeTransition(self, state,action,nextState,deltaReward):
        self.episodeRewards += deltaReward
        self.update(state,action,nextState,deltaReward)

    # returns 0.0 if new state or the q value if we've seen it, and because
    # we cant use tuples as keys in a python dict we hash them
    def getQValue(self, state, action):
        if hash(str((state, action))) not in self.qval:
          self.qval[hash(str((state,action)))]=0.0
        return self.qval[hash(str((state,action)))]

    def computeValueFromQValues(self, state):
        val = 0.0
        action=self.computeActionFromQValues(state)
        if action != None:
          val= self.getQValue(state,action)
        return val

    def computeActionFromQValues(self, state):
        finalaction=None
        legalActions = self.Tetris.get_legal_actions(state[1])

        if len(legalActions)!=0:
          maxval= -999999
          for action in self.Tetris.get_legal_actions(state[1]):
            Qval=self.getQValue(state,action)
            if Qval>=maxval:
              maxval=Qval
              finalaction=action
        return finalaction

    def helperfunction(self, lst, legalactions):
      value, action, new_board = lst
      val = (value + max(self.ideal_place_2(new_board, legalactions,True))[0], action)
      return val


    def getAction(self, state):
        legalActions = self.Tetris.get_legal_actions(state[1])
        action = None
        if len(legalActions)!=0:
              if util.flipCoin(self.epsilon):
                valuedict = {}
                actionlist= self.ideal_place_2(self.Tetris.board, legalActions, False)
                valuelist = map((lambda x: self.helperfunction(x, legalActions)), actionlist)
                return max(valuelist)[1]
              else:
                action = self.computeActionFromQValues(state)
        return action
        
    def update(self, state, action, nextState, reward):
        self.qval[hash(str((state,action)))]+= self.alpha*(reward+self.discount * self.computeValueFromQValues(nextState) - self.getQValue(state,action))
  
    def getPolicy(self, state):
        return self.computeActionFromQValues(state)

    def getValue(self, state):
        return self.computeValueFromQValues(state)

    def run(self,n):
      key_actions = {
        'ESCAPE': self.Tetris.quit,
        'LEFT':   lambda:self.Tetris.move(-1),
        'RIGHT':    lambda:self.Tetris.move(+1),
        'DOWN':   lambda:self.Tetris.drop(True),
        'UP':   self.Tetris.rotate_stone,
        'SPACE':    self.Tetris.toggle_pause,
        'SPACE':  self.Tetris.start_game,
        'RETURN': self.Tetris.insta_drop
      }

      self.Tetris.board = tetris.new_board()
      self.boardprev=self.Tetris.board

      if n< value_iter_rounds:
        self.epsilon = 1
      else:
        self.epsilon = 1/(15.*math.log(float(n)+1))
  
      self.Tetris.gameover = False
      self.Tetris.paused = False
      
      dont_burn_my_cpu = pygame.time.Clock()
      rot, col = self.getAction((self.Tetris.get_board_state(self.Tetris.board),self.Tetris.stone))
      prevboard = self.Tetris.board
      n+=1
      while not(self.Tetris.gameover):
        self.update((prevboard,self.Tetris.stone), (rot,col), (self.Tetris.get_board_state(self.Tetris.board),self.Tetris.stone), self.Tetris.heuristic(self.Tetris.board)) 
        piece = self.Tetris.stone
        prevboard = tetris.deepishcopy(self.Tetris.board)
        legalactions = self.Tetris.get_legal_actions(self.Tetris.stone)
        rot, col =self.getAction((self.Tetris.get_board_state(self.Tetris.board), self.Tetris.stone))
        i= 1
        while i ==1:
          self.Tetris.screen.fill((0,0,0))
          if self.Tetris.gameover:
            self.Tetris.center_msg("""Game Over!\nYour score: %d
    Press space to continue""" % self.Tetris.score)
            if n< 10000:
              self.Tetris.start_game()
            else: 
              self.Tetris.quit()
          else:
            if self.Tetris.paused:
              self.Tetris.center_msg("Paused")
            else:
              pygame.draw.line(self.Tetris.screen,
                (255,255,255),
                (self.Tetris.rlim+1, 0),
                (self.Tetris.rlim+1, self.Tetris.height-1))
              self.Tetris.disp_msg("Next:", (
                self.Tetris.rlim+cell_size,
                2))
              self.Tetris.disp_msg("Score: %d\n\nLevel: %d\
    \nLines: %d" % (self.Tetris.score, self.Tetris.level, self.Tetris.lines),
                (self.Tetris.rlim+cell_size, cell_size*5))
              self.Tetris.draw_matrix(self.Tetris.bground_grid, (0,0))
              self.Tetris.draw_matrix(self.Tetris.board, (0,0))
              self.Tetris.draw_matrix(self.Tetris.stone,
                (self.Tetris.stone_x, self.Tetris.stone_y))
              self.Tetris.draw_matrix(self.Tetris.next_stone,
                (cols+1,2))
          pygame.display.update()



          self.Tetris.place_brick(rot,col)
          i= 0
          for event in pygame.event.get():
            if event.type == pygame.USEREVENT+1:
              pass
            elif event.type == pygame.QUIT:
              self.Tetris.quit()
            elif event.type == pygame.KEYDOWN:
              for key in key_actions:
                if event.key == eval("pygame.K_"
                +key):
                  key_actions[key]()
              
if __name__ == '__main__':
  Q = QLearningAgent()
  iters = []
  linescleared = []
  piecesdropped = []

  for i in range(total_iterations):
    print "Iteration: ", i
    Q.run(i+1)
    if (i % 2 == 0):
      iters.append(i)
      linescleared.append(Q.Tetris.lines)
      piecesdropped.append(Q.Tetris.numpieces)

  # Here is where we pickled the Q data and plotted our graphs once
  # the program had completed running
  pickle.dump(Q.qval, open("Q.p", "wb"))
  plt.figure(1)
  plt.plot(iters, linescleared)
  plt.ylabel("Lines Cleared")
  plt.xlabel("Number of Iterations of Q Learning")
  plt.title("Performance Throughout Learning")

  plt.figure(2)
  plt.plot(iters, piecesdropped)
  plt.ylabel("Pieces Dropped")
  plt.xlabel("Number of Iterations of Q Learning")
  plt.title("Performance Throughout Learning")
  plt.show()

  # pickle time
  file = open('qvalues', 'w')
  pickle.dump(Q.qval2, file)

  file.close()



