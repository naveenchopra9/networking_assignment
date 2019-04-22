import matplotlib.pyplot as plt
import numpy as np

y,z,w,x = np.loadtxt('/Users/naveen/Documents/online_code/output.txt', delimiter=' ', unpack=True)

plt.plot(x,y, label='sending rate vs average time delay')
plt.plot(x,z, label='sending rate vs average time delay')
plt.plot(x,w, label='sending rate vs average time delay')

plt.xlabel('sending rate(it means x second need for one packet)')
plt.ylabel('average time delay')
plt.title('sending rate vs average time delay')
plt.legend()
plt.show()

