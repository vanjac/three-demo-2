
def makePlayer():
    forwardButtonAxis = ButtonAxis(world.buttonInputs['w'], 0.0, 1.0)
    backButtonAxis = ButtonAxis(world.buttonInputs['s'], 0.0, 1.0)
    leftButtonAxis = ButtonAxis(world.buttonInputs['a'], 0.0, 1.0)
    rightButtonAxis = ButtonAxis(world.buttonInputs['d'], 0.0, 1.0)
    
    xWalkAxis = AxisSum(rightButtonAxis, AxisOpposite(leftButtonAxis))
    yWalkAxis = AxisSum(forwardButtonAxis, AxisOpposite(backButtonAxis))
    
    player = FirstPersonPlayer( world,
                                AxisScale(world.axisInputs['mouse-x'], .005),
                                AxisScale(world.axisInputs['mouse-y'], .005),
                                xWalkAxis, yWalkAxis,
                                world.buttonInputs['space'],
                                walkSpeed = 50.0, fallMoveSpeed = 15.0,
                                jumpVelocity = 60.0, walkDeceleration=.001,
                                fallDeceleration=.7)
    world.camera = player
    return player

def use():
    cam = world.camera
    
    def getMeshCallback(mesh, face):
        if mesh is not None:
            mesh.doUseAction()
            
    world.getFaceAtRay( getMeshCallback, cam.getPosition(),
                        Vector(1.0, 0.0, 0.0).rotate(cam.getRotation()) )

class UseScanner(SimObject):

    def __init__(self, button):
        self.button = button

    def scan(self, timeElapsed, totalTime):
        event = self.button.getEvent()
        if event == ButtonInput.PRESSED_EVENT:
            use()

world.simulator.addObject(UseScanner(world.buttonInputs['mouse-left']))


world.score = 0

def addScore(score):
    world.score += score
    print(score, "points!")
    print("Score:", world.score)

class Coin(Entity):

    def scan(self, timeElapsed, totalTime):
        def do(toUpdateList):
            self.rotate(Rotate(0, 0, timeElapsed * 3))
            toUpdateList.append(self)
        self.actions.addAction(do)

    def coinCollide(self):
        self.kill(True)
        addScore(100)

class Platform(Entity):

    def __init__(self, movement, cycleTime):
        super().__init__()
        self.movement = movement
        self.cycleTime = cycleTime
        self.started = False
        self.startTime = None
        self.startPosition = None

    def start(self):
        self.started = True

    def scan(self, timeElapsed, totalTime):
        if self.started and self.startTime == None:
            self.startTime = totalTime
            self.startPosition = self.position
        cycle = math.cos((totalTime - self.startTime)
                         / self.cycleTime * math.pi*2) / 2 + .5
        position = self.startPosition.lerp(
            self.startPosition + self.movement, cycle)
        def do(toUpdateList):
            self.translate(position - self.position)
            toUpdateList.append(self)
        self.actions.addAction(do)
            
    def end(self):
        self.started = False
        self.startTime = None

    def startTouch(self):
        global world
        self.addChild(world.camera)

    def endTouch(self):
        global world
        self.removeChild(world.camera)

class FallingPlatform(Entity):

    def __init__(self):
        super().__init__()
        self.falling = False
        self.zVel = 0

    def startFalling(self):
        self.falling = True

    def scan(self, timeElapsed, totalTime):
        def do(toUpdateList):
            if self.falling:
                self.zVel += FirstPersonPlayer.GRAVITY * timeElapsed
            self.translate(Vector(0, 0, self.zVel * timeElapsed))
            toUpdateList.append(self)
        self.actions.addAction(do)
