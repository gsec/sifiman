#! /usr/bin/env python
# coding: utf-8 ################################################################
#                          SifImAn - a SIF Image Analyzer                      #
################################################################################

from __future__ import print_function, division
import  os, sys, re, getopt

import  numpy as np
import  matplotlib.pyplot as plt
import  sifreader_v3 as sif
from    matplotlib  import ticker, gridspec
from    scipy       import stats

################
#  parameters  #
################
OUTPUT_PATH   = 'output'
EXPOSURE      = 1000            # in milliseconds
ZOOM          = True
#POWER_FACTOR = 12600           # measured factor, kinda random


class Intensity(object):
  def __init__(self, path_arg=None, multi_arg=None, exposure_arg=None):
    # Define default values
    if path_arg is None:
      self.path = os.curdir()
    if multi_arg is None:
      self.multi_image = 0
    if exposure_arg is None:
      self.exposure = 1000

    self.subdir     = os.path.join(self.path, OUTPUT_PATH)
    self.exposure   = exposure_arg
    self.results    = []
    self.image      = []
    self.index      = 0
    self.center     = (None,None)
    self.zoom_area  = (None,None)

    self.pump_file  = ''
    self.both_file  = ''
    self.trans_file = ''
    self.options    = {0: ['single',  self.single],
                       1: ['gain',    self.gain],
                       2: ['both',    self.both],
                       3: ['trans',   self.trans],
                       4: ['pump',    self.pump]}

    try:
      os.mkdir(self.subdir)
    except Exception:
      # ignore if error raised (i.e. already exists)
      pass

  def files(self, ending='.sif'):
    """
    SIF file list extractor.
    """
    for f in sorted(os.listdir(self.path)):
      if f.endswith(ending):
        self.file_name = f
        yield f

  def bg_ex(self, f):
    """
    Background correction for SIF files. Needs file, returns data array.
    Processes the readSIF script for a given filename, takes the (0,0)th
    point, which is the image data array, and subtracts the background
    which is approximated by the minimal value in the data.
    """
    dat = sif.readSIF(os.path.join(self.path, f))[0][0]
    return dat - np.min(dat[:511, :511])

  def single(self):
    print("Single file:", self.file_name)
    self.data =  self.bg_ex(self.file_name)

  def gain(self):
    print("Gain (Both - Trans - Pump):", self.both_file, self.trans_file,  \
          self.pump_file)
    self.data = self.bg_ex(self.both_file) - self.bg_ex(self.trans_file) - \
            self.bg_ex(self.pump_file)

  def both(self):
    print("Both:", self.both_file)
    self.data =  self.bg_ex(self.both_file)

  def trans(self):
    print("Trans:", self.trans_file)
    self.data =  self.bg_ex(self.trans_file)

  def pump(self):
    print("Pump:", self.pump_file)
    self.data = self.bg_ex(self.pump_file)

  def analyze(self):
    """
    Converts SIF file into actual image data. Uses the sifreader_v3 script.
    Normalizes the scale to the power conversion and defines a background
    as lowest value in the image. Writes the intensity and background with
    the filename into the results variable.
    """
    try:
      self.options[self.multi_image][1]()
    except:
      raise Exception("Multi Image Option not defined.")

    self.image =  self.data / self.exposure

    background = self.min_val = np.min(self.image[:511,:511])
    self.max_val = np.max(self.image[:511,:511])
      # stats.mode returns modal value = value that occours most often
    #background = stats.mode(im[:50,:50].ravel())[0][0]

    intensity = self.image.sum() - background*np.size(self.image)

    #results.append((self.index, intensity, background))
    self.index =+ 1

  def plot(self):
    plt.clf()
    if ZOOM:
    # zoom settings
      (cx, cy) = self.center
      (dx, dy) = self.zoom_area
      imgplot = plt.subplot(111)
      imgplot.imshow(self.image)
      imgplot.set_xlim((cx-dx, cx+dx))
      imgplot.set_ylim((cy-dy, cy+dy))
    # scale bar settings
    totalimage = plt.imshow(self.image)
    totalimage.set_clim(self.min_val, self.max_val)
    plt.colorbar()

    if self.multi_image == 0:
      plt.savefig(os.path.join(self.subdir,
        self.file_name).strip('.sif') + '.png')
    else:
      plt.savefig(os.path.join(self.subdir,
        self.options[self.multi_image][0] + '_' +
        self.pump_file).rstrip('p.sif') + '.png')

  def tripler(self, number=3):
    """
    Chops a list (of files) into tuples of size 'number'.
    """
    i = 0
    trip_list = []
    flist = list(self.files())
    while i <= len(flist) - number:
      triples = tuple(flist[i+ count] for count in range(number) )
      trip_list.append(triples)
      i += number
    return trip_list

def usage():
  print()
  print("SifImAn - Analyzer for Andor SIF Image files")
  print("-"*50)
  print("Usage: ", sys.argv[0], "[option] <folder>")
  print("""
        -h  --help      : Print this help
        -p  --path      : Specify path with image files. Default is current
                          directory.
        -m  --multi     : Defines the MULTIPLE_IMAGES option.
                          option values:
                             0 =  single image (default)
                             1 =  gain
                             2 =  both
                             3 =  trans
                             4 =  pump
                             5 =  all
        """)
def main(path_arg, multi_arg, exposure_arg):
  if multi_arg == 0:
    pic = Intensity(path_arg, multi_arg, exposure_arg)
    for f in pic.files():
      pic.analyze()
      pic.plot()

  elif multi_arg == 5:
    for state in range(1,5):
      pic = Intensity(path_arg, state, exposure_arg)
      for f in pic.files():
        pic.analyze()
        pic.plot()

  else:
    pic = Intensity(path_arg, multi_arg, exposure_arg)
    for f in pic.tripler():
      (pic.pump_file, pic.both_file, pic.trans_file) = f
      pic.analyze()
      pic.plot()
##
##  def main_loop():
##    if MULTIPLE_IMAGES == 0:
##      for f in pic.files():
##        pic.analyze()
##        pic.plot()
##    else:
##      for f in pic.tripler():
##        (pic.pump_file, pic.both_file, pic.trans_file) = f
##        pic.analyze()
##        pic.plot()
##
##  # single type:
##  #main_loop(MULTIPLE_IMAGES)
##
##  def all_together():
##    for state in range(1,5):
##      MULTIPLE_IMAGES = state
##      pic = Intensity()
##      pic.zoom_area = (70,100)
##      pic.center = (230,230)
##      main_loop()
##
# ==============================================================================
if __name__ == '__main__':
  try:
    # Short option syntax: "hv:"
    # Long option syntax: "help" or "verbose="
    opts, args = getopt.getopt(sys.argv[1:], "hp:t:",
        ["help", "path=", "tag="])
    path_arg = multi_arg = exposure_arg = None

  except getopt.GetoptError as err:
    # Print debug info
    print(str(err))
    #error_action, exit with error
    sys.exit(2)

  for option, argument in opts:
    if option in ("-h", "--help"):
      usage()
      sys.exit()

    elif option in ("-p", "--path"):
      arg_path = argument

    elif option in ("-t", "--tag"):
      print("Tag Option not implemented")
      sys.exit()
      #arg_tag = argument

    main(path_arg, multi_arg, exposure_arg)
