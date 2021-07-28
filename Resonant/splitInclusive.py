import pandas as pd
import pickle as pkl
from collections import OrderedDict as od

year = "2018"

data = pkl.load( open("inputs/Resonant_HHggtautau_InclusivePresel_Resonant_HH_ggtautau_%s_xrd_final_v2.pkl"%year,"rb") )

processDir = od()

df_2tau = data[data['n_tau']>=2]
pkl.dump(df_2tau,open("output/Resonant_HH_ggtautau_%s_2tau_final_v2.pkl"%year,"wb"))
df_1tau1lep = data[(data['n_tau']==1)&((data['n_electrons']+data['n_muons'])>=1)]
pkl.dump(df_1tau1lep,open("output/Resonant_HH_ggtautau_%s_1tau1lep_final_v2.pkl"%year,"wb"))
df_1tau0lep = data[(data['n_tau']==1)&((data['n_electrons']+data['n_muons'])==0)]
pkl.dump(df_1tau0lep,open("output/Resonant_HH_ggtautau_%s_1tau0lep_final_v2.pkl"%year,"wb"))


