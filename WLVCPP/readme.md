WLVCPP is a machine learning predictor of cell penetrating peptides

=============
To run WLVCPP
=============
for instance, let the name of your fasta file be "candidates.fa"

Three input files have to be there, namely, 
rand_train.fa   ,  recep_train.fa   ,  candidates.fa


I- The unconditional way (Using Google colab): 
Steps
	1. open a new Google colab notebook on your gmail account and rename it
	2. copy the whole code from WLVCPP.py file into a cell 
	3. upload the input files		
	4. run the cell > type the name of your fasta file > hit enter    
 
II- The other way (On your local computer)
Requirements: 
	python3 installed with the following packages pandas, numpy and scikit learn
Steps (directly from the script):
	1. create a folder with python script and the three input files copied in
	2. open the script and run it 
	3. run the script > type the name of your fasta file > hit enter    
Alternatively (from the terminal (on Linux) or cmd (on Windows)): 
	1. create a folder with python script and the three input files copied in
	2. open the terminal (on Linux) or cmd (on Windows) 
	3. navigate to the folder where the script and the input files are
	4. type: python WLVCPP.py candidates.fa
 
===============
Important notes
===============
	1. accurate results are not guranteed if any change happend to the input files rand_train.fa and recep_train.fa 
	2. the script was suited to deal with various incorrectly formatted inputs, however providing proper fasta format is highly encouraged 


