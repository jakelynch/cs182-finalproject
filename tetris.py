#!/usr/bin/env python2
#-*- coding: utf-8 -*-

# NOTE FOR WINDOWS USERS:
# You can download a "exefied" version of this game at:
# http://kch42.de/progs/tetris_py_exefied.zip
# If a DLL is missing or something like this, write an E-Mail (kevin@kch42.de)
# or leave a comment on this gist.

# Very simple tetris implementation
# 
# Control keys:
#       Down - Drop stone faster
# Left/Right - Move stone
#         Up - Rotate Stone clockwise
#     Escape - Quit game
#          P - Pause game
#     Return - Instant drop
#
# Have fun!

# Copyright (c) 2010 "Kevin Chabowski"<kevin@kch42.de>
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
import time
import numpy as np
from random import randrange as rand
import pygame, sys, copy
import  random,util,math
##import qlearningagent
from copy import deepcopy
import cPickle as pickle
# The configuration
cell_size =	18
cols =		10 
rows =		22
maxfps = 	30

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
				print "IndexError"
				return True
	return False

def remove_row(board, row):
	del board[row]
	return [[0 for i in xrange(cols)]] + board
	
def join_matrixes(mat1, mat2, mat2_off):
	off_x, off_y = mat2_off
	for cy, row in enumerate(mat2):
		for cx, val in enumerate(row):
			mat1[cy+off_y-1][cx+off_x] += val
	return mat1

def new_board():
	board = [ [ 0 for x in xrange(cols) ]
			for y in xrange(rows) ]
	board += [[ 9 for x in xrange(cols)] for i in xrange(1)]
	return board

class TetrisApp(object):
	def __init__(self):
		pygame.init()
		pygame.key.set_repeat(250,25)
		self.width = cell_size*(cols+6)
		self.height = cell_size*rows
		self.rlim = cell_size*cols
		self.boardprev = 0
		self.numpieces= 0
		self.bground_grid = [[ 8 if x%2==y%2 else 0 for x in xrange(cols)] for y in xrange(rows)]
		
		self.default_font =  pygame.font.Font(
			pygame.font.get_default_font(), 12)
		
		self.screen = pygame.display.set_mode((self.width, self.height))
		pygame.event.set_blocked(pygame.MOUSEMOTION) # We do not need
		                                             # mouse movement
		                                             # events, so we
		                                             # block them.
		# This is the first time that it passes in a falling piece, and it chooses it randomly,
		# if we are to reach the point that we can do adverserial tetris, then we will want to
		# replace this line so that it always starts with the most troublesome piece
		self.next_stone = tetris_shapes[rand(len(tetris_shapes))]
		self.init_game()
		#self.Q = qlearningagent.QLearningAgent()
	
	def new_stone(self):
		# Where we will have to insert the remainder of our adverserial function, right now it just chooses
		# the different kinds randomly and we would replace that with an intelligent adversary that attempts
		# to make it as difficult as possible for the max player
		self.numpieces += 1
		self.stone = self.next_stone[:]
		self.next_stone = tetris_shapes[rand(len(tetris_shapes))]
		self.stone_x = int(cols / 2 - len(self.stone[0])/2)
		self.stone_y = 0
		
		if check_collision(self.board,
		                   self.stone,
		                   (self.stone_x, self.stone_y)):
			self.gameover = True

	
	def init_game(self):
		self.board = new_board()
		self.numpieces = 0
		self.new_stone()
		self.level = 1
		self.score = 0
		self.lines = 0
		pygame.time.set_timer(pygame.USEREVENT+1, 1000)
	
	def disp_msg(self, msg, topleft):
		x,y = topleft
		for line in msg.splitlines():
			self.screen.blit(
				self.default_font.render(
					line,
					False,
					(255,255,255),
					(0,0,0)),
				(x,y))
			y+=14
	
	def center_msg(self, msg):
		for i, line in enumerate(msg.splitlines()):
			msg_image =  self.default_font.render(line, False,
				(255,255,255), (0,0,0))
		
			msgim_center_x, msgim_center_y = msg_image.get_size()
			msgim_center_x //= 2
			msgim_center_y //= 2
		
			self.screen.blit(msg_image, (
			  self.width // 2-msgim_center_x,
			  self.height // 2-msgim_center_y+i*22))
	
	def draw_matrix(self, matrix, offset):
		off_x, off_y  = offset
		for y, row in enumerate(matrix):
			for x, val in enumerate(row):
				if val!=9:
					pygame.draw.rect(
						self.screen,
						colors[val],
						pygame.Rect(
							(off_x+x) *
							  cell_size,
							(off_y+y) *
							  cell_size, 
							cell_size,
							cell_size),0)
	
	def add_cl_lines(self, n):
		linescores = [0, 40, 100, 300, 1200]
		self.lines += n
		self.score += linescores[n] * self.level
		if self.lines >= self.level*6:
			self.level += 1
			newdelay = 1000-50*(self.level-1)
			newdelay = 100 if newdelay < 100 else newdelay
			pygame.time.set_timer(pygame.USEREVENT+1, newdelay)
	
	def move(self, delta_x):
		if not self.gameover and not self.paused:
			new_x = self.stone_x + delta_x
			if new_x < 0:
				new_x = 0
			if new_x > cols - len(self.stone[0]):
				new_x = cols - len(self.stone[0])
			if not check_collision(self.board,
			                       self.stone,
			                       (new_x, self.stone_y)):
				self.stone_x = new_x
	def quit(self):
		self.center_msg("Exiting...")
		pygame.display.update()
		sys.exit()

	def drop(self, manual):
		if not self.gameover and not self.paused:
			self.score += 1 if manual else 0
			self.stone_y += 1
			if check_collision(self.board,
			                   self.stone,
			                   (self.stone_x, self.stone_y)):
				self.board = join_matrixes(
				  self.board,
				  self.stone,
				  (self.stone_x, self.stone_y))
				self.new_stone()
				cleared_rows = 0
				while True:
					for i, row in enumerate(self.board[:-1]):
						if 0 not in row:
							self.board = remove_row(
							  self.board, i)
							cleared_rows += 1
							break
					else:
						break
				self.add_cl_lines(cleared_rows)
				return True
		return False
	
	def insta_drop(self):
		if not self.gameover and not self.paused:
			while(not self.drop(True)):
				pass

	
	def rotate_stone(self):
		if not self.gameover and not self.paused:
			new_stone = rotate_clockwise(self.stone)
			if not check_collision(self.board,
			                       new_stone,
			                       (self.stone_x, self.stone_y)):
				self.stone = new_stone
	
	def toggle_pause(self):
		self.paused = not self.paused
	
	def start_game(self):
		if self.gameover:
			self.init_game()
			self.gameover = False

	def place_brick(self, num_rotations, best_x):
		cur_x = self.stone_x
		cur_y = self.stone_y
		dif_x = self.stone_x - best_x

		for x in range(num_rotations):
			self.rotate_stone()

		if dif_x < 0:
			for x in range(-(dif_x)):
				self.move(+1)
		else:
			for x in range(dif_x):
				self.move(-1)
				

		# Once ideal rotation and pos is in line, just drops the brick to speed up the game
		self.insta_drop()
 

	def ideal_place(self,origboard):
		""" We need to find a way to stop this from running on every loop because the way it is written
		breaks the game when a piece is at the bottom, it ends the game and passes an error, so we need to
		make it so that this function is run once when a new stone appears, then place_brick runs until the
		brick is placed then the game will call a new stone and the process will repeat"""

		actions = self.get_legal_actions(self.Tetris.stone)
		board = copy.deepcopy(origboard)
		heuristicvals = []
		y = 0
		differencearray= []

		for action in actions:
			y=0
			rot, x = action

			rotpiece = deepcopy(self.Tetris.stone)
			for i in range(rot):	
				rotpiece = 	rotate_clockwise(rotpiece)	

			hyp_board = copy.deepcopy(self.Tetris.board)
			while not(check_collision(hyp_board, rotpiece, (x, y))):
				y+=1



			new_board = join_matrixes(hyp_board, rotpiece, (x,y))

			for i in range(len(new_board)-1):
				if 0 not in new_board[i] and max(new_board[i])<8:
					return action

			differencearray.append(self.toprow(self.Tetris.board,new_board))



		bestaction = actions[differencearray.index(max(differencearray))]
		return bestaction

	def get_legal_actions(self, stone):
		rotations = []
		actions = []
		rotations.append(stone)
		for i in range(1,4):
			rotations.append(rotate_clockwise(rotations[i - 1]))
			#print rotate_clockwise(rotations[i-1])
		for rot in rotations:
			for x in range(cols - len(rot[0])+1):
				actions.append((rotations.index(rot), x))

		return actions


	def get_states(self):
		board = copy.deepcopy(self.board)
		rotations.append(self.stone)
		#print self.stone
		for i in range(1,3):
			rotations.append(rotate_clockwise(rotations[i - 1]))
		for stone in rotations:
			pass



	def average_height(self,board):
		#board_array = np.array(board)
		#print len(board),len(board[0])
		transpose= self.arraytranspose(board)
		#print len(transpose)

		state = []

		for row in transpose:
			# print row
			state.append(next((rows-i for i, x in enumerate(row) if x>0), 0))
		val = float(sum(state))/float(len(state))
		#print val
		return val
		"""board_array_transpose=self.arraytranspose(board)
		Sum= 0
		#print "board_array_transpose = ", board_array_transpose 
		for row in board_array_transpose:

			for i in range(len(row)):
				if row[cols-i] > 0:
					break
				Sum +=1
		val = float(Sum)/float(len(board))
		print "val", val
		return val
		"""

	def difference_squared(self,board, column):
		#board_array = np.array(board)
		transpose=self.arraytranspose(board)
		
		Sum1= 0
		Sum2 = 0
		Sum3= 0
		sq_difference = 0
		for i in range(len(transpose[column])):
			if transpose[column][i]> 0:
				break
			Sum1+=1
		for i in range(len(transpose[column-1])):
			if transpose[column-1][i]> 0:
				break
			Sum2+=1
		for i in range(len(transpose[column+1])):
			if transpose[column+1][i]> 0:
				break
			Sum3+=1
		sq_difference+= (Sum3-Sum1)**2 + (Sum2-Sum1)**2
		return sq_difference

	def heur_diffsum(self, board):
		diffsq=[]
		for i in range(1,cols-1):
			diffsq.append(self.difference_squared(board,i))
		diffsqsum = sum(diffsq)
		avgheight =self.average_height(board)
		return -(diffsqsum+avgheight)

	def heur_row_removal(self, board):
		score = 0
		for i in range(rows):
			if 0 not in board[i]:
				score += 1
		return score

	def heur_empty_spaces(self, board):
		score = 0
		for i in range(rows):
			for j in range(cols):
				if board[i][j] != 0:
					y = 0
					while y < (rows - i):
						if board[rows - y][j] == 0:
							score += 1
						y += 1
		return score

	def heur_bordering_pieces(self, board):
		score = 0
		for i in range(rows):
			for j in range(cols):
				if j == 9 or j == 0:
					if board[i][j] != 0:
						score += 1
		return score

	def heur_touching_pieces(self, board):
		score = 0
		for i in range(rows):
			for j in range(cols):
				if 1<j<8:
					if board[i][j] != 0 and (board[i][j+1] != 0 or board[i][j-1] != 0):
						score += 1
		return score

	def heur_row_count(self, board):
		avg = 0
		rowcount = []
		for i in range(rows):
			if np.count_nonzero(board[i])>0:
				rowcount.append(np.count_nonzero(board[i]))
		if rowcount != []:
			avg = np.average(rowcount)
		return avg 

	def heur_height(self, board):
		transpose=self.arraytranspose(board)
		state = []

		for row in transpose:
			# print row
			state.append(next((rows-i for i, x in enumerate(row) if x>0), 0))
		#print state
		average=float(sum(state))/float(len(state))
		return average

	def heuristic(self, possboard):
		board = np.array(possboard)
		score = 0
		score += 0.15 * self.heur_diffsum(board)
		score += 75 * self.heur_row_removal(board)
		score -= 1 * self.heur_empty_spaces(board)
		score += 3 * self.heur_bordering_pieces(board)
		score += 2 * self.heur_touching_pieces(board)
		score += 3 * self.heur_row_count(board)
		print "Score: ", score
		return score


	def get_board_state(self, board):
		
		transpose= self.arraytranspose(board)

		state = []
		for row in transpose:
			state.append(next((rows-i for i, x in enumerate(row) if x>0), 0))
		row = rows-max(state)
		if max(state) >3:
			array = np.array(board[row:row+3])
			array[array >0] = 1
		else: 
			array = np.array(board[rows-4:rows])
			array[array >0] = 1
		posed = self.arraytranspose(array)
		finalarray = []
		for row in posed:
			finalarray.append(next((3-i for i, x in enumerate(row) if x>0), 0))

		return finalarray
		
	
	def toprow(self,board,hyp_board):
		val = 0
		for i in range(len(board)-2):
			row1, row2,row3, =np.array(board[i]), np.array(board[i+1]), np.array(board[i+2])
			row4, row5, row6 = np.array(hyp_board[i]), np.array(hyp_board[i+1]), np.array(hyp_board[i+2])

			val1,val2,val3 = len(row1[row1>0]),len(row2[row2>0]),len(row3[row3>0])
			val4,val5,val6 = len(row4[row4>0]),len(row5[row5>0]),len(row6[row6>0])
			if val1>0 :

]				return (val4+val5+val6)-(val1 + val2+val3)

		return 0.

	def maxrow(self,board):
		maxval = 0
		for row in board[:len(board)-1]:
			row = np.array(row)
			val = len(row[row>0])
			if val>maxval:
				maxval = val

		return maxval


	def arraytranspose(self, board):
		board2 = deepcopy(board)
		# print board2
		board3 = [[0 for i in range(len(board2))] for i in range(len(board2[0]))]
		# print len(board2),len(board2[0])

		for i in range(len(board2[0])):
			for j in range(len(board2)):
				

				board3[i][j] = board2[j][i]

		return  board3

"""

if __name__ == '__main__':
	App = TetrisApp()
	for i in range(10):
		App.run()
"""