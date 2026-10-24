import sys, getopt
from graph import *

def main(script, *args):
    # set options
    png = 0
    display = 1

    (opts, args) = getopt.getopt(args, 'dp', ['png', 'display='])
    optdict = {}
    for (key, val) in opts:
        optdict[key] = val

    awk = None
    xlabel = 'false alarm probability'
    ylabel = 'mean delay'
    title = ''
    outfile = 'matfar'

    gray = ['0.7', '0.0', '0.0', '0.0']
    marktypes = ['circle', 'box', 'diamond', 'triangle', 'ellipse', 'x']
    linetypes = ['dotted', 'solid', 'dashed', 'longdash', 'dotdash',
                 'dotdotdash', 'dotdotdashdash'] 
    labels = ['GLR', 'CPP']

    files = ['mat_vs_far.glr1', 'mat_vs_far.ipp2b']

    xr = Range(100, 0, 0.25)
    yr = Range(100, 0, 16)
    xsize = 0.015 * xr.range
    ysize = 0.015 * yr.range
    marksize = '%f %f' % (xsize, ysize)

    legendx = 0.2
    legendy = 13
    legendanchor = 'hjl vjt'
    legendfontsize = 18
    
    i=0
    curves = []

    for file in files:
        curve = dump_file(file, awk,
                          linetype=linetypes[i],
                          marktype=marktypes[i],
                          marksize=marksize,
                          fill=0.8,
                          linethickness=2,
                          label=String(labels[i]))
        curves.append(curve)
        i += 1


    # create the graph
    titles = String(title, y=yr.loc(1.1))
    xaxis = make_xaxis(xr, yr, xlabel)
    yaxis = make_yaxis(yr, ylabel)
    helv18 = Font('Helvetica', fontsize=18)
    legend = Legend(legendanchor, x=legendx, y=legendy, font=helv18)
    graph = Graph(xaxis=xaxis, yaxis=yaxis, title=titles, legend=legend)

    make_jgr(outfile, graph, curves)
    make_eps(outfile)
    if png:
        make_png(outfile)


if __name__ == '__main__':
    main(*sys.argv)

