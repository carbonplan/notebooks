import numpy as np
import math
import json

def IRF(curve):
    if curve == 'joos_2013':
        # parameters from Joos et al, 2013 (Table 5)
        a = [0.2173, 0.2240, 0.2824, 0.2763]
        tau = [0, 394.4, 36.54, 4.304]
        t_horizon = np.arange(1001)
    elif curve == 'ipcc_2007':
        # parameters from IPCC 2007 (page 213)
        a = [0.217, 0.259, 0.338, 0.186]
        tau = [0, 172.9, 18.51, 1.186]
        t_horizon = np.arange(1001)
    elif curve == 'ipcc_2000':
        # parameters from IPCC Special Report 2000 (Ch2, Footnote 4)
        a = [0.175602, 0.137467, 0.18576, 0.242302, 0.258868]
        tau = [0, 421.093, 70.5965, 21.42165, 3.41537]
        t_horizon = np.arange(1001)
    else:
        raise ValueError('No IRF parameters by the name \'' + curve + '\'.')  

    IRF = [a[0]] * len(t_horizon)
    for t in t_horizon:
        for i in np.arange(1,len(a)):
            IRF[t] =  IRF[t] + (a[i] * np.exp(-t/tau[i]))
    return IRF


def discount(discount_rate, curve): 
    return [x/math.pow(1+discount_rate, i) for i,x in enumerate(curve)]


def print_benefit_report(method_output, plot):
    print()
    print('Discount rate: ' + str(round(method_output['parameters']['discount_rate']*100,1)) + '%')
    print('Delay: ' + str(method_output['parameters']['delay']) + ' year(s)')
    print('Baseline atmospheric cost: ' + str(round(method_output['baseline_atm_impact'],2)) + ' ton-years')
    print('Benefit from 1tCO2 with delay: ' + str(round(method_output['benefit'],2)) + ' ton-years')
    print('Number needed: ' + str(round(method_output['num_for_equivalence'],1)))
    print()
    if plot: 
        plot = plt.plot(method_output['baseline'], label="baseline")
        plot = plt.plot(method_output['scenario'], label="scenario")
        plot = plt.legend()
    return


def tonyear_setup(method, baseline, time_horizon, delay, discount_rate):
    if delay < 0: 
        raise ValueError('Delay cannot be negative.')
    if time_horizon <= 0:
        raise ValueError('Time horizon must be greater than zero.')
    if len(baseline) < time_horizon:
        raise ValueError('Method cannot analyze over a time horizon that is longer than the baseline scenario (i.e. the length of the baseline array).')
    if method not in ['mc', 'ipcc', 'lashof']:
        raise ValueError('No ton-year accounting method called \'' + method + '\'. Options include: Moura-Costa (\'mc\'), Lashof (\'lashof\'), and IPCC (\'ipcc\').')
    
    baseline = baseline[0:time_horizon+1]
    baseline_discounted = discount(discount_rate, baseline)
    baseline_atm_impact = np.trapz(baseline_discounted)

    if method == 'mc':
        scenario = [-1]*(delay+1) + [0]*(time_horizon-delay)   
        scenario = discount(discount_rate, scenario)
        benefit = -np.trapz(scenario[:delay+1])
    elif method == 'ipcc':
        scenario = [0]*delay + baseline
        scenario = scenario[0:time_horizon+1]
        if time_horizon < delay:
            scenario = scenario[:time_horizon+1]
        scenario = discount(discount_rate, scenario)
        benefit = baseline_atm_impact - np.trapz(scenario[delay:])
    elif method == 'lashof':
        scenario = [0]* delay + baseline
        scenario = discount(discount_rate, scenario)
        benefit = np.trapz(scenario[time_horizon:])
        if time_horizon < delay:
            benefit = np.trapz(scenario[delay:])     
    
    return {'parameters': {'method': method,
                           'time_horizon': time_horizon,
                           'delay': delay,
                           'discount_rate': discount_rate}, 
            'baseline': baseline_discounted,
            'scenario': scenario,
            'baseline_atm_impact': baseline_atm_impact,
            'benefit': benefit,
            'num_for_equivalence': baseline_atm_impact/benefit}


def write_json(collection, output):
    with open(output, "w") as f:
        f.write(json.dumps(collection))