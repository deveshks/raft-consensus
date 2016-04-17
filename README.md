Raft based leader Election algorithm in the presence of crash failures, on top of a message passing
based consensus algorithm.

--------Akshay Jajoo, Devesh Kumar--------
-Execute leader.py as follows:
	> python leader.py -p <port> - h <hostfile> -f <maxCrashes>
-With correct option name parameters can be passed in any order.
-File process.py should be in same directory as leader.py.
-Assuming all the testing will be done on cs machines only and once logged in into one of the machines then no further authentication is required.
-Assuming host ids start from 1 in increasing order.
-Assuming grader does not make any changes to any codefiles. (i.e like do not append any hooks in the file anywhere).
-Assuming that UDP packets are always delivered.(As described in assignment/piazza).In case of drop of UDP packets algorithm may not work correctly
-Read report for configuring some parameters in the code
