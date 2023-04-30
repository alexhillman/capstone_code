import pandas as pd
import matplotlib.pyplot as plt

# get input data

df = pd.read_csv('data.csv')
df=df.astype(float)

ax = df.plot(x='Time', y=['o2', 'ph'])
ax.set_ylabel("Concentration (PPM)")
plt.title("Current TSAR Activity")
plt.savefig('graph.png')

