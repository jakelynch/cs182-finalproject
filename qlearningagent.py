import random,util,math
import tetris
from tetris import TetrisApp
from random import randrange as rand
import pygame, sys, copy
import  random,util,math
import matplotlib.pyplot as plt
##import qlearningagent
from copy import deepcopy

cell_size = 18
cols =    10 
rows =    22
maxfps =  30

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
  
  #[[6, 6, 6, 6]],
  
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
#print rotdict
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
  #print "mat1 = " + str(mat1), "mat2 = " + str(mat2), "mat2_off = " + str(mat2_off)
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



class Agent:
    """
    An agent must define a getAction method, but may also define the
    following methods which will be called if they exist:

    def registerInitialState(self, state): # inspects the starting state
    """
    def __init__(self, index=0):
        self.index = index

    def getAction(self, state):
        """
        The Agent will receive a GameState (from either {pacman, capture, sonar}.py) and
        must return an action from Directions.{North, South, East, West, Stop}
        """
        raiseNotDefined()


class QLearningAgent(TetrisApp):
    """
      Q-Learning Agent

      Functions you should fill in:
        - computeValueFromQValues
        - computeActionFromQValues
        - getQValue
        - getAction
        - update

      Instance variables you have access to
        - self.epsilon (exploration prob)
        - self.alpha (learning rate)
        - self.discount (discount rate)

      Functions you should use
        - self.getLegalActions(state)
          which returns legal actions for a state
    """
    def __init__(self, alpha = 0.01, gamma = .5, epsilon = 1):
        "You can initialize Q-values here..."
        "reinforcementAgent.__init__(self, **args)"
        self.qval=util.Counter()
        self.alpha=alpha
        self.epsilon=epsilon
        self.discount=gamma
        self.Tetris= TetrisApp()
        self.boardprev=0.

        "*** YOUR CODE HERE ***"

    """def getLegalActions(self,state):
                    
                      Get the actions available for a given
                      state. This is what you should use to
                      obtain legal actions for a state
                    
                    return self.actionFn(state)
            """
    def observeTransition(self, state,action,nextState,deltaReward):
        """
            Called by environment to inform agent that a transition has
            been observed. This will result in a call to self.update
            on the same arguments

            NOTE: Do *not* override or call this function
        """
        self.episodeRewards += deltaReward
        self.update(state,action,nextState,deltaReward)

    def getQValue(self, state, action):
        """
          Returns Q(state,action)
          Should return 0.0 if we have never seen a state
          or the Q node value otherwise
        """
        "*** YOUR CODE HERE ***"
        #print "this is\n"
        #print state,action
        if hash(str((state, action))) not in self.qval:
          #print state, action
          self.qval[hash(str((state,action)))]=0.0
          # print "we're getting this"
        if self.qval[hash(str((state,action)))]!=0:
          print "Qval=",self.qval[hash(str((state,action)))] 
        elif self.qval[hash(str((state,action)))]>0:
          print "we're getting somthing else",  self.qval[hash(str((state,action)))]
        return self.qval[hash(str((state,action)))]

    def computeValueFromQValues(self, state):
        """
          Returns max_action Q(state,action)
          where the max is over legal actions.  Note that if
          there are no legal actions, which is the case at the
          terminal state, you should return a value of 0.0.
        """
        "*** YOUR CODE HERE ***"
        val = 0.0
        action=self.computeActionFromQValues(state)
        if action != None:
          val= self.getQValue(state,action)
        #print val
        return val

    def computeActionFromQValues(self, state):
        """
          Compute the best action to take in a state.  Note that if there
          are no legal actions, which is the case at the terminal state,
          you should return None.
        """
        "*** YOUR CODE HERE ***"
        
        finalaction=None
        legalActions = self.Tetris.get_legal_actions(state[1])

        if len(legalActions)!=0:
          maxval= -999999
          #print type(legalActions)
          #print "legalactions: ", self.Tetris.get_legal_actions(state[1])
          for action in self.Tetris.get_legal_actions(state[1]):
            #print action, type(action),state
            Qval=self.getQValue(state,action)

            
            if Qval>=maxval:
              maxval=Qval
              finalaction=action
              
        if maxval>0:
           print "Qval=" +str(maxval)
        return finalaction

    def getAction(self, state):
        """
          Compute the action to take in the current state.  With
          probability self.epsilon, we should take a random action and
          take the best policy action otherwise.  Note that if there are
          no legal actions, which is the case at the terminal state, you
          should choose None as the action.

          HINT: You might want to use util.flipCoin(prob)
          HINT: To pick randomly from a list, use random.choice(list)
        """
        # Pick Action
        legalActions = self.Tetris.get_legal_actions(state[1])
        action = None
        "*** YOUR CODE HERE ***"
        if len(legalActions)!=0:
              if util.flipCoin(self.epsilon):
                action = self.ideal_place(self.Tetris.board)
                #print action 
                


              else:
                action = self.computeActionFromQValues(state)

        #print action
        return action

    def update(self, state, action, nextState, reward):
        """
          The parent class calls this to observe a
          state = action => nextState and reward transition.
          You should do your Q-Value update here

          NOTE: You should never call this function,
          it will be called on your behalf
        """
        "*** YOUR CODE HERE ***"
        #print reward
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

      """ try: 
                       print self.Tetris.board-self.boardprev
                     except:
                       pass"""
      self.Tetris.board = tetris.new_board()
      self.boardprev=self.Tetris.board

      self.epsilon = 1./float(15*math.log(n)+1.)

      
      self.Tetris.gameover = False
      self.Tetris.paused = False
      #print self.Tetris.board

      
      dont_burn_my_cpu = pygame.time.Clock()
      rot, col = self.getAction((self.Tetris.get_board_state(self.Tetris.board),self.Tetris.stone))
      prevboard = self.Tetris.get_board_state(self.Tetris.board)
      n+=1
      # print n
      #while 1:
      while not(self.Tetris.gameover):

        # print self.Tetris.stone
        # print self.Tetris.stone_x
        # print self.Tetris.stone_y
        #print "rot,col=" +str((rot,col))
        self.update((prevboard,self.Tetris.stone), (rot,col), (self.Tetris.get_board_state(self.Tetris.board),self.Tetris.stone), self.Tetris.heuristic(self.Tetris.board)) 

        piece = self.Tetris.stone
        prevboard = self.Tetris.get_board_state(self.Tetris.board)
        legalactions = self.Tetris.get_legal_actions(self.Tetris.stone)
        rot, col =self.getAction((self.Tetris.get_board_state(self.Tetris.board), self.Tetris.stone))
        # print "rot, col ",  rot, col
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
              #print self.Tetris.board
              self.Tetris.draw_matrix(self.Tetris.board, (0,0))
              self.Tetris.draw_matrix(self.Tetris.stone,
                (self.Tetris.stone_x, self.Tetris.stone_y))
              self.Tetris.draw_matrix(self.Tetris.next_stone,
                (cols+1,2))
          pygame.display.update()

          #self.Tetris.ideal_place()
          """prevboard = deepcopy(self.Tetris.board)
                                                  legalactions = self.Tetris.get_legal_actions(self.Tetris.stone)
                                                  rot, col =self.getActihon(self.Tetris.stone)
                                        """


          self.Tetris.place_brick(rot,col)
          i= 0
          #print self.Tetris.board
          for event in pygame.event.get():
            if event.type == pygame.USEREVENT+1:
              pass
            # self.Tetris.drop(False)
            elif event.type == pygame.QUIT:
              self.Tetris.quit()
            elif event.type == pygame.KEYDOWN:
              for key in key_actions:
                if event.key == eval("pygame.K_"
                +key):
                  key_actions[key]()
              
          dont_burn_my_cpu.tick(maxfps)

if __name__ == '__main__':
  Q = QLearningAgent()
  iters = []
  linescleared = []
  piecesdropped = []
  for i in range(6):
    Q.run(i+1)
    if (i % 2 == 0):
      # print i,"th iteration: ", Q.Tetris.lines, "lines cleared"
      iters.append(i)
      linescleared.append(Q.Tetris.lines)
      piecesdropped.append(Q.Tetris.numpieces)
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
