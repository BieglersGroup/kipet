#  _________________________________________________________________________
#
#  Kipet: Kinetic parameter estimation toolkit
#  Copyright (c) 2016 Eli Lilly.
#  _________________________________________________________________________

# Sample Problem 2 (From Sawall et.al.)
# Basic simulation of ODE with spectral data using pyomo discretization 
#
#		\frac{dZ_a}{dt} = -k*Z_a	Z_a(0) = 1
#		\frac{dZ_b}{dt} = k*Z_a		Z_b(0) = 0
#
#               C_a(t_i) = Z_a(t_i) + w(t_i)    for all t_i in measurement points
#               D_{i,j} = \sum_{k=0}^{Nc}C_k(t_i)S(l_j) + \xi_{i,j} for all t_i, for all l_j 

from kipet.model.TemplateBuilder import *
from kipet.sim.PyomoSimulator import *
import matplotlib.pyplot as plt

from kipet.utils.data_tools import *
import os

if __name__ == "__main__":

    # read 200x500 spectra matrix D_{i,j}
    # this defines the measurement points t_i and l_j as well
    filename = 'data_sets{}Dij_basic.csv'.format(os.sep)
    D_frame = read_spectral_data_from_csv(filename)
    
    # create template model 
    builder = TemplateBuilder()    
    builder.add_mixture_component('A',1)
    builder.add_mixture_component('B',0)
    builder.add_parameter('k',0.01)
    # includes spectra data in the template and defines measurement sets
    builder.add_spectral_data(D_frame)

    # define explicit system of ODEs
    def rule_odes(m,t):
        exprs = dict()
        exprs['A'] = -m.P['k']*m.C[t,'A']
        exprs['B'] = m.P['k']*m.C[t,'A']
        return exprs

    builder.set_rule_ode_expressions_dict(rule_odes)
    
    # create an instance of a pyomo model template
    # the template includes
    #   - C variables indexed over time and components names e.g. m.C[t,'A']
    #   - C_noise variables indexed over measurement t_i and components names e.g. m.C_noise[t_i,'A']
    #   - P parameters indexed over the parameter names m.P['k']
    #   - D spectra data indexed over the t_i, l_j measurement points m.D[t_i,l_j]
    pyomo_model = builder.create_pyomo_model(0.0,200.0)

    # create instance of simulator
    simulator = PyomoSimulator(pyomo_model)
    # defines the discrete points wanted in the profiles (does not include measurement points)
    simulator.apply_discretization('dae.collocation',nfe=10,ncp=1,scheme='LAGRANGE-RADAU')
    # simulate
    results_pyomo = simulator.run_sim('ipopt',tee=True)

    # display concentration and absorbance results
    plt.plot(results_pyomo.C_noise)
    plt.xlabel("time (s)")
    plt.ylabel("Concentration (mol/L)")
    plt.title("Concentration Profile")

    plt.figure()
    plt.plot(results_pyomo.S)
    plt.xlabel("Wavelength")
    plt.ylabel("Absorbance (L/(mol cm))")
    plt.title("Absorbance  Profile")

    plt.show()


