#!/usr/bin/python

import sys, os, getopt, glob, string, math
import colorchart, graychart

class Range:
    def __init__(self, n=100, min=None, max=None):
        self.n = n
        self.min = min
        self.max = max

    def newmin(self, x):
        if x<self.min: self.min = x

    def newmax(self, x):
        if x>self.max: self.max = x

    def update(self, x):
        if self.min and self.max:
            self.newmin(x)
            self.newmax(x)
        else:
            self.min = self.max = x

    def get_range(self):
        return 1.0 * (self.max - self.min)

    def get_mid(self):
        return (self.max + self.min) / 2.0

    def get_step(self):
        return self.range / self.n

    range = property(get_range)
    mid = property(get_mid)
    step = property(get_step)

    def loc(self, frac):
        return self.min + frac * self.range

    def union(self, other):
        self.newmin(other.min)
        self.newmax(other.max)

    def grow(self, factor):
        x = self.range * factor
        self.min -= x
        self.max += x

    def index(self, x):
        frac = (x - self.min) / self.range
        index = int(frac * self.n)
        if index < 0: index = -1
        if index > self.n: index = self.n
        return index

    def coord(self, i):
        x = self.min + self.step*i + self.step/2
        return x

    def __str__(self):
        return '(%f, %f)' % (self.min, self.max)


class Thing:
    def __init__(self, *args, **kwds):
        self.prefix = ''
        self.opts = kwds
        self.setopt(*args)

    def setopt(self, *args, **kwds):
        self.opts.update(kwds)
        for arg in args:
            self.opts[arg] = ''

    def __str__(self):
        list = ['%s %s ' % (opt, str(val)) for (opt, val) in self.opts.items()]
        return self.prefix + string.join(list)

    

class Font(Thing): pass

class Hashlabels(Thing): pass

helv24 = Font('Helvetica', fontsize=24)

class String(Thing):
    def __init__(self, label, *args, **kwds):
        kwds.setdefault('font', helv24)
        Thing.__init__(self, *args, **kwds)
        self.prefix = ': %s\n' % label

class Graph(Thing):
    def __init__(self, *args, **kwds):
        Thing.__init__(self, *args, **kwds)
        self.prefix = '\nnewgraph\n'
        if 'noclip' not in args: self.setopt('clip')
        if 'noborder' not in args: self.setopt('border')

class Curve(Thing):
    def __init__(self, *args, **kwds):
        Thing.__init__(self, *args, **kwds)
        self.prefix = '\nnewcurve\n'
        self.type = 'pts'
        self.pts = ''

    def __str__(self):
        ret = Thing.__str__(self)
        ret += self.type + '\n' + self.pts + '\n'
        return ret


class Axis(Thing):
    def __init__(self, range=None, *args, **kwds):
        Thing.__init__(self, *args, **kwds)
        if range:
            self.setopt(min=range.min)
            self.setopt(max=range.max)
            
    def hash_labels(self, locs, labels=[], func=str):
        if labels==[]:
            labels = map(func,locs)
        self.setopt('no_auto_hash_labels')
        list = ['hash_label at %g : %s\n' % p for p in zip(locs, labels)]
        self.setopt(string.join(list))

    def hash_marks(self, locs):
        self.setopt('no_auto_hash_marks')
        list = ['hash_at %g ' % loc for loc in locs]
        self.setopt(string.join(list))

hls24 = Hashlabels(font=helv24)

class Legend(Thing):
    def __init__(self, *args, **kwds):
        Thing.__init__(self, *args, **kwds)
        self.prefix = 'defaults '


def make_xaxis(xr, yr, s='x', hls=hls24):
    label = String(s)
    axis = Axis(size=6, range=xr, label=label, hash_labels=hls,
                 draw_hash_labels_at=yr.loc(-0.04))
    return axis

def make_yaxis(yr, s='y', hls=hls24):
    label = String(s)
    axis = Axis(size=4.5, range=yr, label=label, hash_labels=hls)
    return axis

def manual_labels(axis, n):
    vals = range(0, yr.range, int(yr.range/n))
    axis.hash_labels(vals, func=str)
    axis.hash_marks(vals)

def colorstring(list):
    rgb = '%.4g %.4g %.4g' % list
    return rgb

def graystring(x):
    return colorstring((x, x, x))

def rainbow():
    colors = ['red', 'orange', 'yellow', 'greenyellow', 'green', 'lightblue',
              'cyan', 'blue', 'purple', 'magenta']
    rgbs = [colorchart.rgb.get(color) for color in colors]
    return rgbs

def grayscale(n):
    xs = [1.0*i/n for i in range(n+1)]
    rgbs = [graystring(x) for x in xs]
    return rgbs

def make_lingray():
    fp = open('lingray', 'r')
    print 'rgb = ['
    for line in fp:
        list = parse_line(line)
        print "%.4g," % (list[0]/256.0)
    print ']'
    # need to fix this to eliminate final comma

#make_lingray()

def range_file(file, awk=None):
    fp = popen(file, awk)

    xr = Range(60)
    yr = Range(45)
    
    for line in fp:
        t = parse_line(line)
        if not t: continue
        
        xr.update(t.pop(0))
        for y in t:
            yr.update(y)

    xr.grow(0.1)
    yr.grow(0.1)
    return (xr, yr)

def range_files(files, awk=None):
    file = files[0]
    (xr, yr) = range_file(file, awk)

    for file in files[1:]:
        (xxr, yyr) = range_file(file, awk)
        xr.union(xxr)
        yr.union(yyr)

    return (xr, yr)

def parse_line(line):
    if line[0] == '#': return None
    t = map(float, string.split(line))
    return t

def unparse_lines(t):
    t = ['\t'.join(map(str, line)) for line in t]
    return '\n'.join(t)

def popen(file, awk=None):
    if awk:
        fp = os.popen("awk '%s' < %s" % (awk, file))
    else:
        fp = open(file, 'r')
    return fp

def interp(file, awk=None):
    #print file
    fp = popen(file, awk)
    t = [parse_line(line) for line in fp]
    t = [line for line in t if line]
    return t
    
def no_interp(file, awk=None):
    fp = popen(file, awk)
    line = fp.readline()
    (x, y) = string.split(line)
    lastx = x
    ret = ['%s %s\n' % (x, y)]
    for line in fp:
        (x, y) = string.split(line)
        ret.append('%s %s\n' % (lastx, y))
        ret.append('%s %s\n' % (x, y))
        lastx = x
    return string.join(ret)
            
def dump_file(file, awk=None, marktype='none', linetype='none',
              reader=interp, **kwds):
    curve = Curve(marktype=marktype, linetype=linetype, **kwds)
    t = reader(file, awk)
    if len(t[0]) == 4:
        curve.type = 'y_epts'

    curve.pts = unparse_lines(t)
    return curve

def dump_files(files, awk=None, **kwds):
    i=0
    curves = []
    for file in files:
        curve = dump_file(file, awk,
                          linetype=linetypes[i],
                          marktype=marktypes[i], **kwds)
        curves.append(curve)
        i += 1
    return curves

# convert a list of numeric pairs to a string of coordinates
def convert_locs(locs, xr, yr):
    pts = ['%.6g %.6g' % (xr.coord(i), yr.coord(j)) for (i, j) in locs]
    return string.join(pts)

def scatter_file(file, xr, yr, awk=None):
    # scatter counts the number of times each loc is hit
    scatter = {}
    fp = popen(file, awk)
    for line in fp:
        (x, y) = parse_line(line)
        index = (xr.index(x), yr.index(y))
        scatter[index] = scatter.get(index, 0) + 1

    # list contains (count, loc) pairs, in increasing order of frequency
    list = [(math.log(val), key) for (key, val) in scatter.items()]
    list.sort()

    # zr is the range of frequency values
    zr = Range(14, 0, list[-1][0])


    # locs maps frequency levels onto a list of locs
    locs = {}
    for (z, loc) in list:
        i = zr.index(z) + 1
        try:
            locs[i].append(loc)
        except KeyError:
            locs[i] = [loc]

    # generate one curve per frequency level
    curves = []
    marksize = '%f %f' % (xr.step, yr.step)
    for (i, loc) in locs.items():
        curve = Curve(linetype='none', marktype='box', marksize=marksize,
                      gray=grays[255-16*i])
        curve.pts = convert_locs(loc, xr, yr)
        curves.append(curve)
    return curves

# flatten a tree into a single list
def flatten(list):
    for item in list:
        if is_scalar(item):
            yield item
        else:
            for subitem in flatten(item):
                yield subitem

def has_iter(item):
    try: iter(item)
    except: return 0
    else: return 1

def is_scalar(item):
    return not has_iter(item)

# generate the jgr file.  args is a tree of Things
def make_jgr(outfile, *args):
    jgrfile = outfile + '.jgr'
    outfp = open(jgrfile, 'w')
    for thing in flatten(args):
        outfp.write(str(thing))
    outfp.close()

# use jgraph to generate eps from jgr
def make_eps(outfile):
    jgrfile = outfile + '.jgr'
    epsfile = outfile + '.eps'
    epsfp = os.popen('jgraph %s | epsffit -c 36 0 540 792' % jgrfile, 'r')
    outfp = open(epsfile, 'w')
    outfp.writelines(epsfp)
    outfp.close()
    epsfp.close()

# generate png from eps
def make_png(outfile):
    epsfile = outfile + '.eps'
    pngfile = outfile + '.png'
    (fin, fout, ferr) = os.popen3(
        'pstopnm -stdout -portrait %s | pnmtopng' % epsfile)

    outfp = open(pngfile, 'w')
    outfp.writelines(fout)
    outfp.close()
    fin.close()
    fout.close()
    ferr.close()

#################################################################



def main(script, *args):
    # set options
    png = 0
    display = 1

    (opts, args) = getopt.getopt(args, 'dp', ['png', 'display='])
    optdict = {}
    for (key, val) in opts:
        optdict[key] = val

    # default independent and dependent variables
    ind = 'nepotism'
    deps = ('nepotism', 'selectivity', 
            'mobility', 'skew', 'gnp', 'cv')

    # if there is an argument, it's the name of the independent variable
    if args:
        ind = args[0]
        args = args[1:]

    # if there are more arguments, they're the dependent variables
    if args:
        dep = args

    awk = None
    xlabel = ind
    ylabel = ''
    title = ''
    outfile = 'graph'

    rgbs = ['0.0']
    marktypes = ['circle', 'box', 'diamond', 'triangle', 'ellipse', 'x']
    linetypes = ['solid', 'dotted', 'dashed', 'longdash', 'dotdash',
                 'dotdotdash', 'dotdotdashdash'] 

    files = ['%s.%s' % (ind, dep) for dep in deps]
    (xr, yr) = range_files(files, awk)
    xsize = 0.02 * xr.range
    ysize = 0.02 * yr.range
    marksize = '%f %f' % (xsize, ysize)

    i=0
    curves = []
    for dep in deps:
        file = '%s.%s' % (ind, dep)
        curve = dump_file(file, awk,
                          linetype=linetypes[i],
                          linethickness=2,
                          fill=0.8,
                          marksize=marksize,
                          marktype=marktypes[i],
                          label=String(dep))
        curves.append(curve)
        i += 1


    # create the graph
    titles = String(title, y=yr.loc(1.1))
    xaxis = make_xaxis(xr, yr, xlabel)
    yaxis = make_yaxis(yr, ylabel)
    graph = Graph('noborder', xaxis=xaxis, yaxis=yaxis, title=titles)


    make_jgr(outfile, graph, curves)
    make_eps(outfile)
    if png:
        make_png(outfile)


if __name__ == '__main__':
    main(*sys.argv)

