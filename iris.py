# Name: Eklavya SARKAR, 
# ID:201135564, 
# Username: u5es2

# We're using the Iris dataset to train an ANN
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

#----------------------------------------------------------------------------------------
# CONFIG
#----------------------------------------------------------------------------------------

# Argument Parser for debugging
parser = argparse.ArgumentParser(description='Make a 2D map of a multidimensional input')
parser.add_argument('-d','--debug', action='store_true', default=False, help='Print debug messages to stderr')
args = parser.parse_args()

#----------------------------------------------------------------------------------------
# SET-UP
#----------------------------------------------------------------------------------------

# Constants
# ======== DO NOT CHANGE ========|
INPUTS_MAX_VALUE = 7.9			#|
MAX_CLASSES = 3					#|
MAX_INPUTS_PER_CLASS = 50		#|
# =========DO NOT CHANGE ========|

chosen_inputs_per_class = 50
n_classes = MAX_CLASSES
init_learning_rate = 0.3

if args.debug:
	print("Debug mode ON")
	print('Loading input files ...')

# Raw Data
url = 'http://archive.ics.uci.edu/ml/machine-learning-databases/iris/iris.data'
data = pd.read_csv(url, encoding='utf-8', header=None)

# Add Column names
attributes = ["sepal_length", "sepal_width", "petal_length", "petal_width", "class"]
data.columns = attributes

# Looping
loopStart = 0
loopEnd = MAX_CLASSES*MAX_INPUTS_PER_CLASS
labels = []
inputs = []

for i in range(loopStart,loopEnd,MAX_INPUTS_PER_CLASS):
    for j in range(chosen_inputs_per_class):
        inputs.append(data.iloc[i+j][0:4]/INPUTS_MAX_VALUE) # Append normalised value
        labels.append(data.iloc[i][4])

# Put labels in seperate NumPy array
#labels = np.array(data['class'])
labels = np.array(labels)

# Put inputs in a a seperate NumPy Array, while normalising it
#inputs = np.array(data[["sepal_length", "sepal_width", "petal_length", "petal_width"]]/inputs.max())
inputs = np.array(inputs)

if args.debug:
	if (inputs.max()==1 and inputs.min()==0):
		normaliseCheck = True
	else:
		normaliseCheck = False

	print('Loaded inputs:', type(inputs))
	print('Loaded labels:', type(labels))
	print('Data normalised:', normaliseCheck)

	# Variables
	n = inputs.shape[0]
	m = inputs.shape[1]

	network_dimensions = np.array([n_classes*2,n_classes*2])		
	n_iterations = n

	if args.debug:
		print('n_classes:', n_classes)
		print('n:', n)
		print('m:', m)
		print('Network dimensions:', network_dimensions.shape)
		print('Number of training iterations:', n_iterations)
		print('Initial learning rate:', init_learning_rate)
		print('Inputs per class:', chosen_inputs_per_class)


# Weight Matrix - same for training and testing as same number of classes and therefore network dimensions
net = np.random.random((network_dimensions[0], network_dimensions[1], m))

# Initial Radius (sigma) for the neighbourhood - same for tranining and testing as same network dimensions
init_radius = max(network_dimensions[0], network_dimensions[1]) / 2

# Radius decay parameter - different as (possibly) different number of iterations
time_constant = n_iterations / np.log(init_radius)

if args.debug:
	print('Net', type(net))
	print('Initial Radius', init_radius)
	print('Time constant', time_constant)

#----------------------------------------------------------------------------------------
# METHODS
#----------------------------------------------------------------------------------------

# Find Best Matching Unit (BMU)
def find_bmu(t, net, m):

	# A 1D array which will contain the X,Y coordinates
	# of the BMU for the given input vector t
	bmu_idx = np.array([0,0])

	# Set the initial minimum difference
	min_diff = np.iinfo(np.int).max

	# To compute the high-dimension distance between 
	# the given input vector and each neuron,
	# we calculate the difference between the vectors
	for x in range (net.shape[0]):
		for y in range(net.shape[1]):
			w = net[x,y,:].reshape(m, 1)

			# Don't sqrt to avoid heavy operation
			diff = np.sum((w - t) ** 2)

			if (diff < min_diff):
				min_diff = diff
				bmu_idx = np.array([x, y])

	bmu = net[bmu_idx[0], bmu_idx[1], :].reshape(m, 1)

	return(bmu, bmu_idx, min_diff)

# Decay the neighbourhood radius with time
def decay_radius(initial_radius, i, time_constant):
	return initial_radius * np.exp(-i / time_constant)

# Decay the learning rate with time
def decay_learning_rate(initial_learning_rate, i, n_iterations):
	return initial_learning_rate * np.exp(-i / n_iterations)

# Calculate the influence
def calculate_influence(distance, radius):
	return np.exp(-distance / (2* (radius**2)))

# SOM Step Learning
def trainSOM(inputsValues, times):
	
	bmu_idx_arr = []
	radiusList = []
	learnRateList = []
	sqDistList = []

	for i in range (times):

		if args.debug:
			print(str(round(i/times*100))+'%')
		
		# ------------- INPUT -------------
		# 1. Select a input weight vector at each step

		# This can be random, however since we're using sorted inputs, we're
		# proceeding in a linear manner through all nodes for sake of clarity
		t = inputsValues[i, :].reshape(np.array([m, 1]))

		# ------------- BMU -------------
		# 2. Find the chosen input vector's BMU at each step
		#bmu, bmu_idx = find_bmu(t, net, m)
		bmu, bmu_idx, dist = find_bmu(t, net, m)

		bmu_idx_arr.append(bmu_idx)
		sqDistList.append(dist)
		
		# ------------- DECAY -------------
		# 3. Determine topological neighbourhood for each step
		r = decay_radius(init_radius, i, time_constant)
		l = decay_learning_rate(init_learning_rate, i, times)

		radiusList.append(r)
		learnRateList.append(l)

		# ------------- UPDATE -------------
		# 4. Repeat for all nodes in the *BMU neighbourhood*
		for x in range(net.shape[0]):
			for y in range(net.shape[1]):
				
				# Find weight vector
				w = net[x, y, :].reshape(m, 1)
				#wList.append(w)
				
				# Get the 2-D distance (not Euclidean as no sqrt)
				w_dist = np.sum((np.array([x, y]) - bmu_idx) ** 2)
				#wDistList.append(w_dist)
				
				# If the distance is within the current neighbourhood radius
				if w_dist <= r**2:
					
					# Calculate the degree of influence (based on the 2-D distance)
					influence = calculate_influence(w_dist, r)
					
					# Update weight:
					# new w = old w + (learning rate * influence * delta)
					# delta = input vector t - old w
					new_w = w + (l * influence * (t - w))
					#new_wList.append(new_w)

					# Update net with new weight
					net[x, y, :] = new_w.reshape(1, m)

		# Every 100 iterations we call for a SOM to be made to view
		#if (i>0 and i%100==0):
		#	bmu_interim_arr = np.array(bmu_idx_arr)
		#	makeSOM(bmu_interim_arr, labels, [], [])

	# Convert to NumPy array
	bmu_idx_arr = np.array(bmu_idx_arr)

	#np.savetxt((save_path+'%s'%timeStamped()+'_%s'%n_classes+'classes'+'_%s'%init_learning_rate+'rate'+'_%s'%chosen_inputs_per_class+'inputs'+'.csv'), bmu_idx_arr, fmt='%d', delimiter=',')
	#np.savetxt((save_path+'Net_%s'%timeStamped()+'.txt'), net, fmt='%d')

	return(bmu_idx_arr, radiusList, learnRateList, sqDistList)

def makeSOM(bmu_idx_arr):

	plotVector = np.zeros((n,5))

	x_coords = []
	y_coords = []

	x_coords = np.random.randint(0, 6, chosen_inputs_per_class*n_classes)
	y_coords = np.random.randint(0, 6, chosen_inputs_per_class*n_classes)

	x_coords = np.array(x_coords)
	y_coords = np.array(y_coords)

	# plotVector Format: [X, Y, R, G, B]
	# Coordinates and colours in a single vector

	# Insert training values
	for i in range(n):        
		# X, Ys - Coordinates with added noise
		plotVector[i][0] = bmu_idx_arr[i][0]
		plotVector[i][1] = bmu_idx_arr[i][1]

		# R,G,Bs - Color each point according to class 
		# RGB Values are normalised
		if (labels[i]=='Iris-setosa'):
			plotVector[i][2] = 1
			plotVector[i][3] = 0
			plotVector[i][4] = 0
		elif (labels[i]=='Iris-versicolor'):
			plotVector[i][2] = 0
			plotVector[i][3] = 1
			plotVector[i][4] = 0
		elif (labels[i]=='Iris-virginica'):
			plotVector[i][2] = 0
			plotVector[i][3] = 0
			plotVector[i][4] = 1

	# Generate noise for each point
	if (plotVector.shape[0] > 0):
		a_x = -0.4
		a_y = -0.4
		b_x = 0.4
		b_y = 0.4
		
		noise_x = (b_x-a_x) * np.random.rand(plotVector.shape[0], 1) + a_x
		noise_y = (b_y-a_y) * np.random.rand(plotVector.shape[0], 1) + a_y

	zPlot = np.array(plotVector[:,2:5])

	# With noise
	xPlotNoise = np.add(plotVector[:,0], noise_x[:,0])
	yPlotNoise = np.add(plotVector[:,1], noise_y[:,0])

	x_coordsNoise = np.add(x_coords[:], noise_x[:,0])
	y_coordsNoise = np.add(y_coords[:], noise_y[:,0])

	# Witout noise
	xPlot = plotVector[:,0]
	yPlot = plotVector[:,1]

	if (args.debug):
		print('Rate:', init_learning_rate)
		print('x:', xPlot.shape)
		print('y:', yPlot.shape)
		print('z:', zPlot.shape)
		print('BMUs:', bmu_idx_arr.shape)

	# Plot Scatterplot
	plotSize = (n_classes * 2)
	figSize = 5.91
	plt.figure()

	# Plot nodes
	plt.scatter(x_coords, y_coords, s=20, facecolor=zPlot)
	plt.title(str(n)+' Inputs unsorted without noise')
	plt.show()

	# Plot nodes with noise
	plt.scatter(x_coordsNoise, y_coordsNoise, s=20, facecolor=zPlot)
	plt.title(str(n)+' Inputs unsorted with noise')
	plt.show()

	# Plot data without noise
	plt.scatter(xPlot, yPlot, s=20, marker='o', facecolor=zPlot)
	plt.title(str(n)+' Inputs sorted without noise')
	plt.show()

	# Plot data with noise
	plt.scatter(xPlotNoise, yPlotNoise, s=20, marker='o', facecolor=zPlot)
	plt.title(str(n)+' Inputs sorted with noise')
	plt.show()

	# Legend
	#for i in range(10):
	#	plt.scatter(i, 1, s=20, facecolor=zPlot[i])
	
	#for i in range(n):
	#	plt.text(xPlot[0], yPlot[1], labels[i], ha='center', va='center')

	#plt.legend(handles=[n])

	#plt.axis('off')

	# Export as CSV
	unClustered = np.zeros((n,5))
	unClusteredNoise = np.zeros((n,5))
	clustered = np.zeros((n,5))
	clusteredNoise = np.zeros((n,5))

	unClustered[:,0] = x_coords[:]
	unClustered[:,1] = y_coords[:]
	unClustered[:,2:5] = zPlot*255

	unClusteredNoise[:,0] = x_coordsNoise[:]
	unClusteredNoise[:,1] = y_coordsNoise[:]
	unClusteredNoise[:,2:5] = zPlot*255

	clustered[:,0] = xPlot[:]
	clustered[:,1] = yPlot[:]
	clustered[:,2:5] = zPlot*255 # Un-normalised

	clusteredNoise[:,0] = xPlotNoise[:]
	clusteredNoise[:,1] = yPlotNoise[:]
	clusteredNoise[:,2:5] = zPlot*255 # Un-normalised
	
	np.savetxt(('static/data/Iris/IrisUnsorted.csv'), unClustered, fmt='%d', delimiter=',', comments='', header='xIris,yIris,R,G,B')
	np.savetxt(('static/data/Iris/IrisUnsortedNoise.csv'), unClusteredNoise, fmt='%.3f', delimiter=',', comments='', header='xIris,yIris,R,G,B')
	np.savetxt(('static/data/Iris/IrisSorted.csv'), clustered, fmt='%d', delimiter=',', comments='', header='xIris,yIris,R,G,B')
	np.savetxt(('static/data/Iris/IrisSortedNoise.csv'), clusteredNoise, fmt='%.3f', delimiter=',', comments='', header='xIris,yIris,R,G,B')

	if args.debug:
		print('Saved sorted coordinates')
		print('Saved sorted coordinates with noise')

# Make graphical comparaisons of various parameters
def plotVariables(radius, learnRate, sqDist):

	# Plot radius
	plt.title('Radius evolution')
	plt.xlabel('Number of iterations')
	plt.ylabel('Radius size')
	plt.plot(radius, 'r')
	plt.show()

	# Plot learning rate
	plt.title('Learning rate evolution')
	plt.xlabel('Number of iterations')
	plt.ylabel('Learning rate')
	plt.plot(learnRate, 'r')
	plt.show()

	# Plot 3D distance
	plt.title('Best Matching Unit 3D Distance')
	plt.xlabel('Number of iterations')
	plt.ylabel('Smallest Distance Squared')
	plt.plot(sqDist, 'r')
	plt.show()

# inputs = setUp(150)
bmu, radius, rate, sqDist = trainSOM(inputs, 150)
makeSOM(bmu)
plotVariables(radius, rate, sqDist)
