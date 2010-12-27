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
DEF_ANGLE = 0.0
DEF_SPEED = 1.0
DEF_DETECTION_RADIUS = 150.0
DEF_DETECTION_SLICE = math.pi  # A jubble can see in a 180deg angle ahead

MATURE_AGE = 600.0  # A jubble stops growing after it turns 300
DEATH_AGE = 2000.0  # A jubble dies after it turns 1000

BIRTH_SIZE = 5.0
MATURE_SIZE = 15.0

TURN_ANGLE = math.pi / 7
CHANCE_OF_TURN = 0.1

DEATH_COLOUR = (0,0,0)

# Misc details
ANGLE_RIGHT = 0.0
ANGLE_UP = math.pi * 1.5
ANGLE_LEFT = math.pi
ANGLE_DOWN = math.pi / 2

NOSE_TO_BODY = 1.4
NOSE_WIDTH = 3


class Jubble(object):

    """A jubble."""

    def __init__(self, screen):
        self.screen = screen

        # Randomly initialise its location
        self.x = random.randrange(*HORIZONTAL_RANGE)
        self.y = random.randrange(*VERTICAL_RANGE)

        # Set its trajectory, speed and detection radius to the defaults
        self.angle = DEF_ANGLE
        self.speed = DEF_SPEED
        self.detection_radius = DEF_DETECTION_RADIUS
        self.age = 0
        self.isAlive = True

        # It currently has no goals
        self.has_coord_goal = False
        self.has_jubble_goal = False
        self.goal_x = self.goal_y = None
        self.goal_jubble = None

        # Randomly initialise its colour
        self.colour = rand_colour()

    def update(self):
        """Update the position and status of the jubble by taking into account
        all relevant details.
        
        Right now, this is limited to checking if we have a goal set for this
        jubble (in which case we move toward that goal), randomly walking and
        making sure we stay within the confines of the map. Also update age.

        """
        if self.isAlive:
            # Head toward the jubble goal if the jubble goal is within the
            # detection radius
            if self.has_jubble_goal:
                self._handle_jubble_goal()
        
            # Head toward the goal if we have one. Otherwise, do a random walk
            if self.has_coord_goal:
                self._handle_coord_goal()
            elif blueMoon(CHANCE_OF_TURN):
                self._add_random_angle_shift()

            self._move_one_unit()
            self._get_older()

    def _handle_jubble_goal(self):
        """If the jubble we're aiming for is in our range, chase it."""
        if self.can_detect_jubble(self.goal_jubble):
            self.set_coord_goal(self.goal_jubble.x, self.goal_jubble.y)

    def _handle_coord_goal(self):
        """Go toward the coord goal. If we've reached it, remove the goal."""
        self.angle = to_polar(self.goal_x-self.x, self.goal_y-self.y)[0]

        if self.has_coord_goal and \
           dist((self.x,self.y), (self.goal_x,self.goal_y)) <= self.speed:
            print 'Goal reached!'
            self.has_coord_goal = False
            self.x = self.goal_x
            self.y = self.goal_y

    def _add_random_angle_shift(self):
        """Add some random noise to the current trajectory."""
        self.angle += random.uniform(-TURN_ANGLE, TURN_ANGLE)
        
    def _move_one_unit(self):
        """Update the position of the jubble.

        If we're heading off the map, correct the angle.

        """
        change_x, change_y = to_cartesian(self.angle, self.speed)
        self.x, self.y = self.x + change_x, self.y + change_y
        
        self._correct_offmap_drift()

    def _get_older(self):
        """Age the jubble by one frame's worth."""
        self.age += 1
        if self.age >= DEATH_AGE:
            self.isAlive = False
            self.colour = DEATH_COLOUR

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

    def can_detect_jubble(self, other):
        """Determine if this jubble is able to detect another jubble."""
        return self._can_detect_coord(*other.get_pos())

    def _can_detect_coord(self, ox, oy):
        """Determine if this jubble is able to detect a specific point.

        Factors in the distance of the point and whether the point falls within
        the jubble's viewing field.

        """
        left_edge = self.angle - DEF_DETECTION_SLICE / 2
        right_edge = self.angle + DEF_DETECTION_SLICE / 2
        angle_of_self_to_point = to_polar(ox - self.x, oy - self.y)[0]

        return dist(self.get_pos(), (ox,oy)) <= self.detection_radius and \
            left_edge <= angle_of_self_to_point <= right_edge
            

    def _correct_offmap_drift(self):
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
        size = self.get_size()

        # Draw the body
        pygame.draw.circle(self.screen, self.colour, 
                           self.get_pos(), size)

        # Draw the nose
        nose_x, nose_y = to_cartesian(self.angle, size)
        pygame.draw.line(
            self.screen, self.colour,
            (self.x, self.y),
            (self.x + NOSE_TO_BODY*nose_x, self.y + NOSE_TO_BODY*nose_y),
            NOSE_WIDTH)


### Main-loop

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
                if j is not oj and j.can_detect_jubble(oj):
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
    """Generate a random RGB colour in tuple format."""
    return tuple(random.randrange(0, 256) for i in range(3))


### Geometry stuff

def dist(a, b):
    """Get the Euclidean distance between two points on the plane."""
    return math.hypot(a[0]-b[0], a[1]-b[1])

def to_polar(x, y):
    """Converts (x, y) to (angle, magnitude)."""
    return (math.atan2(y, x), math.hypot(x, y))

def to_cartesian(angle, magnitude):
    """Converts (angle, magnitude) to (x, y)."""
    return (magnitude * math.cos(angle), magnitude * math.sin(angle))
'''
def point_left_of_line(origin, linepoint, querypoint):
    """Determine if a query point is CCW to the line `origin`->`linePoint`."""
    relative_linepoint = (linePoint[0] - origin[0], linePoint[1] - origin[1])
    relative_querypoint = (queryPoint[0] - origin[0], queryPoint[1] - origin[1])

    return cross_product(relative_linepoint, relative_querypoint) >= 0
    
def cross_product(a, b):
    """Find the cross-product of two vectors."""
    return a[0] * b[1] - b[0] * a[1]
'''

main()
