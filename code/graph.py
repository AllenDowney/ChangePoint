#!/usr/bin/python

import os, math, string

def underride(d, *args, **kwds):
    """add args and kwds to the dictionary only if they are not already set"""
    for key in args:
        if key not in d:
            d[key] = ''
            
    for key, val in kwds.iteritems():
        if key not in d:
            d[key] = val

def override(d, **kwds):
    """Add kwds to the dictionary even if they are already set"""
    d.update(kwds)

class Range:
    """represents a range of values with n steps from min to max
    """
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
    """represents a jgraph entity; the opts dictionary contains
    option-value pairs for jgraph options.
    """
    def __init__(self, *args, **kwds):
        self.prefix = ''
        self.opts = kwds
        self.setopt(*args)

    def setopt(self, *args, **kwds):
        """add the given args and kwds to this Thing's options;
        args are given the value ''
        """
        self.opts.update(kwds)
        for arg in args:
            self.opts[arg] = ''

    def __str__(self):
        """the string representation of a Thing is the prefix
        followed by the string rep of the option-value pairs.
        """
        list = ['%s %s ' % (opt, str(val)) for opt, val in self.opts.items()]
        return self.prefix + ''.join(list)

    

class Font(Thing): pass

helv24 = Font('Helvetica', fontsize=24)
helv20 = Font('Helvetica', fontsize=20)

class Hashlabels(Thing): pass

class String(Thing):
    """when a string is printed, it needs a colon before and
    a newline after
    """
    def __init__(self, label, *args, **kwds):
        underride(kwds, font=helv24)
        Thing.__init__(self, *args, **kwds)
        self.prefix = ': %s\n' % label

class Graph(Thing):
    def __init__(self, *args, **kwds):
        Thing.__init__(self, *args, **kwds)
        self.prefix = '\nnewgraph\n'

        # set clip and border unless the user says otherwise
        if 'noclip' not in args: self.setopt('clip')
        if 'noborder' not in args: self.setopt('border')

class Curve(Thing):
    def __init__(self, *args, **kwds):
        Thing.__init__(self, *args, **kwds)
        self.prefix = '\nnewcurve\n'


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
        self.setopt(''.join(list))

    def hash_marks(self, locs):
        self.setopt('no_auto_hash_marks')
        list = ['hash_at %g ' % loc for loc in locs]
        self.setopt(''.join(list))

hls24 = Hashlabels(font=helv24)

class Legend(Thing):
    def __init__(self, *args, **kwds):
        underride(kwds, font=helv20)
        Thing.__init__(self, *args, **kwds)
        self.prefix = 'defaults '

def make_xaxis(xr, yr, label='x', *args, **options):
    underride(options, hash_labels=hls24, size=6,
                 draw_hash_labels_at=yr.loc(-0.05))
    label = String(label)
    axis = Axis(xr, label=label, *args, **options)
    return axis

def make_yaxis(yr, label='y', *args, **options):
    underride(options, hash_labels=hls24, size=4.5)
    label = String(label)
    axis = Axis(yr, label=label, *args, **options)
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
    print file
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
    return ''.join(ret)
            
def dump_file(file, awk=None, marktype='none', linetype='none',
              reader=interp, **kwds):
    curve = Curve(marktype=marktype, linetype=linetype, **kwds)
    t = reader(file, awk)

    pts = unparse_lines(t)
    if len(t[0]) == 4:
        curve.setopt(y_epts=pts)
    else:
        curve.setopt(pts=pts)

    return curve

def dump_lists(t1, t2, marktype='none', linetype='solid', **kwds):
    t = [(y, x) for y, x in zip(t1, t2) if x is not None]
    pts = unparse_lines(t)
    curve = Curve(pts=pts, marktype=marktype, linetype=linetype, **kwds)
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
    return ''.join(pts)

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

# generate the jgr file.  args is a list of Thing trees
def make_jgr(outfile, *args):
    fp = open_jgr(outfile)
    write_jgr(fp, *args)
    fp.close()

def open_jgr(outfile):
    jgrfile = outfile + '.jgr'
    fp = open(jgrfile, 'w')
    return fp

def write_jgr(fp, *args):
    for thing in flatten(args):
        fp.write(str(thing))
        

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


rgb = {
'maroon' : '0.502 0 0',
'darkred' : '0.545 0 0',
'red' : '1 0 0',
'lightpink' : '1 0.714 0.757',
'crimson' : '0.863 0.0784 0.235',
'palevioletred' : '0.859 0.439 0.576',
'hotpink' : '1 0.412 0.706',
'deeppink' : '1 0.0784 0.576',
'mediumvioletred' : '0.78 0.0824 0.522',
'purple' : '0.502 0 0.502',
'darkmagenta' : '0.545 0 0.545',
'orchid' : '0.855 0.439 0.839',
'thistle' : '0.847 0.749 0.847',
'plum' : '0.867 0.627 0.867',
'violet' : '0.933 0.51 0.933',
'fuchsia' : '1 0 1',
'magenta' : '1 0 1',
'mediumorchid' : '0.729 0.333 0.827',
'darkviolet' : '0.58 0 0.827',
'darkorchid' : '0.6 0.196 0.8',
'blueviolet' : '0.541 0.169 0.886',
'indigo' : '0.294 0 0.51',
'mediumpurple' : '0.576 0.439 0.859',
'slateblue' : '0.416 0.353 0.804',
'mediumslateblue' : '0.482 0.408 0.933',
'darkblue' : '0 0 0.545',
'mediumblue' : '0 0 0.804',
'blue' : '0 0 1',
'navy' : '0 0 0.502',
'midnightblue' : '0.098 0.098 0.439',
'darkslateblue' : '0.282 0.239 0.545',
'royalblue' : '0.255 0.412 0.882',
'cornflowerblue' : '0.392 0.584 0.929',
'lightsteelblue' : '0.69 0.769 0.871',
'aliceblue' : '0.941 0.973 1',
'ghostwhite' : '0.973 0.973 1',
'lavender' : '0.902 0.902 0.98',
'dodgerblue' : '0.118 0.565 1',
'steelblue' : '0.275 0.51 0.706',
'deepskyblue' : '0 0.749 1',
'slategray' : '0.439 0.502 0.565',
'lightslategray' : '0.467 0.533 0.6',
'lightskyblue' : '0.529 0.808 0.98',
'skyblue' : '0.529 0.808 0.922',
'lightblue' : '0.678 0.847 0.902',
'teal' : '0 0.502 0.502',
'darkcyan' : '0 0.545 0.545',
'darkturquoise' : '0 0.808 0.82',
'aqua' : '0 1 1',
'cyan' : '0 1 1',
'mediumturquoise' : '0.282 0.82 0.8',
'cadetblue' : '0.373 0.62 0.627',
'paleturquoise' : '0.686 0.933 0.933',
'lightcyan' : '0.878 1 1',
'azure' : '0.941 1 1',
'lightseagreen' : '0.125 0.698 0.667',
'turquoise' : '0.251 0.878 0.816',
'powderblue' : '0.69 0.878 0.902',
'darkslategray' : '0.184 0.31 0.31',
'aquamarine' : '0.498 1 0.831',
'mediumspringgreen' : '0 0.98 0.604',
'mediumaquamarine' : '0.4 0.804 0.667',
'springgreen' : '0 1 0.498',
'mediumseagreen' : '0.235 0.702 0.443',
'seagreen' : '0.18 0.545 0.341',
'limegreen' : '0.196 0.804 0.196',
'darkgreen' : '0 0.392 0',
'green' : '0 0.502 0',
'lime' : '0 1 0',
'forestgreen' : '0.133 0.545 0.133',
'darkseagreen' : '0.561 0.737 0.561',
'lightgreen' : '0.565 0.933 0.565',
'palegreen' : '0.596 0.984 0.596',
'mintcream' : '0.961 1 0.98',
'honeydew' : '0.941 1 0.941',
'chartreuse' : '0.498 1 0',
'lawngreen' : '0.486 0.988 0',
'olivedrab' : '0.42 0.557 0.137',
'darkolivegreen' : '0.333 0.42 0.184',
'yellowgreen' : '0.604 0.804 0.196',
'greenyellow' : '0.678 1 0.184',
'beige' : '0.961 0.961 0.863',
'linen' : '0.98 0.941 0.902',
'lightgoldenrodyellow' : '0.98 0.98 0.824',
'olive' : '0.502 0.502 0',
'yellow' : '1 1 0',
'lightyellow' : '1 1 0.878',
'ivory' : '1 1 0.941',
'darkkhaki' : '0.741 0.718 0.42',
'khaki' : '0.941 0.902 0.549',
'palegoldenrod' : '0.933 0.91 0.667',
'wheat' : '0.961 0.871 0.702',
'gold' : '1 0.843 0',
'lemonchiffon' : '1 0.98 0.804',
'papayawhip' : '1 0.937 0.835',
'darkgoldenrod' : '0.722 0.525 0.0431',
'goldenrod' : '0.855 0.647 0.125',
'antiquewhite' : '0.98 0.922 0.843',
'cornsilk' : '1 0.973 0.863',
'oldlace' : '0.992 0.961 0.902',
'moccasin' : '1 0.894 0.71',
'navajowhite' : '1 0.871 0.678',
'orange' : '1 0.647 0',
'bisque' : '1 0.894 0.769',
'tan' : '0.824 0.706 0.549',
'darkorange' : '1 0.549 0',
'burlywood' : '0.871 0.722 0.529',
'saddlebrown' : '0.545 0.271 0.0745',
'sandybrown' : '0.957 0.643 0.376',
'blanchedalmond' : '1 0.922 0.804',
'lavenderblush' : '1 0.941 0.961',
'seashell' : '1 0.961 0.933',
'floralwhite' : '1 0.98 0.941',
'snow' : '1 0.98 0.98',
'peru' : '0.804 0.522 0.247',
'peachpuff' : '1 0.855 0.725',
'chocolate' : '0.824 0.412 0.118',
'sienna' : '0.627 0.322 0.176',
'lightsalmon' : '1 0.627 0.478',
'coral' : '1 0.498 0.314',
'darksalmon' : '0.914 0.588 0.478',
'mistyrose' : '1 0.894 0.882',
'orangered' : '1 0.271 0',
'salmon' : '0.98 0.502 0.447',
'tomato' : '1 0.388 0.278',
'rosybrown' : '0.737 0.561 0.561',
'pink' : '1 0.753 0.796',
'indianred' : '0.804 0.361 0.361',
'lightcoral' : '0.941 0.502 0.502',
'brown' : '0.647 0.165 0.165',
'firebrick' : '0.698 0.133 0.133',
'black' : '0 0 0',
'dimgray' : '0.412 0.412 0.412',
'gray' : '0.502 0.502 0.502',
'darkgray' : '0.663 0.663 0.663',
'silver' : '0.753 0.753 0.753',
'lightgrey' : '0.827 0.827 0.827',
'gainsboro' : '0.863 0.863 0.863',
'whitesmoke' : '0.961 0.961 0.961',
'white' : '1 1 1',
}


rgb = [
0.08594,
0.1211,
0.1445,
0.1602,
0.1797,
0.1953,
0.207,
0.2188,
0.2305,
0.2422,
0.2539,
0.2617,
0.2734,
0.2812,
0.2891,
0.2969,
0.3047,
0.3125,
0.3203,
0.3281,
0.3359,
0.3438,
0.3477,
0.3555,
0.3633,
0.3672,
0.375,
0.3789,
0.3867,
0.3906,
0.3984,
0.4023,
0.4102,
0.4141,
0.418,
0.4258,
0.4297,
0.4336,
0.4375,
0.4453,
0.4492,
0.4531,
0.457,
0.4648,
0.4688,
0.4727,
0.4766,
0.4805,
0.4844,
0.4883,
0.4922,
0.5,
0.5039,
0.5078,
0.5117,
0.5156,
0.5195,
0.5234,
0.5273,
0.5312,
0.5352,
0.5391,
0.543,
0.5469,
0.5508,
0.5508,
0.5547,
0.5586,
0.5625,
0.5664,
0.5703,
0.5742,
0.5781,
0.582,
0.5859,
0.5859,
0.5898,
0.5938,
0.5977,
0.6016,
0.6055,
0.6094,
0.6094,
0.6133,
0.6172,
0.6211,
0.625,
0.625,
0.6289,
0.6328,
0.6367,
0.6406,
0.6406,
0.6445,
0.6484,
0.6523,
0.6523,
0.6562,
0.6602,
0.6641,
0.6641,
0.668,
0.6719,
0.6758,
0.6758,
0.6797,
0.6836,
0.6836,
0.6875,
0.6914,
0.6953,
0.6953,
0.6992,
0.7031,
0.7031,
0.707,
0.7109,
0.7109,
0.7148,
0.7188,
0.7188,
0.7227,
0.7266,
0.7266,
0.7305,
0.7344,
0.7344,
0.7383,
0.7422,
0.7422,
0.7461,
0.7461,
0.75,
0.7539,
0.7539,
0.7578,
0.7617,
0.7617,
0.7656,
0.7656,
0.7695,
0.7734,
0.7734,
0.7773,
0.7773,
0.7812,
0.7852,
0.7852,
0.7891,
0.7891,
0.793,
0.7969,
0.7969,
0.8008,
0.8008,
0.8047,
0.8047,
0.8086,
0.8125,
0.8125,
0.8164,
0.8164,
0.8203,
0.8203,
0.8242,
0.8281,
0.8281,
0.832,
0.832,
0.8359,
0.8359,
0.8398,
0.8398,
0.8438,
0.8438,
0.8477,
0.8516,
0.8516,
0.8555,
0.8555,
0.8594,
0.8594,
0.8633,
0.8633,
0.8672,
0.8672,
0.8711,
0.8711,
0.875,
0.875,
0.8789,
0.8789,
0.8828,
0.8828,
0.8867,
0.8867,
0.8906,
0.8906,
0.8945,
0.8945,
0.8984,
0.8984,
0.9023,
0.9023,
0.9062,
0.9062,
0.9102,
0.9102,
0.9141,
0.9141,
0.918,
0.918,
0.9219,
0.9219,
0.9258,
0.9258,
0.9297,
0.9297,
0.9336,
0.9336,
0.9375,
0.9375,
0.9414,
0.9414,
0.9453,
0.9453,
0.9453,
0.9492,
0.9492,
0.9531,
0.9531,
0.957,
0.957,
0.9609,
0.9609,
0.9648,
0.9648,
0.9688,
0.9688,
0.9688,
0.9727,
0.9727,
0.9766,
0.9766,
0.9805,
0.9805,
0.9844,
0.9844,
0.9844,
0.9883,
0.9883,
0.9922,
0.9922,
0.9961,
0.9961,
1
]
