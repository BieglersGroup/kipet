#  _________________________________________________________________________
#
#  Kipet: Kinetic parameter estimation toolkit
#  Copyright (c) 2016 Eli Lilly.
#  _________________________________________________________________________

# Sample Problem 1 (From Sawall et.al.)
# Basic simulation of ODE system using multistep-integrator
#
#		\frac{dC_a}{dt} = -k*C_a	C_a(0) = 1
#		\frac{dC_b}{dt} = k*C_a		C_b(0) = 0


from kipet.model.TemplateBuilder import *
from kipet.sim.CasadiSimulator import *
import matplotlib.pyplot as plt

if __name__ == "__main__":

    # create template model 
    builder = TemplateBuilder()    
    builder.add_mixture_component('A',1)
    builder.add_mixture_component('B',0)
    builder.add_parameter('k',0.01)

    # define explicit system of ODEs
    def rule_odes(m,t):
        exprs = dict()
        exprs['A'] = -m.P['k']*m.C[t,'A']
        exprs['B'] = m.P['k']*m.C[t,'A']
        return exprs

    builder.set_rule_ode_expressions_dict(rule_odes)
    
    # create an instance of a casadi model template
    casadi_model = builder.create_casadi_model(0.0,200.0)    
    
    print casadi_model.diff_exprs

    # create instance of simulator
    sim = CasadiSimulator(casadi_model)
    # defines the discrete points wanted in the concentration profile
    sim.apply_discretization('integrator',nfe=200)
    # simulate
    results_casadi = sim.run_sim("cvodes")

    # display concentration results
    plt.plot(results_casadi.C)
    plt.xlabel("time (s)")
    plt.ylabel("Concentration (mol/L)")
    plt.title("Concentration Profile")

    plt.show()
