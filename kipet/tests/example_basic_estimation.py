#  _________________________________________________________________________
#
#  Kipet: Kinetic parameter estimation toolkit
#  Copyright (c) 2016 Eli Lilly.
#  _________________________________________________________________________

# Sample Problem 3 (From Sawall et.al.)
# Basic extimation of kinetic paramenter using pyomo discretization 
#
#         min \sum_i^{nt}\sum_j^{nl}( D_{i,j} -\sum_{k}^{nc} C_k(t_i)*S(l_j))**2/\delta
#              + \sum_i^{nt}\sum_k^{nc}(C_k(t_i)-Z_k(t_i))**2/\sigma_k       
#
#		\frac{dZ_a}{dt} = -k*Z_a	Z_a(0) = 1
#		\frac{dZ_b}{dt} = k*Z_a		Z_b(0) = 0
#
#               C_a(t_i) = Z_a(t_i) + w(t_i)    for all t_i in measurement points
#               D_{i,j} = \sum_{k=0}^{Nc}C_k(t_i)S(l_j) + \xi_{i,j} for all t_i, for all l_j 


from kipet.model.TemplateBuilder import *
from kipet.opt.Optimizer import *
from kipet.sim.CasadiSimulator import *
import matplotlib.pyplot as plt

from kipet.utils.data_tools import *
import os

if __name__ == "__main__":

    # read 200x500 spectra matrix D_{i,j}
    # this defines the measurement points t_i and l_j as well
    filename = 'data_sets{}Dij_basic.txt'.format(os.sep)
    D_frame = read_spectral_data_from_txt(filename)

    # create template model 
    builder = TemplateBuilder()    
    builder.add_mixture_component({'A':1,'B':0})
    builder.add_parameter('k',0.01)
    builder.add_spectral_data(D_frame)

    # define explicit system of ODEs
    def rule_odes(m,t):
        exprs = dict()
        exprs['A'] = -m.P['k']*m.C[t,'A']
        exprs['B'] = m.P['k']*m.C[t,'A']
        return exprs

    builder.set_rule_ode_expressions_dict(rule_odes)
    
    casadi_model = builder.create_casadi_model(0.0,200.0)
    
    casadi_model.diff_exprs['A'] = -casadi_model.P['k']*casadi_model.C['A']
    casadi_model.diff_exprs['B'] = casadi_model.P['k']*casadi_model.C['A']

    sim = CasadiSimulator(casadi_model)    
    sim.apply_discretization('integrator',nfe=100)
    results_casadi = sim.run_sim("cvodes")

    ##########################################################
    
    builder2 = TemplateBuilder()    
    builder2.add_mixture_component({'A':1,'B':0})

    # note the parameter is not fixed
    builder2.add_parameter('k')
    builder2.add_spectral_data(D_frame)

    # define explicit system of ODEs
    def rule_odes(m,t):
        exprs = dict()
        exprs['A'] = -m.P['k']*m.C[t,'A']
        exprs['B'] = m.P['k']*m.C[t,'A']
        return exprs

    builder2.set_rule_ode_expressions_dict(rule_odes)
    
    pyomo_model = builder2.create_pyomo_model(0.0,200.0)
        
    optimizer = Optimizer(pyomo_model)
    
    optimizer.apply_discretization('dae.collocation',nfe=30,ncp=3,scheme='LAGRANGE-RADAU')

    # Provide good initial guess
    optimizer.initialize_from_trajectory('C',results_casadi.C)
    optimizer.initialize_from_trajectory('S',results_casadi.S)
    optimizer.initialize_from_trajectory('C_noise',results_casadi.C_noise)

    # dont push bounds i am giving you a good guess
    solver_options = {'mu_init': 1e-10, 'bound_push':  1e-8}

    # fixes the standard deaviations for now
    sigmas = {'device':1,'A':1,'B':1}
    results_pyomo = optimizer.run_opt('ipopt',
                                      tee=True,
                                      solver_opts = solver_options,
                                      std_deviations=sigmas)

    print "The estimated parameters are:"
    for k,v in results_pyomo.P.iteritems():
        print k,v
    # display results
    plt.plot(results_pyomo.C)
    plt.plot(results_casadi.C_noise.index,results_casadi.C_noise['A'],'*',
             results_casadi.C_noise.index,results_casadi.C_noise['B'],'*')
    plt.xlabel("time (s)")
    plt.ylabel("Concentration (mol/L)")
    plt.title("Concentration Profile")

    plt.figure()

    plt.plot(results_pyomo.S)
    plt.plot(results_casadi.S.index,results_casadi.S['A'],'*',
             results_casadi.S.index,results_casadi.S['B'],'*')
    plt.xlabel("Wavelength (cm)")
    plt.ylabel("Absorbance (L/(mol cm))")
    plt.title("Absorbance  Profile")
    
    plt.show()
    
