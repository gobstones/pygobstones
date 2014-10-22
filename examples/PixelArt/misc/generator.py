#!/usr/bin/python
#
# Copyright (C) 2011-2013 Ary Pablo Batista <arypbatista@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import sys
from PIL import Image

def generate(filename, options, matrixGenerator):
    
    indent = "  "
    output = """program {
  IrAInicioT(Este, Sur)\n"""
            
    for row in matrixGenerator(filename):
        output += (indent + "Mover(Este)\n").join([indent + ("Pintar(%s, %s, %s, %s)\n" % pixel) for pixel in row])            
        output += indent + """
  IrAlBorde(Oeste)
  MoverSiPuede(Sur)
"""      
        
    return output + "}"

def rgbaPixelDigestor(pixel):    
    return tuple(pixel.split(","))


def hexPixelDigestor(pixel):    
    return tuple([int("0x" + pixel[i:i+2], 0) for i in range(0, len(pixel), 2)])

        
def fileMatrixGenerator(options, pixelDigestor):
    def mat_(filename):
        lines = open(filename).readlines()
        pixel_separator = "|" if (not "pixel-separator" in options.keys() or 
                                  options["pixel-separator"] == []) else options["pixel-separator"]
        return [[pixelDigestor(pixel) for pixel in line[:-1].split(pixel_separator)] for line in lines]
    return mat_


def imagePixelDigestor(image, x, y):
    return image.getpixel((x,y))

def imageMatrixGenerator(options, pixelDigestor):
    def mat_(filename):
        im = (Image.open(filename)).convert("RGBA")
        return [[pixelDigestor(im, x, y) for x in xrange(im.size[0])] for y in xrange(im.size[1])]
    return mat_
    

def main(args, options):
    if options["image"]:
        print(generate(args[0], options, imageMatrixGenerator(options, imagePixelDigestor)))
    else:
        if options["hex"]:
            print(generate(args[0], options, fileMatrixGenerator(options, hexPixelDigestor)))
        else:
            print(generate(args[0], options, fileMatrixGenerator(options, rgbaPixelDigestor)))

"""
    Argument parsing
""" 
def default_options(option_switches):
    opt = {}
    for o in option_switches:
        o = o.split(' ')
        sw = o[0][2:]
        if sw[:3] == 'no-':
            neg = True
            sw = sw[3:]
        else:
            neg = False
        if len(o) == 1:
            opt[sw] = neg
        else:
            opt[sw] = []
    return opt   

def parse_options(option_switches, args, max_args=None):
    arguments = []
    opt = default_options(option_switches)
    i = 1
    n = len(args)
    while i < len(args):
        o = None
        for oi in option_switches:
            oi = oi.split(' ')
            if oi[0] == args[i]:
                o = oi
                break
        if o is None:
            if len(arguments) == max_args:
                return False
            arguments.append(args[i])
            i += 1
            continue

        sw = o[0][2:]
        if len(o) == 1:
            if sw[:3] == 'no-':
                neg = True
                sw = sw[3:]
            else:
                neg = False
            opt[sw] = not neg
            i += 1
        else:
            k = 1
            i += 1
            while k < len(o):
                if i >= n: return False
                opt[sw].append(args[i])
                i += 1
                k += 1
    return arguments, opt


SWITCHES = [
    '--image',
    '--csv',
    '--hex',
    '--rgba',
    '--pixel-separator X'
]

def usage():
    print("Argument needed:")
    print( "\t" + "\n\t".join(SWITCHES))

main(*parse_options(SWITCHES, sys.argv))