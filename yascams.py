# - current support: only EMC2 / linuxcnc
# - embedded cutter compensation is NOT used currently, may at some point

import sys

class cam:
  def __init__(self,tooldiam=None,feedrate=None):
    self.tooldiam=tooldiam
    self.toolrad=None
    self.feedrate=feedrate

    if feedrate is not None:
      self.raw("F%s" % feedrate)

    # constants
    self.Rapid=0
    self.Feed=1
    
  def raw(self,str):
    print str

  def preamble(self): # TODO
    self.raw("G90 G40")

    if self.tooldiam is None:
      self.tooldiam=0.0
      print "( WARNING: tooldiam not set, using 0 )"
      
    self.toolrad=self.tooldiam/2.0

    if self.feedrate is not None:
      self.raw("F%s" % self.feedrate)

    self.raw("")

  def tail(self): # TODO: spindle and coolant if configured
    self.raw("\nM02")

  def go(self,mode=None,x=None,y=None,z=None):
    if mode not in [self.Rapid,self.Feed]:
      print "( WARNING: skipping go(): mode makes no sense. )"
      return

    if x is None and y is None and z is None:
      print "( WARNING: skipping go(): no coords given. )"
      return

    line="G0%d" % mode
    if x is not None:
      line+=" X%s" % x

    if y is not None:
      line+=" Y%s" % y

    if z is not None:
      line+=" Z%s" % z

    self.raw(line)

  def line(self,mode=None,startx=None,starty=None,startz=None,
    endx=None,endy=None,endz=None):

    self.go(mode=mode,x=startx,y=starty,z=startz)
    self.go(mode=mode,x=endx,y=endy,z=endz)

  def circle(self,x=None,y=None,z=None,rad=None,diam=None):
    if rad is None:
      if diam is not None:
        rad=diam/2
      else:
        print "( WARNING: neither rad nor diam passed to circle(), can't continue. )"
        sys.exit(1)

    self.raw("G03 X%.4f Y%.4f I-%.4f J0 P1" % (x+rad,y,rad))

  def spiral(self,x=None,y=None,z=None,rad=None,diam=None,p=None):
    if rad is None:
      if diam is not None:
        rad=float(diam)/2.0
      else:
        print "( WARNING: neither rad nor diam passed to spiral(), can't continue. )"
        sys.exit(1)

    # P defaults to one rotation per tool diam
    if self.toolrad>0:
      p=int(abs(z/self.toolrad))
    else:
      if p is None:
        print "( WARNING: neither tooldiam nor P passed to spiral(), using P=2 )"
        p=2

    self.raw("G03 X%s Y%s Z%s I-%s J0 P%d" % (x+rad,y,z,rad,p))

  def hole(self,x=None,y=None,bottom=None,diam=None,finish=None):
    # bottom is the Z depth of the hole floor
    # finish is the amount left by the roughing cuts

    if self.z_clearance is None:
      self.critical("Can't make hole() when Z clearance hasn't been set!")

    if x is None or y is None or bottom is None or diam is None:
      self.critical("X, Y, Bottom, and Diameter are required for hole(), can't continue.")

    # since we arent using cutter offsets, we calculate them here. in the case of
    # hole(), we just decrease the radii by the cutter radius.
    rad=float(diam)/2.0
    rad-=self.toolrad

    if finish is not None and finish>0.0:
      # make all the cuts at rad-=finish, then a wall pass at original rad
      roughrad=rad-finish
    else: roughrad=rad

    self.raw("\n( hole at X%s Y%s down to Z%s; diam %s, finish %s )" % (
      x,y,bottom,diam,finish))

    self.go(mode=self.Rapid,z=self.z_clearance) # go to Z clearance
    self.go(mode=self.Rapid,x=(x+roughrad),y=y)      # go to spiral start
    self.spiral(x=x,y=y,z=bottom,rad=roughrad)        # spiral down to bottom level
    self.circle(x=x,y=y,z=bottom,rad=roughrad)        # make full pass at bottom level
    if rad!=roughrad:
      self.go(mode=self.Feed,x=(x+rad))
      self.circle(x=x,y=y,z=bottom,rad=rad)      # if enabled, make finish pass
    self.go(mode=self.Rapid,x=x,y=y)            # rapid to center
    self.go(mode=self.Rapid,z=self.z_clearance) # rapid back to Z clearance
    
  def drill(): pass

# yay test program
cam=cam()
cam.feedrate=1
cam.tooldiam=0.125
cam.z_clearance=0.1
cam.preamble()

cam.go(mode=cam.Rapid,x=0,y=0,z=cam.z_clearance)
cam.go(mode=cam.Feed,z=-0.01)
cam.go(mode=cam.Rapid,z=cam.z_clearance)

cam.hole(x=0.5,y=0,bottom=-0.26,diam=0.25,finish=0.010)
cam.hole(x=1,y=0,bottom=-0.26,diam=0.375,finish=0.010)
cam.hole(x=1.5,y=0,bottom=-0.26,diam=0.5,finish=0.010)

cam.tail()
