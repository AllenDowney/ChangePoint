import sys, getopt, os
from graph import *

"""
Mean annual Nile flow, 1871-1970, units: 10^8 m^3, water yr: july-june
#Original Data Listing:
#78Biomtrka65   243- 252 
# George W. Cobb
# The problem of the Nile: Conditional solution to a changepoint problem
#
#Additional Reference:
#91EnvrMtrc 2   341- 375 
# I. B. MacNeill;S. M. Tang;V. K. Jandhyala
# A search for the source of the Nile's change-points
"""


def main(script, *args):
    # set options
    png = 0
    display = 1

    (opts, args) = getopt.getopt(args, 'dp', ['png', 'display='])
    optdict = {}
    for (key, val) in opts:
        optdict[key] = val

    outfile = os.path.splitext(script)[0]
    print outfile
    fp = open_jgr(outfile)

    # TOP GRAPH
    xlabel = 'time'
    ylabel = 'annual flow (10^9 m^3)'
    title = ''

    gray = ['0.0', '0.0', '0.0']
    linetypes = ['solid', 'dashed', 'longdash', 'dotdash']
    labels = ['data']

    files = ['nile.0']

    xr = Range(100, 1870, 1971)
    yr = Range(100, 0, 160.0)

    legendx = 1960
    legendy = 150
    legendanchor = 'hjr vjt'
    legendfontsize = 18
    
    curves = []
    t1 = 1899, 1899
    t2 = yr.min, yr.max
    curve = dump_lists(t1, t2, gray=0.8, linethickness=2, linetype='dotted')
    curves.append(curve)

    for i, file in enumerate(files):
        curve = dump_file(file,
                          linetype=linetypes[i],
                          linethickness=1,
                          label=String(labels[i]))
        curves.append(curve)

    # create the graph
    titles = String(title, y=yr.loc(1.1))
    xaxis = make_xaxis(xr, yr, xlabel)
    yaxis = make_yaxis(yr, ylabel, size=4)
    helv18 = Font('Helvetica', fontsize=18)
    legend = Legend(legendanchor, x=legendx, y=legendy, font=helv18)
    graph = Graph(xaxis=xaxis, yaxis=yaxis, title=titles, legend=legend)
    write_jgr(fp, graph, curves)

    fp.close()
    
    make_eps(outfile)
    if png:
        make_png(outfile)


if __name__ == '__main__':
    main(*sys.argv)

