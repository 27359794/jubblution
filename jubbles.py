import pygame
import random
import math

# Screen details
SCREEN_SIZE = (640, 480)
EDGE_AVOIDANCE = 30
HORIZONTAL_RANGE = (EDGE_AVOIDANCE, SCREEN_SIZE[0]-EDGE_AVOIDANCE)
VERTICAL_RANGE = (EDGE_AVOIDANCE, SCREEN_SIZE[1]-EDGE_AVOIDANCE)
BG_COLOUR = (255, 255, 255)
FRAME_RATE = 60

# Jubble details
DEF_COLOUR = (255, 0, 0)
DEF_SIZE = 10
DEF_ANGLE = 0.0
DEF_SPEED = 1.0
DEF_DETECTION_RADIUS = 60.0

MATURE_AGE = 600.0 # A jubble stops growing after it turns 300
DEATH_AGE = 2000.0 # A jubble dies after it turns 1000

BIRTH_SIZE = 5.0
MATURE_SIZE = 15.0

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

        self.angle = DEF_ANGLE
        self.speed = DEF_SPEED

        self.has_coord_goal = False
        self.goal_x = self.goal_y = None

        self.has_jubble_goal = False
        self.goal_jubble = None

        self.colour = rand_colour()
        self.detection_radius = DEF_DETECTION_RADIUS

        self.age = 0

    def update(self):
        """Update the position and status of the jubble by taking into account
        all relevant details.
        
        Right now, this is limited to checking if we have a goal set for this
        jubble (in which case we move toward that goal), randomly walking and
        making sure we stay within the confines of the map. Also update age.

        """
        # Head toward the jubble goal if the jubble goal is within the detection radius
        if self.has_jubble_goal and \
           dist(self.goal_jubble.get_pos(), self.get_pos()) <= \
           self.detection_radius:
            self.set_coord_goal(self.goal_jubble.x, self.goal_jubble.y)
        
        # Head toward the goal if we have one. Otherwise, do a random walk
        if self.has_coord_goal:
            self.angle = math.atan2(self.goal_y-self.y, self.goal_x-self.x)
        else:
            self.angle += random.uniform(-TURN_ANGLE, TURN_ANGLE)

        # If the distance from here to the goal is shorter than the distance the
        # next move will take you, just move directly to the goal
        distOfNextMove = math.hypot(self.speed * math.cos(self.angle), 
                                    self.speed * math.sin(self.angle))
        if self.has_coord_goal and \
           dist((self.x,self.y), (self.goal_x,self.goal_y)) <= distOfNextMove:
            self.has_coord_goal = False
            self.x = self.goal_x
            self.y = self.goal_y

        # Update the position of the jubble
        self.x += self.speed * math.cos(self.angle)
        self.y += self.speed * math.sin(self.angle)

        # Make sure you stay well on the map
        self.correct_offmap_drift()

        self.age += 1
        
    def set_coord_goal(self, gx, gy):
        """Set an (x,y) goal for the jubble to head toward.

        Both coordinates must be within the bounds of the map or else the goal
        set request will be ignored and a message saying so will be sent to
        stdout.

        """
        if (gx >= HORIZONTAL_RANGE[0] and gx <= HORIZONTAL_RANGE[1]) and\
           (gy >= VERTICAL_RANGE[0] and gy <= VERTICAL_RANGE[1]):
            self.has_coord_goal = True
            self.goal_x = gx
            self.goal_y = gy
        else:
            print 'Invalid goal issued!'

    def set_jubble_goal(self, gj):
        """Set another jubble as a goal for this jubble to head toward.

        This is essentially a coord goal, except it will update the coordinates
        to match whatever the current position of the other jubble is.

        """
        self.has_jubble_goal = True
        self.goal_jubble = gj

    def correct_offmap_drift(self):
        """If you find yourself heading off the map, correct your trajectory."""
        if self.x <= HORIZONTAL_RANGE[0]:  self.angle = ANGLE_RIGHT
        if self.x >= HORIZONTAL_RANGE[1]:  self.angle = ANGLE_LEFT
        if self.y <= VERTICAL_RANGE[0]:    self.angle = ANGLE_DOWN
        if self.y >= VERTICAL_RANGE[1]:    self.angle = ANGLE_UP

    def get_size(self):
        """Get the size of the jubble (in px)."""
        if self.age >= MATURE_AGE:
            return MATURE_SIZE
        else:
            # Get the current age as a fraction of the maturity age, then find
            # this position on the scale from BIRTH_SIZE to MATURE_SIZE
            return self.age / MATURE_AGE * (MATURE_SIZE-BIRTH_SIZE) + BIRTH_SIZE

    def get_pos(self):
        """Get the (x,y) of this jubble."""
        return (self.x, self.y)

    def draw(self):
        """Draw the jubble sprite."""
        pygame.draw.circle(self.screen, self.colour, 
                           self.get_pos(), self.get_size())


def main():
    screen = pygame.display.set_mode(SCREEN_SIZE)
    clock = pygame.time.Clock()

    jubbles = [Jubble(screen) for i in range(3)]
    running = True

    while running:
        # Clear the screen and update jubbles
        screen.fill(BG_COLOUR)
        for j in jubbles:
            j.update()
            j.draw()
            # Set jubbles on other jubbles
            for oj in jubbles:
                if j is not oj and \
                   dist(j.get_pos(), oj.get_pos()) <= j.detection_radius:
                    j.set_jubble_goal(oj)
        
        for e in pygame.event.get():
            # If we receive a quit event (window close), stop running
            if e.type == pygame.QUIT:
                running = False
            # If we receive a mouse click, set a coordinate goal for our jubble
            # at the position of the click
            elif e.type == pygame.MOUSEBUTTONDOWN:
                for j in jubbles:
                    j.set_coord_goal(*e.pos)
                
        # Refresh the display
        pygame.display.flip()
        clock.tick(FRAME_RATE)


def blueMoon(chance):
    """Returns true with a probability of `chance`."""
    return random.random() < chance


def rand_colour():
    return tuple(random.randrange(0, 256) for i in range(3))

def dist(a, b):
    """Get the Euclidean distance between two points on the plane."""
    return math.hypot(a[0]-b[0], a[1]-b[1])


main()
