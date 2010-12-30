# TODO: currently, a jubble can only detect jubbles whose *centres* are within
# the first jubble's viewing range. fix this!

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
DEF_DETECTION_SLICE = math.pi/2  # A jubble can see in a 90deg angle ahead

MATURE_AGE = 600.0  # A jubble stops growing after it turns 300
############ DEBUG
DEATH_AGE = 20000.0  # A jubble dies after it turns 1000

BIRTH_SIZE = 5.0
MATURE_SIZE = 15.0

TURN_ANGLE = math.pi / 7
CHANCE_OF_TURN = 0.1

DEATH_COLOUR = (220, 220, 220)
VIEWING_ANGLE_LINE_COLOUR = (200, 200, 200)

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

        # Randomly initialise its colour
        self.colour = rand_colour()

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

        # TODO: get rid of this debugging
        self.old_goal_jubble_position = None

    def update(self):
        """Update the position and status of the jubble by taking into account
        all relevant details.
        
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
        """If the jubble we're aiming for is alive and in range, chase it.

        If the target is dead or not within range, remove the goal.
        Otherwise, if we can chase it, set it as our coordinate goal.

        Assumes we have a jubble goal already.

        """
        assert self.has_jubble_goal

        if self.goal_jubble.isAlive and self.can_chase_jubble(self.goal_jubble):
            self.set_coord_goal(self.goal_jubble.x, self.goal_jubble.y)
        else:
            self.has_jubble_goal = False

    def _handle_coord_goal(self):
        """Go toward the coord goal. If we've reached it, remove the goal.

        Assumes we have a coord goal already.

        """
        assert self.has_coord_goal

        self.angle = to_polar(self.goal_x-self.x, self.goal_y-self.y)[0]

        if self.has_coord_goal and \
           dist((self.x,self.y), (self.goal_x,self.goal_y)) <= self.speed:
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
            self.kill()

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

    def will_fight_with_jubble(self, other):
        """Determine whether this jubble is willing to fight with another.

        Currently, a jubble will only fight with jubbles younger or the same age
        as this one. Later it will depend on courage, our size, the other
        jubble's size, etc.

        Note that this function MUST BE DETERMINISTIC. It will be evaluated
        every frame, so if a jubble sees an opponent repeatedly in several
        consecutive frames it should make the same choice every time.

        """
        return self.age >= other.age

    def will_win_against_jubble(self, other):
        """Determine whether this jubble will win a fight against another
        jubble.

        Currently, the winner has to be a) older than the other and b) can
        detect the other (to prevent accidental kills).

        Note that unlike the 'will fight with jubble' function, this one can be
        non-deterministic as it will only happen once between two jubbles.

        """
        return self.age >= other.age and self.can_detect_jubble(other)

    def can_chase_jubble(self, other):
        """Decide whether another jubble can be chased.

        Once a jubble has been detected, it does not have to be in this jubble's
        field of vision to be chased. It merely has to be within the dist
        bounds.

        """
        return self._coord_in_range(*other.get_pos())

    def _can_detect_coord(self, ox, oy):
        """Determine if this jubble is able to detect a specific point.

        Factors in the distance of the point and whether the point falls within
        the jubble's viewing field.

        """
        left_edge = self.angle - DEF_DETECTION_SLICE / 2
        right_edge = self.angle + DEF_DETECTION_SLICE / 2
        angle_of_self_to_point = to_polar(ox - self.x, oy - self.y)[0]

        return self._coord_in_range(ox, oy) and \
               left_edge <= angle_of_self_to_point <= right_edge

    def _coord_in_range(self, ox, oy):
        """Determine whether a coordinate is in the dist range of the jubble."""
        return dist(self.get_pos(), (ox,oy)) <= self.detection_radius

    def colliding_with_jubble(self, other):
        """Determine whether this jubble is currently colliding with another."""
        return self.isAlive and other.isAlive and \
               circles_are_touching(self.get_pos(), other.get_pos(),
                                    self.get_radius(), other.get_radius())

    def kill(self):
        """Kill this jubble and set all relevant attributes to reflect this."""
        self.isAlive = False
        self.colour = DEATH_COLOUR

    def _correct_offmap_drift(self):
        """If you find yourself heading off the map, correct your trajectory."""
        if self.x <= HORIZONTAL_RANGE[0]:  self.angle = ANGLE_RIGHT
        if self.x >= HORIZONTAL_RANGE[1]:  self.angle = ANGLE_LEFT
        if self.y <= VERTICAL_RANGE[0]:    self.angle = ANGLE_DOWN
        if self.y >= VERTICAL_RANGE[1]:    self.angle = ANGLE_UP

    def get_radius(self):
        """Get the size of the jubble's radius (in px)."""
        if self.age >= MATURE_AGE:
            return MATURE_SIZE
        else:
            # Get the current age as a fraction of the maturity age, then find
            # this position on the scale from BIRTH_SIZE to MATURE_SIZE
            return self.age / MATURE_AGE * (MATURE_SIZE-BIRTH_SIZE) + BIRTH_SIZE

    def get_pos(self):
        """Get the (x,y) position of this jubble."""
        return (self.x, self.y)

    def draw(self, overriding_colour=None):
        """Draw the jubble sprite.
        
        The `colour` keyword argument allows for all the jubble's colours to be
        overwritten with a single colour.

        """
        if overriding_colour is not None:
            # A colour has been specified that overrides the defaults.
            # Use that colour for everything, instead of the defaults
            self._draw_viewing_angle(overriding_colour)
            if self.isAlive and self.has_jubble_goal:
                self._draw_jubble_goal(overriding_colour)
            self._draw_body(overriding_colour)
            self._draw_nose(overriding_colour)
        else:
            self._draw_viewing_angle(VIEWING_ANGLE_LINE_COLOUR)
            if self.isAlive and self.has_jubble_goal:
                self._draw_jubble_goal((255, 0, 0))
            self._draw_body(self.colour)
            self._draw_nose(self.colour)

    def _draw_body(self, colour):
        """Draw the jubble's body."""
        pygame.draw.circle(
            self.screen, colour,
            self.get_pos(), self.get_radius())

    def _draw_nose(self, colour):
        """Draw the jubble's 'nose'"""
        nose_x, nose_y = to_cartesian(self.angle, self.get_radius())

        pygame.draw.line(
            self.screen, colour,
            self.get_pos(),
            (self.x + NOSE_TO_BODY*nose_x, self.y + NOSE_TO_BODY*nose_y),
            NOSE_WIDTH)

    def _draw_viewing_angle(self, colour):
        """Draw the lines representing the jubble's viewing angle."""
        left_x, left_y = to_cartesian(self.angle - DEF_DETECTION_SLICE / 2, 100)
        right_x, right_y = to_cartesian(self.angle + DEF_DETECTION_SLICE / 2, 100)

        # Draw the left line of the viewing angle
        pygame.draw.line(
            self.screen, colour,
            self.get_pos(),
            (self.x + left_x, self.y + left_y),
            2)

        # Draw the right line of the viewing angle
        pygame.draw.line(
            self.screen, colour,
            self.get_pos(),
            (self.x + right_x, self.y + right_y),
            2)

    def _draw_jubble_goal(self, colour):
        """Draw a line representing the jubble this jubble is targetting.

        LOADS of debugging stuff here. TODO: get rid of it"""
        

        pygame.draw.line(
            self.screen, colour,
            self.get_pos(),
            self.goal_jubble.get_pos() if self.old_goal_jubble_position is None \
            else self.old_goal_jubble_position,
            1)
        self.old_goal_jubble_position = self.goal_jubble.get_pos()

    def erase(self):
        """Fill in the jubble's current position with the background colour."""
        self.draw(overriding_colour=BG_COLOUR)


def main():
    screen = pygame.display.set_mode(SCREEN_SIZE)
    pygame.display.set_caption("Jubblution")
    clock = pygame.time.Clock()

    screen.fill(BG_COLOUR)

    jubbles = [Jubble(screen)]
    running = True

    while running:
        update_jubbles(jubbles)
                
        # Refresh the display
        pygame.display.flip()
        clock.tick(FRAME_RATE)

        for e in pygame.event.get():
            # If we receive a quit event (window close), stop running
            if e.type == pygame.QUIT:
                running = False
            # If we receive a mouse click, set a coordinate goal for our jubble
            # at the position of the click
            elif e.type == pygame.MOUSEBUTTONDOWN:
                for j in jubbles:
                    j.set_coord_goal(*e.pos)

        # Add a new jubble for the first 10 frames
        if len([j for j in jubbles if j.isAlive]) < 10:
            jubbles.append(Jubble(screen))


def update_jubbles(jubbles):
    # Update jubbles and redraw them
    for j in jubbles:
        j.erase()
        j.update()
        j.draw()

        for oj in jubbles:
            if j.isAlive and oj.isAlive and j is not oj:
                # Set chases
                if j.can_detect_jubble(oj) and \
                   j.will_fight_with_jubble(oj) and \
                   not j.has_jubble_goal:
                    j.set_jubble_goal(oj)

        # Set combats / defeats
        if j.has_jubble_goal and j.colliding_with_jubble(j.goal_jubble):
            if j.will_win_against_jubble(j.goal_jubble):
                j.goal_jubble.kill()


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

def circles_are_touching(centre1, centre2, radius1, radius2):
    """Determine if two circles of different radii intersect.

    Two circles intersect if the Euclidean distance between their origins is
    less than or equal to the sum of their radii.

    """
    return dist(centre1, centre2) <= radius1 + radius2

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
