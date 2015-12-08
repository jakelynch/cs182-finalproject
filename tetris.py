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
import numpy as np
from random import randrange as rand
import pygame, sys, copy
import  random,util,math
##import qlearningagent
from copy import deepcopy
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
	[[1, 1, 1],
	 [0, 1, 0]],
	
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
			mat1[cy+off_y-1	][cx+off_x] += val
	return mat1

def new_board():
	board = [ [ 0 for x in xrange(cols) ]
			for y in xrange(rows) ]
	board += [[ 1 for x in xrange(cols)] for i in xrange(1)]
	return board

class TetrisApp(object):
	def __init__(self):
		pygame.init()
		pygame.key.set_repeat(250,25)
		self.width = cell_size*(cols+6)
		self.height = cell_size*rows
		self.rlim = cell_size*cols
		self.boardprev = 0
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
				if val:
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

		# Rotates brick to proper position
		for x in range(num_rotations):
			self.rotate_stone()

		# Places brick in best x position
		if dif_x < 0:
			# move piece dif_x moves left
			for x in range(dif_x):
				self.move(+1)
		else:
			# move piece dif_x moves right
			for x in range(dif_x):
				self.move(-1)

		# Once ideal rotation and pos is in line, just drops the brick to speed up the game
		self.insta_drop()
 

	def ideal_place(self,origboard):
		""" We need to find a way to stop this from running on every loop because the way it is written
		breaks the game when a piece is at the bottom, it ends the game and passes an error, so we need to
		make it so that this function is run once when a new stone appears, then place_brick runs until the
		brick is placed then the game will call a new stone and the process will repeat"""

		heuristicvals = []
		bestxforrot = []
		bestvalforrot = []
		rotations = []
		board = copy.deepcopy(origboard)
		
		rotations.append(self.Tetris.stone)
		#print self.stone
		for i in range(1,3):
			rotations.append(rotate_clockwise(rotations[i - 1]))
		for stone in rotations:
			actions = self.get_legal_actions(stone)
			#print "actions: ", actions
			for x in range(cols-len(stone[0])):
				for y in range(rows):
					if check_collision(board, stone, (x, y-len(stone))):
						hyp_board = copy.deepcopy(self.Tetris.board)
						#print type(hyp_board)
						try:
							#print "here"
							#print join_matrixes(hyp_board, stone, (x,y))
							#print "matrix ", join_matrixes(hyp_board, stone, (x,y))
							difference = self.maxrow(join_matrixes(hyp_board, stone, (x,y)))- self.maxrow(origboard)
							
							heuristicvals.append(difference)
						except: 
							print "Oops thats an error"
							
						print x,y
						print stone
						# print "copied board: ", board, "\n"
						# print "board: ", board, "\n"
						# print join_matrixes(hyp_board, self.stone, (x,y))
			print max(heuristicvals)
			bestvalforrot.append(max(heuristicvals))
			bestxforrot.append(heuristicvals.index(max(heuristicvals)))

		bestrot = bestvalforrot.index(max(bestvalforrot))
		#print "we return ", rotations[bestrot], bestxforrot[bestrot]
		action = rotations[bestrot], bestxforrot[bestrot]
		print action
		return action

	def get_legal_actions(self, stone):
		rotations = []
		actions = []
		rotations.append(stone)
		for i in range(1,3):
			rotations.append(rotate_clockwise(rotations[i - 1]))
			#print rotate_clockwise(rotations[i-1])
		for rot in rotations:
			for x in range(cols - len(stone[0])):
				actions.append((rot, x))
		return actions


	def get_states(self):
		board = copy.deepcopy(self.board)
		rotations.append(self.stone)
		#print self.stone
		for i in range(1,3):
			rotations.append(rotate_clockwise(rotations[i - 1]))
		for stone in rotations:
			pass

	"""	def qlearning(self):
		Q=qlearning.QLearningAgent()
		Q.computeActionFromQ"""


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


	def heuristic(self, possboard):
		# print "possboard: ", "\n", possboard, "\n"
		board = np.array(possboard)
		# iterates through entire board determing score based on 
		# 1) If it will remove a row
		# 2) Will there be empty spaces under the placed block
		#print "pass"
		diffsq=[]
		for i in range(1,cols-1):
			diffsq.append(self.difference_squared(possboard,i))
		diffsqsum = sum(diffsq)
		#print "diffsqsum =" +str(diffsqsum)
		avgheight =self.average_height(possboard)
		#print "avgheight =" +str(avgheight)

		score = -(diffsqsum+avgheight-5)
		#print "score = ", score, " diffsqsum = ", diffsqsum, "avgheight =" , avgheight
		#print "Score 1: ", score
		rowcount=[]
		for i in range(rows):
			for x in possboard[i]:
				if x == 0:
					score -= .01
			# Adds for each row that will be removed
			if 0 not in possboard[i]:
				score += 50.0

			# if there are empty spaces underneath spaces filled by block then subtracts one for each instance
			# found because empty spaces under blocks are undesirable
			for j in range(cols):
				if possboard[i][j] != 0:
					y = 0
					while y < (rows - i):

						if possboard[rows - y][j] == 0:
							score -= .01
						y += 1
			#print "score 2= ", score
			if np.count_nonzero(board[i])>0:
				rowcount.append(np.count_nonzero(board[i]))
		if rowcount != []:
			rowcountscore = (2*np.average(rowcount))**5
		else:
			rowcountscore= 0.
		# print "rowcountscore = "+ str(rowcountscore)
		score+=rowcountscore
		#print "Score 2: ", score
		#score += 1000.
		# if score > 0: 
			# print "Score:", score		
		return score


	def get_board_state(self, board):
		
		#print len(board),len(board[0])
		transpose= self.arraytranspose(board)
		#print len(transpose)

		state = []

		for row in transpose:
			# print row
			state.append(next((rows-i for i, x in enumerate(row) if x>0), 0))
		#print state
		row = rows-max(state)

		if max(state) >3:

			array = np.array(board[row:row+4])
			#if array ==[]:
			#	print "error"
			array[array >0] = 1
		else: 
			#print "hi"
			array = np.array(board[rows-4:rows])
			array[array >0] = 1
		#print len(array),len(array[0])
		posed = self.arraytranspose(array)
		finalarray = []
		for row in posed:
			finalarray.append(next((4-i for i, x in enumerate(row) if x>0), 0))
		#print  finalarray
		return finalarray
		
	

	def maxrow(self,board):
		maxval = 0
		for row in board[:len(board)-1]:
			row = np.array(row)
			val = len(row[row>0])
			if val>maxval:
				maxval = val
			#print "val", val
		return maxval


	def arraytranspose(self, board):
		board2 = deepcopy(board)
		# print board2
		board3 = [[0 for i in range(len(board2))] for i in range(len(board2[0]))]
		# print len(board2),len(board2[0])
		# print len(board3),len(board3[0])
		# print len(board),len(board[0])
		for i in range(len(board2[0])):
			for j in range(len(board2)):
				
				#print i,j
				# print i,j, board2[j][i]
				board3[i][j] = board2[j][i]

		# print board3
		return  board3

"""

if __name__ == '__main__':
	App = TetrisApp()
	for i in range(10):
		App.run()
"""