import pygame
import random
import math

# Screen details
SCREEN_SIZE = (640, 480)
EDGE_AVOIDANCE = 30
HORIZONTAL_RANGE = (EDGE_AVOIDANCE, SCREEN_SIZE[0]-EDGE_AVOIDANCE)
VERTICAL_RANGE = (EDGE_AVOIDANCE, SCREEN_SIZE[1]-EDGE_AVOIDANCE)
BG_COLOUR = (255, 255, 255)
FRAME_RATE = 100

# Jubble details
DEF_COLOUR = (255, 0, 0)
DEF_SIZE = 10
TURN_ANGLE = math.pi / 10

# Misc details
ANGLE_RIGHT = 0.0
ANGLE_UP = math.pi * 1.5
ANGLE_LEFT = math.pi
ANGLE_DOWN = math.pi / 2


class Jubble(object):

    """A jubble."""

    def __init__(self, screen):
        self.screen = screen

        self.x = random.randrange(*HORIZONTAL_RANGE)
        self.y = random.randrange(*VERTICAL_RANGE)

        self.angle = 0.0
        self.speed = 1.0

        self.has_goal = False
        self.goal_x = 0
        self.goal_y = 0

    def update(self):
        if self.has_goal:
            # Head toward our goal
            self.angle = math.atan2(self.goal_y-self.y,
                                    self.goal_x-self.x)
        else:
            # Do a random walk
            self.angle += random.uniform(-TURN_ANGLE, TURN_ANGLE)

        # If the distance from here to the goal is shorter than the distance the
        # next move will take you, just move directly to the goal
        distOfNextMove = math.hypot(self.speed * math.cos(self.angle), 
                                    self.speed * math.sin(self.angle))
        if self.has_goal and \
           dist((self.x,self.y), (self.goal_x,self.goal_y)) <= distOfNextMove:
            self.has_goal = False
            self.x = self.goal_x
            self.y = self.goal_y

        # Update the position of the jubble
        self.x += self.speed * math.cos(self.angle)
        self.y += self.speed * math.sin(self.angle)

        # Make sure you stay well on the map
        self.correct_offmap_drift()
        
    def set_coord_goal(self, gx, gy):
        """Set an (x,y) goal for the jubble to head toward.

        Both coordinates must be positive, both because this makes logical sense
        (i.e. you never want to go somewhere off the surface of the earth unless
        you're an astronaut) and because arctan only likes it this way.

        Both coordinates should also be within the bounds of earth.

        """
        # If the goal is in bounds, set it
        # Otherwise, print an error to stdout
        if (gx >= HORIZONTAL_RANGE[0] and gx <= HORIZONTAL_RANGE[1]) and\
           (gy >= VERTICAL_RANGE[0] and gy <= VERTICAL_RANGE[1]):
            self.has_goal = True
            self.goal_x = gx
            self.goal_y = gy
        else:
            print 'Invalid goal issued!'

    def correct_offmap_drift(self):
        """If you find yourself heading off the map, correct your trajectory."""
        if self.x <= HORIZONTAL_RANGE[0]:  self.angle = ANGLE_RIGHT
        if self.x >= HORIZONTAL_RANGE[1]:  self.angle = ANGLE_LEFT
        if self.y <= VERTICAL_RANGE[0]:    self.angle = ANGLE_DOWN
        if self.y >= VERTICAL_RANGE[1]:    self.angle = ANGLE_UP

    def draw(self):
        """Draw the jubble sprite."""
        pygame.draw.circle(self.screen, DEF_COLOUR, (self.x, self.y), DEF_SIZE)


def main():
    screen = pygame.display.set_mode(SCREEN_SIZE)
    clock = pygame.time.Clock()

    jubble1 = Jubble(screen)

    running = True

    while running:
        # clear screen
        screen.fill(BG_COLOUR)

        # update jubbles
        jubble1.update()
        jubble1.draw()
        
        # check for quit event
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False

            elif e.type == pygame.MOUSEBUTTONDOWN:
                jubble1.set_coord_goal(*e.pos)
                
        # refresh display
        pygame.display.flip()
        clock.tick(FRAME_RATE)


def blueMoon(chance):
    return random.random() < chance


def dist(a, b):
    return math.hypot(a[0]-b[0], a[1]-b[1])


main()
