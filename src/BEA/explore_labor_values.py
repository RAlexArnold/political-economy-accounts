# -*- coding: utf-8 -*-
"""
Created on Tue Jul 28 14:47:45 2026

@author: Alex
"""
from importlib import reload

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

import BEA

reload(BEA)

self = BEA.BEA()

#year = 2000


for year in np.arange(2000, 2023):
    self.start(year)
    if year==2000:
        v_df = self.v_df
    else:
        v_df = pd.concat([v_df, self.v_df], axis=1)
        
 

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(24, 7), sharex=True, sharey=True)

mins = 60
hr = 1.0

plot_df = v_df.T*(mins/hr)
# Transpose so that years become the index and sectors become columns
plot_df.iloc[:, 0:7].plot(ax=ax[0])

ax[0].set_xlabel("Year")
ax[0].set_ylabel("Labor Value [minute per dollar]")
ax[0].set_title("Labor Values by Industry")
ax[0].legend(title="Sector", bbox_to_anchor=(1.05, 1), loc="upper left")

#plt.tight_layout()
#plt.show()

#fig, ax = plt.subplots(figsize=(12, 7))

# Transpose so that years become the index and sectors become columns
plot_df.iloc[:, 8:].plot(ax=ax[1])

ax[1].set_xlabel("Year")
ax[1].set_ylabel("Labor-Value")
ax[1].set_title("Vertically Integrated Labor by Industry")
ax[1].legend(title="Sector", bbox_to_anchor=(1.05, 1), loc="upper left")

#ax[0].set_yscale('log')
#ax[1].set_yscale('log')

plt.tight_layout()
plt.show()



    
   



