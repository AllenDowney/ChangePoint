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
    xlabel = 'serial number'
    ylabel = 'cumulative probability'
    title = 'Changepoint probability'
    outfile = 'series'

    gray = ['0.7', '0.0']
    marktypes = ['circle', 'box', 'diamond', 'triangle', 'ellipse', 'x']
    linetypes = ['dotted', 'solid', 'dashed', 'longdash', 'dotdash',
                 'dotdotdash', 'dotdotdashdash'] 

    roots = ['data', 'prob']
    sigma = '1.0'
    files = ['%s.%s' % (root, sigma) for root in roots]

    (xr, yr) = range_files(files, awk)
    xsize = 0.02 * xr.range
    ysize = 0.02 * yr.range
    marksize = '%f %f' % (xsize, ysize)

    legendx = 100
    legendy = -3
    legendanchor = 'hjr vjb'
    legendfontsize = 18

    i=0
    curves = []

    for file in files:
        curve = dump_file(file, awk,
                          linetype=linetypes[i],
                          linethickness=2,
                          gray=gray[i],
                          label=String(roots[i]))
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

