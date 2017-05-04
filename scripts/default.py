import wave

#music = wave.open(str(getAudio("Pixelland")), 'rb')
#properties = propertiesForWave(music)
properties = None

world.audioStream = AudioMixer(keepOpen=True, properties=properties)

#musicStream = AudioDataStream(music.readframes(music.getnframes()), properties)
#musicStream.play()
#musicStream.setCompleteAction(musicStream.play)
#world.audioStream.addStream(musicStream)


def makePlayer():
    player = FirstPersonPlayer( world,
                                world.axisInputs['x_look'],
                                world.axisInputs['y_look'],
                                world.axisInputs['x_walk'],
                                world.axisInputs['y_walk'],
                                world.buttonInputs['jump'],
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

world.simulator.addObject(UseScanner(world.buttonInputs['use']))

class FallScanner(SimObject):

    def __init__(self):
        self.die = False

    def scan(self, timeElapsed, totalTime):
        if world.camera.getPosition().z < -1000:
            self.die = True

    def update(self):
        if self.die:
            die()

world.simulator.addObject(FallScanner())

world.score = 0

def addScore(score):
    global score1, score2, score3, score4, score5
    world.score += score

    place = 1
    for i in range(0, 5):
        digit = int((world.score % (place * 10)) / place)

        digitPoint = [score1, score2, score3, score4, score5][i]
        digitRenderMesh = digitPoint.getChildren()[0]
        digitMesh = digitRenderMesh.getMesh()

        for face in digitMesh.getFaces():
            face.textureShift = face.textureShift.setX(114 - 12 * digit)
            face.calculateTextureVertices()

        place *= 10

    world.audioStream.addStream(
        AmplitudeModifier(
            AudioStreamSequence([
                NoteStream(750, 0.05, properties),
                NoteStream(1000, 0.05, properties)
            ], properties),
        0.2) )

def die():
    print("You died.")
    mapPath = getMap("map1")
    state = loadMapState(mapPath)
    controller.setState(state)

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


class InfinitePlatform(Entity):

    def __init__(self, movement):
        super().__init__()
        self.movement = movement

    def scan(self, timeElapsed, totalTime):
        def do(toUpdateList):
            self.translate(self.movement * timeElapsed)
            toUpdateList.append(self)
        self.actions.addAction(do)

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
        self.fallTime = None
        self.zVel = 0

    def startFalling(self):
        self.falling = True

    def scan(self, timeElapsed, totalTime):
        def do(toUpdateList):
            if self.falling:
                if self.fallTime == None:
                    self.fallTime = totalTime
                if totalTime - self.fallTime > 2.0:
                    self.zVel += FirstPersonPlayer.GRAVITY * timeElapsed
            self.translate(Vector(0, 0, self.zVel * timeElapsed))
            toUpdateList.append(self)
        self.actions.addAction(do)

class Conveyor(Entity):

    def __init__(self, movement):
        super().__init__()
        self.movement = movement
        self.enabled = False

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False

    def scan(self, timeElapsed, totalTime):
        def do(toUpdateList):
            if self.enabled:
                world.camera.translate(self.movement * timeElapsed)
                toUpdateList.append(world.camera)
            renderMesh = self.getChildren()[0]
            mesh = renderMesh.getMesh()
            for f in mesh.getFaces():
                if f.getNormal().z > 0.9:
                    pass
                    #f.textureShift += Vector(0, -timeElapsed * 8)
                    #f.calculateTextureVertices()
        self.actions.addAction(do)

class Button(Entity):

    def __init__(self, onAction=None, offAction=None):
        super().__init__()
        self.startPosition = None
        self.targetPosition = None
        self.onAction = onAction
        self.offAction = offAction

    def on(self):
        self.targetPosition = self.startPosition - Vector(0,0,3)
        if self.onAction != None:
            self.onAction()

    def off(self):
        self.targetPosition = self.startPosition
        if self.offAction != None:
            self.offAction()

    def scan(self, timeElapsed, totalTime):
        if self.startPosition == None:
            self.startPosition = self.getPosition()
            self.targetPosition = self.startPosition
        def do(toUpdateList):
            self.translate((self.targetPosition - self.getPosition())
                           * 0.5)
            toUpdateList.append(self)
        self.actions.addAction(do)

class HiddenPlatform(Entity):
    HIDDEN_Z = -2048
    def __init__(self, startHidden=False):
        super().__init__()
        self.startZ = None
        if startHidden:
            self.cycleTarget = math.pi/2
            self.cycle = math.pi/2
        else:
            self.cycleTarget = 0
            self.cycle = 0
        self.startHidden = startHidden

    def hide(self):
        self.cycleTarget = math.pi/2
        
    def show(self):
        self.cycleTarget = 0

    def scan(self, timeElapsed, totalTime):
        if self.startZ == None:
            self.startZ = self.getPosition().z
        def do(toUpdateList):
            if self.cycle > self.cycleTarget:
                self.cycle -= timeElapsed*2
            if self.cycle < self.cycleTarget:
                self.cycle += timeElapsed*2
            zRange = self.startZ - HiddenPlatform.HIDDEN_Z
            position = (1-(1-math.cos(self.cycle))**6) \
                       * zRange + HiddenPlatform.HIDDEN_Z
            self.translate(Vector(0,0,position - self.getPosition().z))
            toUpdateList.append(self)
        self.actions.addAction(do)

class RippleEnable(Entity):

    def __init__(self, enableFunctions, disableFunctions, enabled=False):
        super().__init__()
        self.lastUpdateTime = -1
        self.index = -1
        self.enabled = [enabled for f in enableFunctions]
        self.enableFunctions = enableFunctions
        self.disableFunctions = disableFunctions
        self.enabling = False

    def _enableIndex(self, index):
        if not self.enabled[index]:
            self.enableFunctions[index]()
            self.enabled[index] = True

    def _disableIndex(self, index):
        if self.enabled[index]:
            self.disableFunctions[index]()
            self.enabled[index] = False

    def enable(self):
        self.enabling = True
        self.index = 0
        self.lastUpdateTime = -1

    def disable(self):
        self.enabling = False
        self.index = 0
        self.lastUpdateTime = -1

    def scan(self, timeElapsed, totalTime):
        if self.lastUpdateTime == -1:
            self.lastUpdateTime = totalTime
        if self.index != -1:
            if self.index >= len(self.enableFunctions):
                self.index = -1
            else:
                if totalTime - self.lastUpdateTime > .1:
                    self.lastUpdateTime = totalTime
                    if self.enabling:
                        self._enableIndex(self.index)
                    else:
                        self._disableIndex(self.index)
                    self.index += 1
