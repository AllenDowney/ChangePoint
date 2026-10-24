import sys
from math import *
from random import *

def trimmed_average(t, percent=0.01):
    # compute the average of the elements in t, excluding the
    # top percent
    t = t[:]
    t.sort()
    trim = int(round(percent * len(t)))
    trim = max(trim, 1)
    t = t[:-trim]
    return 1.0 * sum(t) / len(t)

def generate_data(mus=[0, 1], sigma=1.0, n=100):
    t = []
    for mu in mus:
        t.extend([normalvariate(mu, sigma) for i in xrange(n)])
    return t

def cumulant(t):
    """return the cumulant sum of t (backward)
    """
    s = t[:]
    sum = 0
    for i in range(len(t)-1,-1,-1):
        sum += t[i]
        s[i] = sum
    return s
        
def calc_gk(t, k, mu0, sigma):
    """calculate gk with numin=0.0, using Equation 2.4.40 on
    page 53 of Basseville and Nikiforov
    """

    t2 = [y-mu0 for y in t]
    t3 = cumulant(t2)

    t4 = t3[:]
    for j in range(k):
        t4[j] = t3[j]**2 / (k-j+1)

    gk = max(t4) / 2.0 / sigma / sigma
    return gk
    

def calc_gk(t, k, mu0, sigma, numin=0.1):
    """calculate gk with the given numin, using Equation 2.4.38 on
    page 53 of Basseville and Nikiforov
    (k is the highest index you're allowed to look at)
    """
    n = k+1
    t = t[:n]
    
    # compute the signum of the sum of centered observations
    co = cumulant([y-mu0 for y in t])
    s1 = [signum(x) for x in co]

    # compute estimated nu for all j
    t2 = cumulant([abs(y-mu0) - numin for y in t])
    t3 = [t2[j] / (k-j+1) for j in range(n)]
    t4 = [max(x, 0) + numin for x in t3]

    # sign of nuhat[j] should be the same as s1[j]
    nuhat = [s1[j] * abs(t4[j]) for j in range(n)]

    t5 = [(co[j] - nuhat[j]/2*(k-j+1)) * nuhat[j]
          for j in range(len(nuhat))]

    gk = max(t5) / sigma**2
    return gk
    

def signum(x):
    if x<0: return -1
    if x>0: return 1
    return 0


def test_true_alarm(rseed, threshes, sigma=1.0):
    """rseed is a random seed; threshes is a set of thresholds.
    Return a dictionary that maps from a
    threshold in threshes to the time the alarm triggered
    that threshold.
    """
    # generate data
    seed(rseed)
    mu0 = 0
    mus = [mu0, 1, 1, 1, 1]
    n = 50
    t = generate_data(mus, sigma, n)

    # tba is time before alarm
    tba = {}
    for thresh in threshes:
        tba[thresh] = float('Inf')
            
    # iterate through the data until all the thresholds have
    # been reached
    for k in range(0, len(t)):
        gk = calc_gk(t, k, mu0, sigma)

        sys.stderr.write('%d\t%d\t%f\t%d\n' % (rseed, k, gk, len(threshes)))

        # we have to make a copy of threshes so we can modify
        # the original inside the loop
        for thresh in set(threshes):
            if gk > thresh:
                # print k, gk, thresh
                tba[thresh] = k
                threshes.remove(thresh)

        if not threshes: break

    return tba


def alarm_time(threshes, runs=100, sigma=1.0):
    """run test_true_alarm the given number of times with
    the given sigma.
    Returns complete, farate, mat (see below).
    """

    # tbas maps from a threshold to a list of "time before alarm"
    tbas = {}
    for thresh in threshes:
        tbas[thresh] = []

    for i in range(runs):
        d = test_true_alarm(i, set(threshes), sigma)

        # d maps from a threshold to a single time before alarm
        for thresh, i in d.iteritems():
            tbas[thresh].append(i)

    complete = {}     # fraction of runs that generated an alarm
    farate = {}       # fraction of runs that had a false alarm
    mat = {}          # mean alarm time of runs that didn't fa

    for thresh in threshes:
        complete[thresh] = 1.0 * len(tbas[thresh]) / runs

        # count the number of false alarms and make a list
        # of time before alarm for runs that didn't fa
        fa = 0
        t = []
        for k in tbas[thresh]:
            if k <= 50:
                fa += 1
            else:
                t.append(k-50)

        # compute farate and mat
        farate[thresh] = 1.0 * fa / runs
        if len(t):
            mat[thresh] = trimmed_average(t)
        else:
            mat[thresh] = None

    return complete, farate, mat




def mta_vs_thresh(threshes, runs=100, sigma=1.0):
    complete, farate, mat = alarm_time(threshes, runs, sigma)

    for thresh in threshes:
        print thresh, complete[thresh], farate[thresh], mat[thresh]



def main():
    threshes = [4.8 + 0.2*i for i in range(20)]

    mta_vs_thresh(threshes, runs=100)
    
    #mta_vs_sigma(threshes, runs=10)


if __name__ == '__main__':
    main()
