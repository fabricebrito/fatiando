"""
GradientSolver:
    Class for generic solving of inverse problems using gradient methods. 
    Subclass them and implement the problem specific methods to solve a new 
    inverse problem.
    Includes:
        * solving linear inverse problems with Tikhonov regularization
        * total variation inversion
        * solving non-linear inverse problems with Levemberg-Marquardt algorithm
        * allows receiving prior parameter weights (useful for depth-weighing in
          gravity inversion)
        * automatically contaminates the data with Gaussian noise and re-runs
          the inversion to generate many estimates
        * calculate mean and standard deviation of the various estimates
        * plot histogram of residuals
"""
__author__ = 'Leonardo Uieda (leouieda@gmail.com)'
__date__ = 'Created 15-Jul-2010'


import time
import logging
import math

import numpy
import pylab

import fatiando
from fatiando.utils import contaminate


# Add the default handler (a null handler) to the class loggers to ensure that
# they won't print verbose if the program calling them doesn't want it
logger = logging.getLogger('GradientSolver')       
logger.setLevel(logging.DEBUG)
logger.addHandler(fatiando.default_log_handler)



class GradientSolver():
    """
    Generic inverse problem solver.
    Subclass this and implement the methods:
        * _build_jacobian
        * _build_first_deriv
        * _calc_adjustment
        * _get_data_array
        * _get_data_cov
    REMEMBER: set self._nparams and self._ndata
    To use equality constraints simply implement a method that fills
    self._equality_matrix and self._equality_values.
    """
    
    
    def __init__(self):
        
        # inversion parameters
        self._nparams = 0
        self._ndata = 0
        self._equality_matrix = None
        self._equality_values = None
        self._first_deriv_matrix = None
                
        # Inversion results
        self.estimates = []
        self._goals = []
        
        # The logger for this class
        self._log = logging.getLogger('GradientSolver')
        
    
    def _build_jacobian(self, estimate):
        """
        Make the Jacobian matrix of the function of the parameters.
        'estimate' is the the point in the parameter space where the Jacobian
        will be evaluated.
        In case of a linear inverse problem, estimate is expected to be None.
        """
        
        # Raise an exception if the method was raised without being implemented
        raise NotImplementedError, \
            "_build_jacobian was called before being implemented"
            
    
    def _calc_adjusted_data(self, estimate):
        """
        Calculate the adjusted data vector based on the current estimate
        """
        
        # Raise an exception if the method was raised without being implemented
        raise NotImplementedError, \
            "_calc_adjusted_data was called before being implemented"
        
        
    def _build_first_deriv(self):
        """
        Compute the first derivative matrix of the model parameters.
        """
        
        # Raise an exception if the method was raised without being implemented
        raise NotImplementedError, \
            "_build_first_deriv was called before being implemented"
            
            
    def _get_data_array(self):
        """
        Return the data in a Numpy array so that the algorithm can access it
        in a general way
        """        
        
        # Raise an exception if the method was raised without being implemented
        raise NotImplementedError, \
            "_get_data_array was called before being implemented"
                           
            
    def _get_data_cov(self):
        """
        Return the data covariance in a 2D Numpy array so that the algorithm can
        access it in a general way
        """        
        
        # Raise an exception if the method was raised without being implemented
        raise NotImplementedError, \
            "_get_data_cov was called before being implemented"
        
                                      
    def _calc_means(self):
        """
        Calculate the means of the parameter estimates. 
        """
        
        assert self.estimates, "Tried to calculate mean of parameters " + \
            "before running the inversion."
            
        means = []
        
        for param in numpy.transpose(self.estimates):
            
            means.append(param.mean())
            
        return means
    
    
    # Property for accessing the means of the parameter estimates
    mean = property(_calc_means)
    
            
    def _calc_stddevs(self):
        """
        Calculate the standard deviations of the parameter estimates. 
        """
        
        assert self.estimates, "Tried to calculate standard deviation of" + \
            " parameters before running the inversion."
        
        stds = []
        
        for param in numpy.transpose(self.estimates):
            
            stds.append(param.std())
            
        return stds
    
    
    # Property for accessing the standard deviations of the parameter estimates
    stddev = property(_calc_stddevs)
    
    
    def _calc_mean_residuals(self):
        """
        Calculates the residuals based on the mean solution found.
        """
        
        assert self.estimates, "Tried to calculate residuals before " + \
            "running the inversion."
        
        residuals = self._get_data_array() - self._calc_adjusted_data(self.mean)
    
        return residuals
    
    
    # Property for accessing the residuals due to the mean of the parameter 
    # estimates
    residuals = property(_calc_mean_residuals)
    
    
    def _calc_mean_rms(self):
        """
        Calculates the residual mean square error of the mean solution found.
        """
        
        assert self.estimates, "Tried to calculate rms before " + \
            "running the inversion."
                
        residuals = self.residuals
        
        rms = numpy.dot(residuals.T, residuals)
    
        return rms
    
    
    # Property for accessing the rms due to the mean estimate
    rms = property(_calc_mean_rms)
    
    
    def clear_equality(self):
        """
        Erase the equality constraints
        """
                
        self._equality_matrix = None
        self._equality_values = None
        
            
    def clear(self):
        """
        Erase the inversion results.
        """
                
        # Inversion results
        self.estimates = []
        self._goals = []
        
        
    def _build_tikhonov_weights(self, damping, smoothness, curvature, \
                                prior_weights):
        """
        Build the weight matrix for Tikhonov regularization.
        """
        
        Wp = numpy.zeros((self._nparams, self._nparams))
        
        if damping:
            
            Wp = Wp + damping*numpy.identity(self._nparams)
            
        if smoothness:
            
            if self._first_deriv_matrix == None:
                
                start = time.time()
                
                self._first_deriv_matrix = self._build_first_deriv()
                
                end = time.time()
                
                self._log.info("  Build first derivative matrix: " + \
                               "%d x %d (%g s)" \
                               % (self._first_deriv_matrix.shape[0], \
                                  self._first_deriv_matrix.shape[1], \
                                  end - start))
            
            aux = numpy.dot(self._first_deriv_matrix.T, \
                            self._first_deriv_matrix)
            
            Wp = Wp + smoothness*aux
            
        if curvature:
            
            if self._first_deriv_matrix == None:
                
                start = time.time()
                
                self._first_deriv_matrix = self._build_first_deriv()
                
                end = time.time()
                
                self._log.info("  Build first derivative matrix: " + \
                               "%d x %d (%g s)" \
                               % (self._first_deriv_matrix.shape[0], \
                                  self._first_deriv_matrix.shape[1], \
                                  end - start))
                
            if not smoothness:
                
                aux = numpy.dot(self._first_deriv_matrix.T, \
                            self._first_deriv_matrix)
                
            Wp = Wp + curvature*numpy.dot(aux.T, aux)
             
        if prior_weights != None:
            
            Wp = numpy.dot(numpy.dot(prior_weights, Wp), prior_weights)
            
        return Wp
    
    
    def _build_tv_grad_hessian(self, estimate, sharpness, beta, prior_weights):
        """
        Return the gradient and Hessian of the Total Variation prior.
        """
        
        if self._first_deriv_matrix == None:
            
            self._first_deriv_matrix = self._build_first_deriv()
            
        nderivs = len(self._first_deriv_matrix)
                
        d = numpy.zeros(nderivs)
        
        D = numpy.zeros((nderivs, nderivs))
                        
        for l in range(nderivs):
            
            deriv = numpy.dot(self._first_deriv_matrix[l], estimate)
            
            sqrt = math.sqrt(deriv**2 + beta)
            
            d[l] = deriv/sqrt
            
            D[l][l] = beta/(sqrt**3)
            
        grad = sharpness*numpy.dot(self._first_deriv_matrix.T, d)
        
        hessian = sharpness*numpy.dot( \
                            numpy.dot(self._first_deriv_matrix.T, D), \
                                      self._first_deriv_matrix)
    
        return grad, hessian
    
    
    def _linear_overdetermined(self, tk_weights, prior_mean, equality, \
                               adjustment, data_variance, contam_times):
        """
        Solves the linear overdetermined problem. See doc for solve_linear for
        details on the parameters.
        """
        
        start = time.time()
        
        jacobian = self._build_jacobian(None)
        
        end = time.time()
        
        self._log.info("  Build Jacobian (sensibility) matrix: %d x %d (%g s)" \
                       % (jacobian.shape[0], jacobian.shape[1], end - start))
        
        start = time.time()
        
        normal_eq = numpy.dot(jacobian.T, jacobian)
        
        if tk_weights != None:
            
            normal_eq = normal_eq + tk_weights
            
            if prior_mean != None:
                
                y_tk_priormean = numpy.dot(tk_weights, prior_mean)
            
        if equality:
            
            normal_eq = normal_eq + \
                        equality*numpy.dot(self._equality_matrix.T, \
                                           self._equality_matrix)
                        
            y_equality = equality*numpy.dot(self._equality_matrix.T, \
                                            self._equality_values)
            
        end = time.time()
                
        self._log.info("  Build Normal Equations system: %d x %d (%g s)" \
                       % (normal_eq.shape[0], normal_eq.shape[1], end - start))
                
        # The normal equation matrix, equality constraint terms, and Tikhonov 
        # term due to the use of prior mean are unchanged when contaminating 
        # the data and re-running the inversion.
        
        data = self._get_data_array()
        
        start = time.time()
        
        for i in xrange(contam_times + 1): # +1 is for the real data
           
            # The linear system to be solved is N*p = y, where N is the normal
            # equation matrix (normal_eq) and y = A.T*data + equality and prior mean
            # terms.
            
            y = numpy.dot(jacobian.T, data)
            
            if prior_mean != None:
                
                y = y + y_tk_priormean
            
            if equality:
                
                y = y + y_equality
                
            estimate = numpy.linalg.solve(normal_eq, y)
            
            self.estimates.append(estimate)
            
            if contam_times > 0:
                
                data = contaminate.gaussian(self._get_data_array(), \
                                            stddev=math.sqrt(data_variance), \
                                            percent=False, return_stddev=False)
                
        end = time.time()
        
        self._log.info("  Contaminate data %d times with " % (contam_times) + \
                       "Gaussian noise (%g s)" % (end - start))
    
    
    def _linear_underdetermined(self, tk_weights, prior_mean, equality, \
                                adjustment=1, data_variance=0, contam_times=0):
        """
        Solves the linear underdetermined problem. See doc for solve_linear for
        details on the parameters.
        """
        
        # BUILD JACOBIAN MATRIX
        start = time.time()
        
        jacobian = self._build_jacobian(None)
        
        end = time.time()
        
        self._log.info("  Build Jacobian (sensibility) matrix: %d x %d (%g s)" \
                       % (jacobian.shape[0], jacobian.shape[1], end - start))
        
        # BUILD PARAMETER WEGHTS AND ITS INVERSE
        start = time.time()
        
        param_weights = numpy.zeros((self._nparams, self._nparams))
        
        if tk_weights != None:
            
            param_weights = param_weights + tk_weights
                        
        if equality:
            
            param_weights = param_weights + \
                            equality*numpy.dot(self._equality_matrix.T, \
                                               self._equality_matrix)
                            
        self._log.info("  det(parameter weights) = %g" \
                       % (numpy.linalg.det(param_weights)))
                                                        
        inv_param_weights = numpy.linalg.inv(param_weights)
        
        del param_weights
            
        end = time.time()
                
        self._log.info("  Calculate inverse of parameter weights (%g s)" \
                       % (end - start))
        
        # BUILD THE NORMAL EQUATION SYSTEM
        start = time.time()
        
        normal_eq = numpy.dot(numpy.dot(jacobian, inv_param_weights), \
                              jacobian.T) + \
                    numpy.identity(self._ndata)
        
        # The system that will be solved is:
        #     N*lagrange_mult = data + A*Wp^-1*y_prior
        # where y_prior is the term due to Tikhonov prior mean and equality
        # constraints
        y_prior = None
        
        if prior_mean != None:
            
            y_prior = numpy.dot(tk_weights, prior_mean)
            
        if equality:
            
            if prior_mean != None:
            
                y_prior = y_prior + \
                          equality*numpy.dot(self._equality_matrix.T, \
                                             self._equality_values)
                          
            else:
                
                y_prior = equality*numpy.dot(self._equality_matrix.T, \
                                             self._equality_values)
        
        if y_prior != None:
        
            # Not to repeat the multiplication every time    
            y_prior = numpy.dot(inv_param_weights, y_prior)
            
            y_prior_aux = numpy.dot(jacobian, y_prior)
            
        end = time.time()
                
        self._log.info("  Build Normal Equations system: %d x %d (%g s)" \
                       % (normal_eq.shape[0], normal_eq.shape[1], end - start))
            
        # Not to repeat the multiplication every time
        aux = numpy.dot(inv_param_weights, jacobian.T)
        
        del inv_param_weights
                
        # The normal equation matrix, equality constraint terms, and Tikhonov 
        # term due to the use of prior mean are unchanged when contaminating 
        # the data and re-running the inversion.
        
        data = self._get_data_array()
        
        start = time.time()
        
        for i in xrange(contam_times + 1): # +1 is for the real data
                
            y = data
            
            if y_prior != None:
                
                y = y + y_prior_aux
                
            lagrange_mult = numpy.linalg.solve(normal_eq, y)
            
            estimate = numpy.dot(aux, lagrange_mult)
                        
            if y_prior != None:
                
                estimate = estimate + y_prior
            
            self.estimates.append(estimate)
            
            if contam_times > 0:
                
                data = contaminate.gaussian(self._get_data_array(), \
                                            stddev=math.sqrt(data_variance), \
                                            percent=False, return_stddev=False)
                
        end = time.time()
        
        self._log.info("  Contaminate data %d times with " % (contam_times) + \
                       "Gaussian noise (%g s)" % (end - start))
        
                        
    def solve_linear(self, damping=0, smoothness=0, curvature=0, equality=0, \
                     adjustment=1, prior_mean=None, prior_weights=None, \
                     data_variance=1, contam_times=0):
        """
        Solve the linear inverse problem with Tikhonov regularization.
        
        Parameters:
            
            damping:
        
            smoothness:
                   
            curvature:
        
            equality:
        
            adjustment:
            
            prior_mean:
            
            prior_weights:
            
            data_variance:
            
            contam_times:
        """
        
        self._log.info("LINEAR INVERSION:")
        self._log.info("  damping    (Tikhonov order 0) = %g" % (damping))
        self._log.info("  smoothness (Tikhonov order 1) = %g" % (smoothness))
        self._log.info("  curvature  (Tikhonov order 2) = %g" % (curvature))
        self._log.info("  equality constraints          = %g" % (equality))
        self._log.info("  a priori data variance        = %g" % (data_variance))
        self._log.info("  a priori data stddev          = %g" \
                       % (math.sqrt(data_variance)))
        self._log.info("  use prior mean of parameters  = %s" \
                       % (prior_mean != None))
        self._log.info("  use prior parameters weights  = %s" \
                       % (prior_weights != None))
        
        if self._ndata >= self._nparams:
            
            self._log.info("  problem type                  = OVERDETERMINED")
            
        else:
            
            self._log.info("  problem type                  = UNDERDETERMINED")
            
        # Wipe a clean slate before starting
        self.clear()
        
        start = time.time()
                               
        if damping or smoothness or curvature:
            
            start_tk = time.time()
            
            tk_weights = self._build_tikhonov_weights(damping, smoothness, \
                                                      curvature, prior_weights)
            
            end_tk = time.time()
            
            self._log.info("  Build Tikhonov parameter weights (%g s)" \
                           % (end_tk - start_tk))
            
        else:
            
            tk_weights = None
            
        if prior_mean != None:
            
            assert tk_weights != None, "A prior mean value only makes sense" + \
                " when using Tikhonov inversion (set one or more of: " + \
                "damping, smoothness, or curvature; to non-zero.)"
                        
        if equality:

            assert self._equality_matrix != None and \
                   self._equality_values != None, \
                "Tried to use equality constraints without setting any."
                        
        if self._ndata >= self._nparams:
                    
            self._linear_overdetermined(tk_weights, prior_mean, equality, \
                                       adjustment, data_variance, contam_times)

        else:
            
            assert tk_weights != None or equality, \
                "Can't solve underdetermined problem without prior " + \
                "information (regularization or equality constraints)."
                    
            self._linear_underdetermined(tk_weights, prior_mean, equality, \
                                         adjustment, data_variance, \
                                         contam_times)
                
        self._log.info("  RMS = %g" % (self.rms))
            
        end = time.time()
        
        self._log.info("  Total time of inversion: %g s" % (end - start))
            
            
    def plot_residuals(self, title="Residuals", bins=0):
        """
        Plot a histogram of the residuals due to the mean solution.
        
        Parameters:
            
            - title: title of the figure
            
            - bins: number of bins (default to len(residuals)/8)
            
        Note: to view the image use pylab.show()
        """
                        
        residuals = self.residuals
        
        if bins == 0:
        
            bins = len(residuals)/8
    
        pylab.figure()
        pylab.title(title)
        
        pylab.hist(residuals, bins=bins, facecolor='gray')
        
        pylab.xlabel("Residuals")
        pylab.ylabel("Count")    
        