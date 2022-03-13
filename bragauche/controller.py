import pygame

from .dexarmserial import DexArmSerial, Gcode


BLACK = pygame.Color("black")
WHITE = pygame.Color("white")


class Axis:
    def __init__(self, start, coeff, min=-1000, max=1000):
        self.val = start
        self.coeff = coeff
        self.min = min
        self.max = max
        self.modified = False

    def update(self, action):
        val = self.val + action * self.coeff
        self.val = max(min(val, self.max), self.min)
        self.modified = False if action == 0 else True

    def invalidate(self):
        self.modified = False


class RelativeAxis(Axis):
    def update(self, action):
        val = action * self.coeff
        self.val = max(min(val, self.max), self.min)
        self.modified = False if action == 0 else True


class ArmState:
    MAX_HIGH = [0, 300, 0]

    def __init__(self):
        self.x = Axis(self.MAX_HIGH[0], 10)
        self.y = Axis(self.MAX_HIGH[1], 10)
        self.z = Axis(self.MAX_HIGH[2], 5)
        self.r = RelativeAxis(0, 10)
        self.grab = False
        self.push = False
        self.release = False
        self.modified = True

    def update(self, x, y, z, r, grab, push, release):
        self.x.update(x)
        self.y.update(y)
        self.z.update(z)
        self.r.update(r)
        self.modified = (
            self.x.modified
            or self.y.modified
            or self.z.modified
        )
        self.grab = True if grab == 1 else False
        self.push = True if push == 1 else False
        self.release = True if release == 1 and grab == 0 else False

    def invalidate(self):
        self.grab = False
        self.push = False
        self.release = False
        self.modified = False
        self.x.invalidate()
        self.y.invalidate()
        self.z.invalidate()


class Arm:
    BAUDS = 115200

    def __init__(self) -> None:
        self.serial = DexArmSerial()
        self.gcode = Gcode(self.serial)
        self.arm_state = ArmState()

    def open(self, port):
        status = self.serial.open(port, self.BAUDS)
        if status is True:
            self.gcode.init()
            self.gcode.init_rotary()
            self.gcode.XYZ(
                self.arm_state.x.val,
                self.arm_state.y.val,
                self.arm_state.z.val,
            )

    def update(self, x, y, z, r, grab, push, release):
        self.arm_state.update(x, y, z, r, grab, push, release)
        if self.arm_state.r.modified:
            self.gcode.rotate(self.arm_state.r.val)
        if self.arm_state.modified:
            self.gcode.XYZ(
                self.arm_state.x.val,
                self.arm_state.y.val,
                self.arm_state.z.val,
            )
            self.gcode.wait()
        if self.arm_state.grab:
            self.gcode.M100x(0)
        elif self.arm_state.push:
            self.gcode.M100x(1)
        if self.arm_state.release:
            self.gcode.M100x(2)

    def invalidate(self):
        self.arm_state.invalidate()


class ButtonFilter:
    def __init__(self):
        self.value = 0

    def get(self, new_value):
        ret = 0
        if new_value == 1 and self.value == 0:
            ret = 1
        self.value = new_value
        return ret


# This is a simple class that will help us print to the screen.
# It has nothing to do with the joysticks, just outputting the
# information.
class TextPrint(object):
    def __init__(self):
        self.reset()
        self.font = pygame.font.Font(None, 20)

    def tprint(self, screen, textString):
        textBitmap = self.font.render(textString, True, BLACK)
        screen.blit(textBitmap, (self.x, self.y))
        self.y += self.line_height

    def reset(self):
        self.x = 10
        self.y = 10
        self.line_height = 15

    def indent(self):
        self.x += 10

    def unindent(self):
        self.x -= 10


class MainLoop:
    def __init__(self):
        self.done = False
        pygame.init()
        self.grab_ = ButtonFilter()
        self.push_ = ButtonFilter()
        self.release_ = ButtonFilter()
        self.x = 0
        self.y = 0
        self.z = 0
        self.r = 0
        self.grab = 0
        self.push = 0
        self.release = 0
        self.clock = pygame.time.Clock()
        pygame.joystick.init()
        self.screen = pygame.display.set_mode((500, 700))
        pygame.display.set_caption("Bragauche")
        self.text_print = TextPrint()
        self.arm = Arm()
        self.nb_joysticks = 0
        self.joystick = None

    def open(self, port):
        self.arm.open(port)

    def loop(self):
        self.done = False
        while not self.done:
            self.get_joystick()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.done = True
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        self.done = True
            self.joystick_state()
            self.update_arm_state()
            self.draw()
            self.invalidate()
            self.clock.tick(20)

    def get_joystick(self):
        nb_joysticks = pygame.joystick.get_count()
        if self.nb_joysticks != nb_joysticks:
            self.nb_joysticks = nb_joysticks
            self.joystick = None
            for i in range(nb_joysticks):
                joystick = pygame.joystick.Joystick(i)
                joystick.init()
                if "Xbox" in joystick.get_name():
                    self.joystick = joystick
                    break

    def joystick_state(self):
        def axis(i):
            if self.joystick is None:
                return 0
            value = self.joystick.get_axis(i)
            if value > 0.6:
                return 1
            elif value < -0.6:
                return -1
            else:
                return 0

        if self.joystick is None:
            return
        self.x = axis(0)
        self.y = -axis(1)
        self.z = -axis(4)
        self.r = axis(3)
        self.grab = self.grab_.get(self.joystick.get_button(0))
        self.push = self.push_.get(self.joystick.get_button(3))
        self.release = self.release_.get(self.joystick.get_button(1))

    def update_arm_state(self):
        self.arm.update(
            self.x, self.y, self.z, self.r, self.grab, self.push, self.release
        )

    def invalidate(self):
        self.arm.invalidate()

    def __del__(self):
        pygame.quit()

    def draw(self):
        self.screen.fill(WHITE)
        self.text_print.reset()
        name = (
            self.joystick.get_name()
            if self.joystick is not None
            else "Not detected"
        )
        self.text_print.tprint(self.screen, f"bragauche: {name}")
        self.text_print.tprint(self.screen, "")
        self.text_print.tprint(
            self.screen,
            f"Input: X {self.x}, Y {self.y}, Z: {self.z}, R: {self.r}, "
            f"Grab: {self.grab}, Push: {self.push}, Release: {self.release}",
        )
        self.text_print.tprint(
            self.screen,
            f"Arm: X {self.arm.arm_state.x.val}, "
            f"Y {self.arm.arm_state.y.val}, "
            f"Z: {self.arm.arm_state.z.val}, "
            f"R: {self.arm.arm_state.r.val}, "
            f"Grab: {self.arm.arm_state.grab}, "
            f"Push: {self.arm.arm_state.push}, "
            f"Release: {self.arm.arm_state.release}"
        )
        self.text_print.tprint(
            self.screen,
            f"Modified: {self.arm.arm_state.modified}",
        )
        pygame.display.flip()


def control(port):
    mainloop = MainLoop()
    mainloop.open(port)
    mainloop.loop()
    del mainloop
