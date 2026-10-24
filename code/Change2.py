import sys
from math import *
from random import *

class Slider:
    """each slider is based on the assumption that there is a breakpoint
    at (before) index, and computes the probabilities p(i|index) for each
    i between index+2 and t-2, where t is the index of the most recent x
    """
    def __init__(self, index):
        self.index = index
        self.n = 0
        self.S1 = []
        self.S2 = []

    def update(self, x):
        x2 = x*x
        for i in xrange(self.n):
            self.S1[i] += x
            self.S2[i] += x2

        self.n += 1
        self.S1.append(x)
        self.S2.append(x2)

    def moments(self, i):
        """return the moments of the set of points to the right of i
        """
        return self.n-i, self.S1[i], self.S2[i]
            
    def likelihood(self):
        n, S1, S2 = self.n, self.S1, self.S2
        self.like = [0] * n
        if n < 4: return
        m0 = self.moments(0)

        # for each value of i, compute the likelihood(i+|j++)
        # where j = self.index
        for i in xrange(2,n-1):
            m2 = self.moments(i)
            m1 = sub_moments(m0, m2)
            like1 = likelihood(*m1)
            like2 = likelihood(*m2)
            #n1, n2 = m1[0], m2[0]

            self.like[i] = exp(like1+like2)
            #self.like[i] = 1.0

        self.like[1] = self.like[2]
        self.like[-1] = self.like[-2]
        self.normalize()

    def normalize(self, factor=1.0):
        nc = sum(self.like) / factor
        if nc == 0: return
        for i in xrange(self.n):
            self.like[i] /= nc

    def dump(self):
        print '\n#', self.index
        total = 0
        for i, x in enumerate(self.like):
            total += x
            print i+self.index, total

    def pjpp(self, i):
        """return p(i+|j++)

        Precondition: likelihood has run since the last update.
        """
        return self.like[i-self.index]
    
    

def likelihood(n, s1, s2):
    mu = s1 / n
    var = s2 / n - mu**2
    #sigma = sqrt(var)
    like = -n * log(var) / 2
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
    a, b, d = c1
    e, f, g = c2
    return [a-e, b-f, d-g]
    #return [c1[i]-c2[i] for i in range(3)]
    #return [m1-m2 for m1, m2 in zip(c1, c2)]


class Estimate:
    def __init__(self, n, p, pp):
        self.n = n
        self.p = p
        self.pp = pp

    def ppkp(self, i):
        return self.pp[i]

    def dump(self):
        print '\n#', self.n
        for i, x in enumerate(self.p):
            print i, x

        print '\n#', self.n
        for i, x in enumerate(self.pp):
            print i, x

    def calc_xp(self):
        # xp is the cumulative sum of p
        p = self.p
        xp = p[:]
        total = 0
        for i in range(-1, -self.n, -1):
            total += p[i]
            xp[i] = total

        self.xp = xp

def copy_est(previous, f):
    n = previous.n + 1
    p = previous.p[:] + [f]
    pp = previous.pp[:] + [0]
    return Estimate(n, p, pp)

        


class Series:
    def __init__(self):
        self.n = 0
        self.f = 0.01
        self.data = []
        self.sliders = {}
        self.estimates = {}
        self.init_est()
        self.prior = self.make_est(500)
        self.prior.calc_xp()
        
        return
        total = 0
        for i in range(150):
            pip = self.prior.p[-150+i]
            total += pip
            print i, total


    def init_est(self):
        """initialize the first three elements of self.estimates
        """
        for i in range(1,4):
            self.estimates[i] = self.make_est(i)

        
    def make_est(self, n):
        """make estimates of p and pp based on no data, only the
        prior probability, f, of a changepoint at any time.
        """
        #p = [0] * n
        pp = [0] * n
        f = self.f
        
        #print '\n#'
        #total = 0
        p = [f * pow(1-f, n-i-1) for i in range(n)]
        
        #for i in range(n):
        #    p[i] = f * pow(1-f, n-i-1)
        #total += p[i] * (n-i)
            #print i, p[i] 

        #print '\n#'
        #total = 0
        for i in range(n-1):
            t = [p[k] * f * pow(1-f, k-i-1)
                 for k in range(i+1, n)]
            pp[i] = sum(t)
            #total += pp[i] * (n-i)
            #print i, pp[i] 
                
        #print total
        return Estimate(n, p, pp)

    
    def add(self, x):
        self.n += 1
        self.data.append(x)

        i = self.n-1
        self.sliders[i] = Slider(i)

        for sl in self.sliders.itervalues():
            sl.update(x)


    def process(self, p=False, pp=False):
        for sl in self.sliders.itervalues():
            sl.likelihood()

        self.calc_prob()
        #if p: self.print_p()
        #self.calc_pp()
        #if pp: self.print_pp()
    

    def calc_prob(self):
        """each slider corresponds to the hypothesis that the second
        breakpoint is at j.

        The jth slider can compute p(i+|j++) for any i
        
        p(i+) = sum_j p(i+|j++) * p(j++)  for all j less than i
        """
        n = self.n
        
        if n < 4: return

        previous = self.estimates[n-1]
        
        self.estimates[n] = copy_est(previous, self.f)
        #self.estimates[n] = self.make_est(n)

        for i in range(1):
            self.iterate_est(n)


    def iterate_est(self, n):
        est = self.estimates
        p = est[n].p
        pp = est[n].pp
        f = self.f
        prior_p = self.prior.p
        prior_pp = self.prior.pp
        prior_xp = self.prior.xp
        sliders = self.sliders

        #print '\nn=', n, tp
        
        # update p
        tp = sum(p)
        ctp = 1-tp
        pjpp = [sliders[0].pjpp(i) * tp for i in range(0, n-1)]
        
        for i in range(0, n-1):
            t = [pp[j] * sliders[j].pjpp(i) for j in range(0, i-1)]
            p[i] = sum(t)

            #p[i] = 0
            #for j in range(0, i-1):
            #    ppj = pp[j]
            #    pjpp = sliders[j].pjpp(i)
            #    p[i] += ppj * pjpp

            #print i, p[i],

            t = [(tp * prior_p[j] + ctp * prior_pp[j]) *
                 pjpp[i] / (tp + prior_xp[j])
                 for j in range(-1, -500, -1)]
            p[i] += sum(t)

            #for j in range(-1, -500, -1):
            #    ppj = tp * prior_p[j] + (1-tp) * prior_pp[j]
            #    pjpp = pjpp[i] * tp / (tp + prior_xp[j])
            #    p[i] += ppj * pjpp
            #    print i, j, ppj, pjpp, tp+xp

            #print p[i]

        # for values that can't be computed with data,
        # fill in priors
        # p[-1] = f
        # p[1] = 0
        # p[0] = 0 


        # update pp
        for i in range(0,n-2):
            t = [p[k] * est[k].pp[i] for k in range(i+1, n)]
            pp[i] = sum(t)

            #pp[i] = 0
            #for k in range(i+1, n):
            #    ppkp = est[k].ppkp(i)
            #    pp[i] += p[k] * ppkp
            #print n, i, pp[i]
            
        # for values that can't be computed with data,
        # fill in priors
        # pp[-1] = 0
        pp[-2] = f * (1-p[-1])


#        for i in range(n):
#            print n, i, pp[i]
 
#        for i in range(n):
#            print n, i, p[i]
 

    def print_like(self, step=10):
        n = self.n
        for i in xrange(0, n, step):
            self.sliders[i].dump()


    def print_p(self):
        n = self.n
        p = self.estimates[n].p

        print '\n#prob'
        total = 0
        for i in range(n-1, -1, -1):
            total += p[i]
            #print i, p[i]
            print i, total


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
    seed(12)
    t = [normalvariate(0,sigma) for i in xrange(n)]
    t += [normalvariate(0,sigma) for i in xrange(n)]
    #t += [normalvariate(0,sigma) for i in xrange(n)]
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
        series.process()
        
    #series.print_like()
    series.print_p()

    return
    
    t = series.choice(1000)

    filename = 'pred.' + str(sigma)
    fp = open(filename, 'w')
    for x in t:
        s = str(x) + '\n'
        fp.write(s)
    fp.close




def main(name, sigma='1', *args):
    #decay_problem()
    #test_dirichlet()

    sigma = float(sigma)
    test_changepoint(sigma)


    
if __name__ == '__main__':
    main(*sys.argv)
    #import profile
    #profile.run('main(*sys.argv)')


    
