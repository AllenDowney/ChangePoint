import sys
from math import *
from random import *
from Hist import *

class Hypo:
    def __init__(self, p, theta):
        self.p = p
        self.theta = theta

    def __str__(self):
        return str(self.theta) + '   ' + str(self.p)

    def likelihood(self, data):
        """compute the probability of this data given this hypothesis;
        subclasses must override this method
	"""
        return None

    def update(self, data):
        """update p based on the given data
	"""
        self.p *= self.likelihood(data)

    def normalize(self, nc):
        self.p /= nc


class DecayHypo(Hypo):
    """this is the Hypothesis that the decay constant in MacKay's
    problem 3.3 is lambda=self.theta
    """
    def likelihood(self, data):
        """compute the probability of this data given this hypothesis
	"""
        lamb = self.theta
        Z = exp(-1.0/lamb) - exp(-20.0/lamb)

        like = 1.0
        for x in data:
            like *= exp(-x/lamb) / lamb / Z
        return like


class CompoundHypo(Hypo):
    """for a compound hypothesis, theta is a collection and p is
    the sum of the probabilities of the sub-hypotheses.  A compound
    hypothesis is normalized if p=sum of sub-hypotheses=1.0 
    """
    def update(self, data):
        """update this hypothesis based on the given data
	"""
	for h in self.theta:
	    h.update(data)

	self.p = self.normalizing_constant()

    def add(self, h):
        """add an additional hypothesis to this compound
        """
        self.theta.append(h)

    def remove(self, h):
        """add an additional hypothesis to this compound
        """
        self.theta.remove(h)

    def normalizing_constant(self):
        return sum([h.p for h in self.theta])

    def normalize(self):
        nc = self.normalizing_constant()
	for h in self.theta:
	    h.normalize(nc)
        self.p = 1.0

    def __iter__(self):
        for h in self.theta:
            yield h

    def dump(self, fp=None):
        total = 0
        for h in self.theta:
            total += h.p
            s = str(h) + '\t' + str(total) + '\n'
            if fp:
                fp.write(s)
            else:
                print s,


from mdict import mdict

class ChangeDict(dict):
    """a dictionary that maps from an
    index i to the probability that there is a changepoint at i
    """
    def update(self, ch):
        """update the p(i) based on the collection of p(i|j) in
        ch, which is a ChangeHypo
        """

        # md maps from i to a list of tuples (j, p(i|j))
        md = mdict()
        for h in ch.theta:
            j, i = h.w1.i, h.w2.i
            md[i] = (j, h.p)

        t = md.items()
        t.sort()
        for i, u in t:
            self[i] = 0
            for j, pij in u:
                pj = self.get(j, 1)
                self[i] += pj * pij 

        self.normalize()

    def normalize(self):
        nc = sum(self.values())
        for i in self:
            self[i] /= nc

    def dump(self):
        for i, p in self.iteritems():
            print i, p


class ChangeHypo(CompoundHypo):
    """a compound hypothesis where theta is a list of WindowHypos
    """
    def __init__(self, n=100):
        self.n = n
        self.theta = []

    def dump(self, fp=None):
        t = [(h.w2.i, h) for h in self.theta]
        t.sort()

        total = 0
        for i, h in t:
            total += h.p
            #print h.w1.i, h.w2.i, h.p 
            
            s = '%d\t%f\n' % (i, total)
            if fp:
                fp.write(s)
            else:
                print s,

    def choice(self, n=1000):
        """draw a sample from this hypothesis by sampling from each of
        the subhypothesis in proportion to their probabilities.
        Precondition: the hypothesis has been normalized.
        """
        t = []
        for h in self.theta:
            k = int(round(n * h.p))
            w1, w2 = h.theta
            print w1.n, k
            if k:
                s = h.choice(k)
                t.extend(s)
        return t

    def update(self, series):
        """update the existing hypothesis, possibly creating some new
        ones and deleting old ones.  series is the Series object this
        ChangeHypo belongs to
        """
        index = series.n - 1                 # index of the last data point
        data = series.data
        x = data[-1]
        
        for h in self.theta:
            h.update(x)

        if len(self.theta) == 0:
            wh = make_window_hypo(index, data)
            self.add(wh)
            return

        # choose X hypotheses at random and sort them by probability
        hs = [choice(self.theta) for j in range(3)]
        phs = [(h.p, h) for h in hs]
        phs.sort()
        phs.reverse()

        # make a new hypothesis
        p, old = phs[0]
        wh = make_wh_copy(index, old, data)

        for p, old in phs:
            wh = make_wh_split(index, old, data)
            if wh:
                self.add(wh)
                break

        # if there are not enough hypotheses, add an extra one
        if len(self.theta) < self.n:
            wh = make_wh_nosplit(index, old, data)
            self.add(wh)


        # if there are enough hypotheses, remove two
        if len(self.theta) > self.n:
            # remove the lowest probability of the ones we saw
            p, dead = phs[-1]
            self.remove(dead)
            
            # remove the lowest index of the ones we saw
            ihs = [(h.w1.i, h) for h in hs]
            ihs.sort()
            for i, dead in ihs:
                try:
                    self.remove(dead)
                    break
                except ValueError:
                    continue


class Discount(dict):
    """compute the discount factor for a window hypothesis with
    n1 and n2 points (and keep previous computations around for
    future reference)
    """
    
    def lookup(self, n1, n2):
        if n1 < 6 or n2 < 6: return 0

        if n1 < n2:
            n1, n2 = n2, n1
            
        try:
            return self[n1, n2]
        except KeyError:
            t1 = n1**2 * log(1 + 2.0/(n1-5))
            t2 = n2**2 * log(1 + 2.0/(n2-5))
            std = 2.0 * sqrt(t1 + t2)
            self[n1, n2] = std
            return std

    def look2(self, n):
        return self.lookup(n, n) / sqrt(2)
    
discount = Discount()

class Slider:
    """each slider is based on the assumption that there is a breakpoint
    at (before) index, and computes the probabilities p(i|index) for each
    i between index+2 and t-2, where t is the index of the most recent x
    """
    def __init__(self, index):
        self.index = index
        self.S1 = []
        self.S2 = []

    def update(self, x):
        x2 = x*x
        for i in xrange(len(self.S1)):
            self.S1[i] += x
            self.S2[i] += x2

        self.S1.append(x)
        self.S2.append(x2)

    def moments(self, i):
        """return the moments of the set of points to the right of i
        """
        n = len(self.S1)
        return n-i, self.S1[i], self.S2[i]
            
    def likelihood(self):
        S1, S2 = self.S1, self.S2
        n = len(S1)
        self.like = [0] * n
        if n < 4: return

        # compute the priors
        for i in xrange(2,n-1):
            self.like[i] = discount.lookup(i, n-i) 
            self.like[i] = 1.0

        # p0 is the probability that there is no changepoint
        f = 0.01
        p0 = pow(1-f, n)

        # normalize the priors
        self.normalize(1-p0)

        # like[0] is not actually the likelihood that there is
        # a changepoint at index 0; it is a convenient storage
        # spot for the likelihood that there is no changepoint.
        self.like[0] = 1 - sum(self.like)

        # compute the posterior that there is no changepoint
        m0 = self.moments(0)
        like0 = likelihood(*m0)
        std = discount.look2(n)            
        self.like[0] *= exp(like0)

        print self.index, self.like[0] 

        # for each value of i, compute the likelihood(i|self.index)
        for i in xrange(2,n-1):
            m2 = self.moments(i)
            m1 = sub_moments(m0, m2)
            like1 = likelihood(*m1)
            like2 = likelihood(*m2)
            n1, n2 = m1[0], m2[0]
            assert(n1 == i)

            self.like[i] *= exp(like1+like2)

        self.normalize()

        return
        if self.index % 20 == 0:
            print '\n#', self.index
            for i, x in enumerate(self.like):
                print i+self.index, x




    def normalize(self, factor=1.0):
        nc = sum(self.like) / factor
        if nc == 0: return
        for i in xrange(len(self.like)):
            self.like[i] /= nc

    def likelihood2(self):
        S1, S2 = self.S1, self.S2
        n = len(S1)
        self.like2 = [[0]] * n
        if n < 4: return

        # compute the priors
        for i in xrange(0,n-1):
            n1 = i
            self.like2[i] = [0] * n
            if i<2: continue
            
            for k in xrange(i+2, n-3):
                n2 = k-i
                self.like2[i][k] = 1.0 / discount.lookup(n1, n2) 
 
        # the prior probability that there is no changepoint, for each k
        f = 0.01
        p0 = [pow(1-f, k) for k in xrange(n)]

        # normalize the priors
        for k in xrange(2, n-1):
            nc = sum([self.like2[i][k] for i in xrange(k-1)]) / p0[k]

            if nc == 0: continue
            for i in xrange(k-1):
                self.like2[i][k] /= nc

        # store the p0 in the first row of like2
        for k in xrange(2, n-1):
            self.like2[0][k] = p0[k]
            
        # for each value of i, compute the likelihood(i|self.index)
        m = self.moments(0)
        for i in xrange(2,n-1):
            mi = n-i, S1[i], S2[i]
            m1 = sub_moments(m, mi)
            like1 = likelihood(*m1)
            n1 = m1[0]
            assert(n1 == i)
            
            for k in xrange(i+2, n-3):
                mk = n-k, S1[k], S2[k]
                m2 = sub_moments(mi, mk)
                like2 = likelihood(*m2)
                n2 = m2[0]
                assert(n1 == i)
                
                self.like2[i][k] *= exp(like1+like2)

        # the probability that there is no changepoint between
        # 0 and k is based on the likelihood of mnk
        for k in range(2, n-1):
            mk = self.moments(k)
            mnk = sub_moments(m, mk)
            like0 = likelihood(*mnk)
            self.like2[0][k] *= exp(like0)

        # normalize the likelihoods (making them probabilities)
        self.normalize2()

        if self.index % 30 == 0 and False:
            print '\n#', self.index
            for i, like in enumerate(self.like):
                if i>0 and like>0:
                    print self.index+i, like


    def normalize2(self):
        n = len(self.like)

        # for each value of k, normalize across the values
        # of i, where i==0 is a special location that contains
        # the probability that there is no breakpoint before k.
        for k in xrange(2,n):
            nc = 0
            for i in xrange(k-1):
                nc += self.like2[i][k]

            if nc == 0: continue
            for i in xrange(k):
                self.like2[i][k] /= nc

    def pij(self, i):
        """return the probability that there is a breakpoint at i,
        given the assumption of this slider that there was a
        breakpoint at self.index (j).

        Precondition: likelihood has run since the last update.
        """
        i2 = i-self.index
        return self.like[i2]
    
    def pijk(self, i, k):
        """return the probability that there is a breakpoint at i,
        given the assumption of this slider that there was a
        breakpoint at self.index (j), and the additional assumption
        that there is a breakpoint at k.

        Precondition: likelihood has run since the last update.
        """
        i2 = i-self.index
        k2 = k-self.index
        return self.like2[i2][k2]
    
    
class WindowHypo(Hypo):
    """the hypothesis that there is a changepoint in the data
    between the Windows w1 and w2, given that there was a changepoint
    at the beginning of w1.
    """
    def __init__(self, w1, w2):
        self.w1 = w1
        self.w2 = w2
        self.p = self.likelihood()

    def likelihood(self):
        """compute the probability of this data given this hypothesis.
        the data are stored inside the windows, so they are not
        passed as parameters
	"""
        m1 = self.w1.moments()
        m2 = self.w2.moments()
        n2 = m2[0]
        m = add_moments(m1, m2)
        like0 = likelihood(*m)
        
        like1 = self.w1.likelihood()
        like2 = self.w2.likelihood()
        return exp(like0-like1-like2)+sqrt(n2)

    def update(self, x):
        """add a new data point to this hypothesis and recompute likelihood
        """
        self.w2.add(x)
        self.p = self.likelihood()

    def __str__(self):
        return '%d\t%g' % (self.w2.i, self.p)

    def choice(self, n=1):
        """return n choices from w2"""
        t = [choice(self.w2.data) for i in xrange(n)]
        return t

    def sample(self, n=1):
        """estimate the parameters of w2 and generate a sample
        from the corresponding t distribution
        """

def make_window(index, t):
    """make a new window with the given index and the moments of t"""
    return Window(index, *calc_moments(t))

def make_window_hypo(index, t):
    """make a new window hypothesis with two points in w2 and
    the rest in w1 (this should only be invoked to make the
    first hypothesis, with 4 data points)
    """
    t1 = t[:-2]
    t2 = t[-2:]
    i1 = index-len(t)+1
    i2 = index-1
    w1 = make_window(i1, t1)
    w2 = make_window(i2, t2)
    wh = WindowHypo(w1, w2)
    return wh


def make_wh_copy(index, old, t):
    """make a new window hypo that is a copy of old
    """
    wh = WindowHypo(old.w1, old.w2)
    return wh


def make_wh_split(index, old, t):
    """make a new window hypo based on the assumption that the old
    one is true, using the most recent data
    """
    # the new w2 contains the most recent two points
    t2 = t[-2:]
    c2 = calc_moments(t2)
    i2 = index-1
    w2 = Window(i2, *c2)

    # the new w1 is the same as the old w2 except that we have to
    # subtract the last two data points, since they
    # will be in the new w2
    cold2 = old.w2.moments()
    n, s1, s2 = sub_moments(cold2, c2)

    # if the new w1 would have fewer than 2 points, bail out
    if n < 2: return None

    i1 = old.w2.i
    w1 = Window(i1, n, s1, s2)
    wh = WindowHypo(w1, w2)
    return wh


def make_wh_nosplit(index, old, t):
    """make a new window hypo based on the assumption that the old
    one is false, using the most recent data
    """
    # the new w2 contains the most recent two points    
    t2 = t[-2:]
    c2 = calc_moments(t2)
    i2 = index-1
    w2 = Window(i2, *c2)

    # the new w1 is the sum of the old w1 and w2, minus
    # the two points we just stole
    cold1 = old.w1.moments()
    cold2 = old.w2.moments()

    c1 = add_moments(cold1, cold2)
    c1 = sub_moments(c1, c2)
    i1 = old.w1.i

    w1 = Window(i1, *c1)
    wh = WindowHypo(w1, w2)
    return wh



class Window:
    """a window represents a subset of a time series.  It keeps
    track of its indices into the series, and summary statistics
    that can be updated incrementally.
    """
    def __init__(self, i, n, s1, s2):
        if i<0: raise Error
        self.i = i
        self.n = n
        self.s1 = s1
        self.s2 = s2

    def remove(self, x):
        self.n -= 1
        self.s1 -= x
        self.s2 -= x**2

    def add(self, x):
        self.n += 1
        self.s1 += x
        self.s2 += x**2

    def likelihood(self):
        return likelihood(self.n, self.s1, self.s2)

    def moments(self):
        return self.n, self.s1, self.s2

def likelihood(n, s1, s2):
    mu = s1 / n
    var = s2 / n - mu**2
    sigma = sqrt(var)
    like = -n * log(sigma)
    return like

def calc_moments(t):
    n = len(t)
    s1 = sum(t)
    s2 = sum([z*z for z in t])
    return n, s1, s2

def add_moments(c1, c2):
    """return the sum of two moment vectors"""
    return [m1+m2 for m1, m2 in zip(c1, c2)]

def sub_moments(c1, c2):
    """return the difference of two moment vectors"""
    return [m1-m2 for m1, m2 in zip(c1, c2)]

    
class Series:
    def __init__(self):
        self.n = 0
        self.data = []
        #self.ch = ChangeHypo(100)
        #self.cd = ChangeDict()
        self.sliders = {}
        
    def add(self, x):
        self.n += 1
        self.data.append(x)

        i = self.n-1
        self.sliders[i] = Slider(i)

        for sl in self.sliders.itervalues():
            sl.update(x)

        #if self.n < 4: return        
        #self.ch.update(self)
        #self.cd.update(self.ch)


    def process(self, p=False, pp=False):
        if self.n<10: return
        
        for sl in self.sliders.itervalues():
            sl.likelihood()

        self.calc_prob()
        if p: self.print_p()
        self.calc_pp()
        if pp: self.print_pp()
    
    def process2(self, p=False, pp=False):
        if self.n<10: return

        for sl in self.sliders.itervalues():
            sl.likelihood2()

        self.calc_prob2()
        if p: self.print_p()
        self.calc_pp()
        if pp: self.print_pp()

    
    def calc_prob(self):
        """each slider corresponds to the hypothesis that there is
        a breakpoint at j.  The jth slider can compute p(i|j) for any i

        The probability of a breakpoint at i is
        p(i) = sum_i p(i|j) * p(j)  for all j less than i
        """
        n = self.n
        p = [0] * n
        pp = [0] * n
        self.p = p
        self.pp = pp

        p[0] = 1
        for i in range(2,n):
            for j in range(i-1):
                pij = self.sliders[j].pij(i)
                p[i] += p[j] * pij

 
    def calc_prob2(self):
        """each slider corresponds to the hypothesis that there is
        a breakpoint at j.

        The jth slider can compute p(i|j,k) for any i, k

        The probability of a breakpoint at i is
        p(i) = sum_i p(i|j,k) * p(j) * p(k)

        for all j less than i and all k > i

        Precondition: self.p and self.pp exist
        """
        n = self.n
        p = self.p
        
        for i in range(1,n):
            p[i] = 0
            for j in range(0, i-1):
                for k in range(i+1, n):
                    pijk = self.sliders[j].pijk(i,k)
                    p[i] += pijk * p[j] * p[k]

        return

        # normalize the posteriors so that they integrate to
        # n*f, the expected number of changepoints
        f = 0.01
        factor = n * f
        nc = (sum(p) - p[0]) / factor
        for i in xrange(1, n):
            p[i] /= nc

        p[0] = pow(1-f, n)


    def calc_pp(self):
        n = self.n
        p = self.p
        pp = self.pp

        factor = 1
        nc = 0
        for i in range(n-1, -1, -1):
            pp[i] = p[i] * factor
            nc += pp[i]
            factor *= 1-p[i]

        for i in range(0, n):
            pp[i] /= nc

    def print_p(self):
        n = self.n
        p = self.p

        print '\n#prob'
        total = 0
        for i in range(0, n):
            total += p[i]
            print i, p[i]
            #print i, total

    def print_pp(self):
        n = self.n
        pp = self.pp

        print '\n#prob+'
        total = 0
        for i in range(n-1, -1, -1):
            total += pp[i]
            #print i, pp[i]
            print i, total
 
def generate_data(sigma=1, n=100):
    seed(10)
    t = [normalvariate(1,sigma) for i in xrange(n)]
    t += [normalvariate(-1,sigma) for i in xrange(n)]
    t += [normalvariate(-1,sigma) for i in xrange(n)]
    #t += [normalvariate(0,sigma) for i in xrange(n)]
    return t


def generate_trend_data(sigma=1, n=100):
    t = []
    for i in range(n):
        mu = 1.0 * i / n
        x = normalvariate(mu,sigma)
        t.append(x)
    return t


def test_changepoint(sigma=1):
    t = generate_data(sigma, n=50)
    #t = generate_trend_data(sigma)

    filename = 'data.' + str(sigma)
    fp = open(filename, 'w')
    for i, x in enumerate(t):
        s = '%d\t%f\n' % (i, x)
        fp.write(s)
    fp.close()
        
    series = Series()

    for i, x in enumerate(t):
        series.add(x)
        if i % 30 == 0 and False:
            series.process()
            series.process2(pp=True)

    series.process(p=True)
    #series.process2(p=True, pp=True)

    #series.ch.normalize()

    #filename = 'prob.' + str(sigma)
    #fp = open(filename, 'w')
    #series.ch.dump(fp)
    #fp.close()

    #series.cd.dump()


    return
    
    t = series.ch.choice(1000)

    filename = 'pred.' + str(sigma)
    fp = open(filename, 'w')
    for x in t:
        s = str(x) + '\n'
        fp.write(s)
    fp.close


def avgstd(t):
    """return the mean and standard deviation of a sequence of
    values"""
    n = len(t)
    mu = sum(t) / n
    var = sum([(x-mu)**2 for x in t]) / n
    sigma = sqrt(var)
    return n, mu, sigma
    

def make_uniform(n=10):
    """make a hypothesis with n equally spaced micro-hypotheses
    between lam=0+e and lam=100, all with the same prior likelihood
    """

    lambs = [100.0 * (i+1) / n for i in range(n)]
    hypos = [DecayHypo(1.0, lamb) for lamb in lambs]
    h = CompoundHypo(1.0, hypos)
    h.normalize()
    return h


def decay_problem():

    # make a uniform prior
    h = make_uniform(1000)

    # the data from page 49
    data = [1.5, 2, 3, 4, 5, 12]

    # update the distribution and normalize
    h.update(data)
    h.normalize()

    # print the posterior distribution on logx scale
    for hypo in h:
        print hypo


def single_dirichlet(X):
    """select a set of parameters from the Dirichlet distribution
    with parameters X; for an explanation of the algorithm, see
    http://en.wikipedia.org/wiki/Dirichlet_distribution
    """
    Y = [gammavariate(x, 1) for x in X]
    denom = sum(Y)
    Z = [y/denom for y in Y]
    return Z

def sample_dirichlet(X, n=1):
    """return a list with length n of samples from
    the Dirichlet distribution with parameters X
    """
    return [single_dirichlet(X) for i in xrange(n)]


def test_dirichlet(n=1000):
    """generate data similar to the figure on page 84 of Bayesian
    Data Analysis (Example on Pre-election polling)
    """
    X = [728, 584, 138]

    h = Hist()
    for i in xrange(n):
        Z = single_dirichlet(X)
        diff = Z[0] - Z[1]
        h.count(diff)

    for x, f in h.cdf():
        print x, f


def test_conjecture(n=100):
    """this is a quick check of a conjecture, because I was too
    lazy to do the algebra
    """
    X = [uniform(0,10) for i in xrange(n)]
    n, mu, sigma = avgstd(X)
    print n, mu, sigma
    Z = [(x-mu) / sigma for x in X]
    s = sum([z*z for z in Z])
    print s



def main(name, sigma='1', *args):
    #decay_problem()
    #test_dirichlet()

    sigma = float(sigma)
    test_changepoint(sigma)


    
if __name__ == '__main__':
    main(*sys.argv)
    #import profile
    #profile.run('main(*sys.argv)','prof')


    
