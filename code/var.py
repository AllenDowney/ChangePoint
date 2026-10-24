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

    outfile = os.path.splitext(script)[0]        
    fp = open_jgr(outfile)

    # TOP GRAPH
    xlabel = 'index'
    ylabel = ''
    title = ''

    gray = ['0.0', '0.0', '0.0']
    linetypes = ['solid', 'dashed', 'longdash', 'dotdash']
    labels = ['data']

    files = ['var.0']

    xr = Range(100, -1, 120)
    yr = Range(100, -4.1, 4.1)

    legendx = 90
    legendy = 3.2
    legendanchor = 'hjl vjt'
    legendfontsize = 18
    
    curves = []
    t1 = 40, 40
    t2 = yr.min, yr.max
    curve = dump_lists(t1, t2, gray=0.8, linethickness=2)
    curves.append(curve)

    t1 = 80, 80
    curve = dump_lists(t1, t2, gray=0.8, linethickness=2)
    curves.append(curve)
    
    for i, file in enumerate(files):
        curve = dump_file(file,
                          linetype=linetypes[i],
                          linethickness=1,
                          label=String(labels[i]))
        curves.append(curve)

    # create the graph
    titles = String(title, y=yr.loc(1.1))
    xaxis = make_xaxis(xr, yr, xlabel,
                       'no_draw_axis_label', 'no_draw_hash_labels')
    yaxis = make_yaxis(yr, ylabel, size=4)
    helv18 = Font('Helvetica', fontsize=18)
    legend = Legend(legendanchor, x=legendx, y=legendy, font=helv18)
    graph = Graph(xaxis=xaxis, yaxis=yaxis, title=titles, legend=legend)
    write_jgr(fp, graph, curves)

    # BOTTOM GRAPH
    ylabel = 'cumulative probability'
    title = ''

    gray = ['0.0', '0.0', '0.0']
    linetypes = ['solid', 'dashed', 'longdash', 'dotdash']
    labels = ['P(i+)', 'P(i++)']

    files = ['var.p0', 'var.pp0']

    yr = Range(100, -0.1, 1.1)
    legendy = 0.95
    
    curves = [None] * len(files)
    for i, file in enumerate(files):
        curves[i] = dump_file(file,
                             linetype=linetypes[i],
                             linethickness=2,
                             label=String(labels[i]))

    # create the graph
    titles = String(title, y=yr.loc(1.1))
    xaxis = make_xaxis(xr, yr, xlabel)
    yaxis = make_yaxis(yr, ylabel, size=4)
    legend = Legend(legendanchor, x=legendx, y=legendy, font=helv18)
    graph = Graph(xaxis=xaxis, yaxis=yaxis, title=titles, legend=legend,
                  y_translate=-4.5)
    write_jgr(fp, graph, curves)


    fp.close()
    
    make_eps(outfile)
    if png:
        make_png(outfile)


if __name__ == '__main__':
    main(*sys.argv)

