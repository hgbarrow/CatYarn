import math, os, pygame, random, pickle
from pygame.locals import *

""" CatYarn! by Henry Barrow """
# Check to see if program is running on android
try:
	import android
except ImportError:
	android = None

# Use pygame mixer on pc, android mixer on android - for sounds
try:
	import pygame.mixer as mixer
except ImportError:
	import android.mixer as mixer

# Set screen resolution
SCREENRECT = Rect(0, 0, 720, 1000)
if android:
	SCREENRECT = Rect(0, 0, 720, 1280)

# image dictionary - paths: images
_image_library = {}
# initialize image if it has never been used before, otherwise return image
def get_image(path):
	global _image_library
	image = _image_library.get(path)
	if image == None:
		canonicalized_path = path.replace('/', os.sep).replace('\\', os.sep)
		image = pygame.image.load(canonicalized_path).convert_alpha()
		_image_library[path] = image
	return image


#create sound library  - similar to image library
_sound_library = {}
def play_sound(path):
	global _sound_library
	sound  = _sound_library.get(path)
	if sound == None:
		canonicalized_path = path.replace('/', os.sep).replace('\\', os.sep)
		sound = mixer.Sound(canonicalized_path)
		_sound_library[path] = sound
	clock = pygame.time.Clock()
	sound.play()
	

def play_music(path, play_cnt):
	"""This function plays music a given number of times, -1 means loop"""
	canonicalized_path = path.replace('/', os.sep).replace('\\', os.sep)
	mixer.music.load(canonicalized_path)
	mixer.music.play(play_cnt)
	return 1
	
class Cat(pygame.sprite.Sprite):
	"""Cat Sprite"""
	
	def __init__(self):
		pygame.sprite.Sprite.__init__(self, self.containers)
		self.image = self.play_image
		self.rect = self.image.get_rect()
		
		# make a hitbox that is smaller than the sprite rectangle
		self.hbox = self.rect.inflate(-90, -100)
		self.rect.centerx = SCREENRECT.centerx
		self.rect.bottom = SCREENRECT.bottom - 100
		self.img_src = self.image
		
		# set maximum movement speed
		self.maxdx = 13
		self.dead = False
	
	def update(self):
		# android mouse position is (0, 0) when finger is lifted
		if pygame.mouse.get_pos() == (0,0) and android:
			self.image = self.img_src
		else:
			mousex = pygame.mouse.get_pos()[0]
			mousey = pygame.mouse.get_pos()[1]
		
			# Rotate cat so she is following the mouse (or finger)
			center = self.rect.center
			if center[1] - mousey == 0: angle = 0
			else: angle = -(180/math.pi) * math.atan(float(mousex - center[0])/(center[1] -mousey))
		
			if self.dead:
				# change cat sprite and move toward the top of the screen
				self.img_src = self.again_image
				self.rect = self.image.get_rect()
				self.rect.top = SCREENRECT.top + 200

				
			rotimage = pygame.transform.rotate(self.img_src, angle)
			rotrect = rotimage.get_rect(center=self.rect.center)
			self.image = rotimage
			self.rect = rotrect
			self.rect.centerx = center[0]
			
			#Speed up cat on PC when RMB is held
			if not android:
				if pygame.mouse.get_pressed()[2] == 1:
					self.maxdx = 20
				else: self.maxdx = 13
			
			#Move cat toward mouse position
			if mousex > self.rect.centerx:
				dx = min(self.maxdx, mousex - self.rect.centerx)
				self.rect.centerx += dx
			else:
				dx = min(self.maxdx, self.rect.centerx - mousex)
				self.rect.centerx -= dx
		
		#Update the hitbox
		self.hbox = self.rect.inflate(-90, -100)
		self.hbox.center = self.rect.center
		
		
	

	
class Yarn(pygame.sprite.Sprite):
	speed = 14
	angleleft = 135
	angleright = 45
	
	def __init__(self):
		pygame.sprite.Sprite.__init__(self, self.containers)
		self.rect = self.image.get_rect()
		self.update = self.start
		self.dx = 0
		self.dy = 0
		
		# start yarn in a random position on the top of the screen
		self.rect.centerx = random.randint(1, SCREENRECT.width)
	def start(self):
		self.rect.top = SCREENRECT.top
		
		# Decide if yarn should drop
		if pygame.mouse.get_pressed()[0] ==1 or (self.score.score > 0):
			self.setfp()
			self.dx = 0
			self.dy = self.speed
			self.update = self.move
			
	def setfp(self):
		self.fpx = float(self.rect.centerx)
		self.fpy = float(self.rect.centery)
		
	def setint(self):
		self.rect.centerx = int(round(self.fpx))
		self.rect.centery = int(round(self.fpy))
		
	def move(self):
		#check for cat:yarn collision
		if self.rect.colliderect(self.cat.hbox) and self.dy > 0:
			x1 = self.cat.hbox.right
			y1 = self.angleright
			x2 = self.cat.hbox.left - (self.rect.width - 1)
			y2 = self.angleleft
			x = self.rect.left
			m = float(y2-y1)/(x2 - x1)
			y = m*(x - x1) + y1
			angle = math.radians(y)
			self.dx = self.speed*math.cos(angle)
			self.dy = -self.speed*math.sin(angle)
			
			if self.score != 0: self.score.update()
			
			if float(self.score.score) % 10 == 0 and self.score.score != 0:
				yrn_list = self.yarns.sprites()
				for i in range(len(yrn_list)):
					yrn_list[i].speed += 2
					print yrn_list[i].speed
			
		self.fpx = self.fpx + self.dx
		self.fpy = self.fpy + self.dy
		self.setint()
		
		# Decide what happens when yarn wants to go off-screen
		if not SCREENRECT.contains(self.rect):
			if self.rect.bottom > SCREENRECT.bottom:
				self.kill()
				self.score.lifechange()
			
			else:
				if self.rect.left < SCREENRECT.left or self.rect.right > SCREENRECT.right:
					self.dx = -self.dx
				if self.rect.top < SCREENRECT.top:
					self.dy = -self.dy
				self.rect.clamp_ip(SCREENRECT)
				self.setfp()
		
		#check for yarn - yarn collision
		if len(self.yarns.sprites()) > 1:
			yrn_hit_list = pygame.sprite.spritecollide(self, self.yarns, \
							False, pygame.sprite.collide_rect_ratio(0.6))
			if len(yrn_hit_list) >= 2:
				for i in range(0, len(yrn_hit_list)):
						yrn_hit_list[i].dx = -yrn_hit_list[i].dx
						yrn_hit_list[i].dy = -yrn_hit_list[i].dy
				

class Sound(pygame.sprite.Sprite):
	""" Class for sound and mute button"""
	def __init__(self):
		pygame.sprite.Sprite.__init__(self, self.containers)
		
		if not self.muted:
			play_music('data\Who Likes to Party.mp3', -1)
			self.image = self.unmuted_image
		else:
			self.image = self.muted_image
			
		self.rect = self.image.get_rect()
		self.rect.right = SCREENRECT.right - 15
		self.rect.top = 40	
	def update(self):
		pass
	
	def toggle(self):
		self.muted = not self.muted
		if self.muted:
			self.image = self.muted_image
			mixer.music.pause()
		else:
			self.image = self.unmuted_image
			mixer.music.play()
			
		
		
class Score(object):
	""" Object to keep track of the score """
	def __init__(self, hi_score):
		self.score = 0
		self.lives = 9
		self.hi_score = hi_score
		self.img = self.font.render(str(self.score), True, (0, 255, 0))
		self.img_life = self.font.render(str(self.lives), True, (255, 0, 0))
		self.img_hi = self.font.render(str(self.hi_score), True, (0, 0, 255))
		
	def update(self):
		self.score += 1
		
		#check if hi score has been beat
		if self.score > self.hi_score:
			self.hi_score = self.score
			self.img_hi = self.font.render(str(self.hi_score), True, (0, 0, 255))
			
		
		#play random sound
		if not self.sound.muted:
			randsoundfile = 'data\cat_%d.wav' % random.randint(1, 6)
			play_sound(randsoundfile)
		
		#Re-render score image
		self.img = self.font.render(str(self.score), True, (0, 255, 0))
		if self.score % 5 == 0 and self.score != 0:
			Yarn()
	def lifechange(self):
		self.lives -= 1
		self.img_life = self.font.render(str(self.lives), True, (255, 0, 0))
		self.just_died = True
		if android:
			android.vibrate(0.3)
		
def main():
	pygame.init()
	screen = pygame.display.set_mode(SCREENRECT.size)
	
	if android:
		android.init()
		android.map_key(android.KEYCODE_BACK, pygame.K_ESCAPE)
	
	# Define image and song locations
	Cat.play_image = get_image("data\marie_small.png")
	Cat.again_image = get_image("data\marie_again.png")
	Yarn.image = get_image('data\yarn_new.png')
	Sound.unmuted_image = get_image("data\sound_on.png")
	Sound.muted_image = get_image("data\sound_off.png")
	
	pygame.display.set_icon(get_image('data\marie_square.png'))
	pygame.display.set_caption('CatYarn!')
	play_music('data\Who Likes to Party.mp3', -1)
	mixer.music.pause()
	
	#load Hi Score and sound info
	savefile = 'data\save.dat'
	try:
		with open(savefile, 'rb') as file:
			hi_score = pickle.load(file)
			Sound.muted = pickle.load(file)
	except:
		hi_score = 0
		Sound.muted = False
		
	#make background
	background = pygame.Surface(SCREENRECT.size).convert()
	background.fill((0, 0, 255))
	
	# Currently backgrounds are the same, but could depend on platform
	if android:
		yarn_bg = get_image('data\BG_android.jpg')
	else: 
		yarn_bg = get_image('data\BG_android.jpg')
	
	# Screen Blit background
	screen.blit(yarn_bg, (0, 0))
	pygame.display.update()
	
	#keep track of sprites - lump them into groups
	yarns = pygame.sprite.Group()
	Yarn.yarns = yarns
	
	all = pygame.sprite.RenderUpdates()
	
	Cat.containers = all
	Yarn.containers = all, yarns
	Sound.containers = all
	
	#keep track of time
	clock = pygame.time.Clock()
	
	# Generate sprites
	cat = Cat()
	Yarn.cat = cat #feed yarn object cat information
	yarn = Yarn()
	Cat.yarn = yarn #feed cat object yarn information
	sound = Sound()
	
	#Sent font and render static text
	font = pygame.font.Font('vademecum.ttf', 80)
	scoretext = font.render('Score: ', True, (0, 255, 0))
	livestext = font.render('Lives: ', True, (255, 0, 0))
	hitext = font.render('Hi: ', True, (0, 0, 255))
	Score.font = font
	
	Score.sound = sound
	score = Score(hi_score)
	#score.update()
	
	Yarn.score = score #feed score to yarn - for new yarns dropping after 3 hit
	
	#game loop
	while 1:
		
		if android:
			if android.check_pause():
				android.wait_for_resume()
		
		# get input
		for event in pygame.event.get():
			if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
				with open(savefile, 'wb') as file: #Save Hi Score
					pickle.dump(score.hi_score, file)
					pickle.dump(sound.muted, file)
				return
			if event.type == KEYDOWN and event.key == K_F11: #toggle fullscreen if F11 is pressed
				flags = screen.get_flags()
				screen = pygame.display.set_mode(SCREENRECT.size, flags^FULLSCREEN)
				screen.blit(yarn_bg, (0, 0))
				
			if event.type == KEYDOWN and event.key == K_SPACE: #reset game if space is pressed
				score.lives = 0
				score.just_died = True
				
			if event.type == MOUSEBUTTONDOWN and sound.rect.collidepoint(pygame.mouse.get_pos()):
				sound.toggle()
		#clear sprites
		all.clear(screen, background)
		
		
		# if you lost a yarn but still have lives:
		if len(yarns.sprites()) < 1 and score.lives > 0:
			Yarn()
		
		# Game Over events
		if score.lives == 0:
			if score.just_died:
				mixer.music.stop()
				if not sound.muted:	
					play_sound('data\cat_fail.wav')
				for yrn in yarns:
					yrn.kill()
				score.just_died = False
				cat.dead = True
				
				
			if pygame.mouse.get_pressed()[0] ==1: #if mouse clicked start a new game
				if cat.rect.collidepoint(pygame.mouse.get_pos()):
					if not sound.muted:
						mixer.music.play()
						
					score.score = -1
					score.update()
					score.lives = 10
					score.lifechange()
					Yarn()
					cat.__init__()
			
		# redraw sprites
		all.update()
		
		#redraw sprites
		screen.blit(yarn_bg, (0,0))
		dirty = all.draw(screen)
		scorerect = screen.blit(scoretext, (20, 0))
		scoreprint = screen.blit(score.img, (scorerect.width + 20, 0))
		livesprint = screen.blit(livestext, (20, scoreprint.bottom))
		livesrect = screen.blit(score.img_life, (livesprint.right, scoreprint.bottom))
		hiprint = screen.blit(hitext, (20, livesrect.bottom))
		hinum = screen.blit(score.img_hi, (hiprint.right, livesrect.bottom))
		
		#pygame.draw.rect(screen, (255, 0, 0), cat.hbox, 1) #draw hitbox for debugging
		pygame.display.flip()
		
		# maintain frame rate
		clock.tick(60)
		
		#Uncomment next line to display FPS in window title
		#pygame.display.set_caption('CatYarn!      FPS: '+ str(clock.get_fps()))
		
		
if __name__ == "__main__":
    main()