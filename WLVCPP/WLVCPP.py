#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
from random import random, uniform, shuffle
from sklearn.model_selection import ShuffleSplit
from sklearn.model_selection import StratifiedShuffleSplit
from os import walk , getcwd, remove
from sklearn.model_selection import learning_curve
from sklearn.svm import SVC
from os.path import exists
pd.options.mode.chained_assignment = None  # default='warn'



####################################################################################################################
### peptides list and fasta files
####################################################################################################################
# cpps, ncpps, FN = from_cluster(fasta_file, cluster_file)
# cpps, ncpps = from_fasta(fasta_file)
# peptides = from_fasta(fasta_file)  if not labeled as cpp and/or non 
def from_fasta(fasta_file): 
    peptides, cpps , ncpps = [],[],[]
    sf = open(fasta_file)
    for line in sf : https://github.com/BahaaIsmail/WLVCPP.git
        if 'cpp' in line : 
            line = sf.readline()
            pep = line.strip('\n')
            cpps += [pep]
        elif 'non' in line : 
            line = sf.readline()
            pep = line.strip('\n')
            ncpps += [pep]   
        elif '>' in line : 
            line = sf.readline()
            pep = line.strip('\n')
            peptides += [pep]             
    sf.close()    
    if peptides : 
        return peptides
    return cpps, ncpps

# cpps and ncpps lists --->  fasta file
def to_fasta(cpps,ncpps,fasta_name): 
    tf = open(fasta_name,'w')
    k = 1
    for pep in cpps : 
        tf.write('>cpp_'+str(k)+'\n'+pep+'\n')  
        k += 1
    k = 1
    for pep in ncpps : 
        tf.write('>non_'+str(k)+'\n'+pep+'\n')  
        k += 1   
    tf.close()

    
#X, y = loadcsv(datafile) 
def loadcsv(datafile) : 
    data = pd.read_csv(datafile) 
    if 'Unnamed: 0' in data.columns : 
        data = data.drop('Unnamed: 0' , axis = 1)
    y = data['cpp']
    X = data.drop('cpp' , axis = 1)
    return X , y 


####################################################################################################################
### handeling descriptors and datasets
####################################################################################################################
mps = ['A',	'C','D','E','F','G','H','I','K','L','M','N','P','Q','R','S','T','V','W','Y']
## from numeric to categories including removing of outliers
def categorise(data):
    for c in data.columns: 
        if not c  in ['cpp','peps'] : 
            q1 = data[c].quantile(0.25)
            q3 = data[c].quantile(0.75)
            iqr = q3-q1
            low = q1-1.5*iqr
            up  = q3+1.5*iqr
            L = [i for i in data[c]]
            for i in range(len(L)) : 
                if L[i] > up : 
                    L[i] = up
                elif L[i] < low : 
                    L[i] = low

            mn, mx = min(L), max(L)
            d = (mx-mn)/10
            for j in range(len(L)) : 
                for i in range(1,11) : 
                    if L[j] <= mn+i*d :
                        L[j] = i/10
                        break
            data[c] = L
    return data


# data = datset_builder(cpps, ncpps) 
def datset_builder(cpps, ncpps):    
    peptides = cpps + ncpps
    peptides = [p.upper() for p in peptides]
    arap = [i+'+'+j for i in mps for j in mps if i < j]
    aran = [i+'-'+j for i in mps for j in mps if i < j]
    aagroups = {'pol' : ['S','T','C','P','N','Q'] , 'non' : ['G','A','V','L','I','M'] , 
                'aro' : ['F','Y','W'] , 'pos' : ['K','R','H'] , 'neg' : ['D','E'] }
    aa2g = {a:g for g in aagroups for a in mps if a in aagroups[g]}   

    data = {c:[] for c in mps+aran+arap}   
    for c in aagroups : 
        data[c] = [] 
    
    # aa composition
    for c in mps : 
        for p in peptides : 
            L = len(p)
            k = p.count(c)
            data[c] += [k] 

    ## aagroups 
    for c in aagroups : 
        g = aagroups[c]               
        for p in peptides :            
            k = len([r for r in p if r in g])
            data[c] += [k] 
    
    ## dp composition
    dpgroups = [] 
    for i in aagroups : 
        for j in aagroups : 
            f,s = sorted([i,j])
            g = f+'_'+s
            if not g in dpgroups : 
                dpgroups += [g]

    dipeps = {g:[] for g in dpgroups}
    n = 0 
    for ij in dpgroups:
        [i,j] = ij.split('_')
        for p in peptides :
            L = len(p)
            dplist = [aa2g[p[a]]+'_'+aa2g[p[a+1]] for a in range(L-1) if not [b for b in ['X', 'B' ,'J', 'Z','U'] if b in [p[a],p[a+1]]]]        
            k = dplist.count(ij)
            if i != j : 
                ji = j+'_'+i
                k += dplist.count(ji)
            if k > 0 : 
                n+=1
            dipeps[i+'_'+j] += [k]
    dipeps = pd.DataFrame(dipeps)
    
    # aa ratios
    for i in mps : 
        for j in mps : 
            if i < j : 
                for p in peptides :
                    L= len(p) 
                    data[i+'+'+j] += [abs(p.count(i)+p.count(j))]
                    data[i+'-'+j] += [abs(p.count(i)-p.count(j))]
     
    data['length'] = [] 

    data['peps'] = []    # does that affests the correlation and so changes the dataset values?
    for p in peptides : 
        data['peps'] += [p]
        data['length'] += [len(p)]

    if len(ncpps):
        data['cpp'] = []
        for p in peptides :
            if p in cpps : 
                data['cpp'] += [1]
            elif p in ncpps : 
                data['cpp'] += [0]
    data = pd.DataFrame(data)

    for c in dipeps : 
        data[c] = dipeps[c]
    return data


# data = engineer(data, thr)
def engineer(data, thr) : 
    for c in data.columns : 
        if not c in ['cpp','peps'] :
            minv = min(data[c])
            data[c] = np.log1p(data[c]-minv+1)
            data[c] = categorise(pd.DataFrame(data[c]))     
    return data


# data = add_corr(data,adds,subs) 
def add_corr(data,adds,subs):
    data['corr'] = round(sum([data[c] for c in adds]) - sum([data[c] for c in subs]))
    return data 




############################################################################################################
### general definitions 
seed = 43
cv_split = ShuffleSplit(n_splits = 10, test_size = .25, train_size = .75, random_state = seed )
model = SVC(max_iter = 10000,probability=True)

############################################################################################################

# random
feats_rand = [92.91, 93.41, 93.43, -0.85, -65, 93.17, 93.17, 93.43, 93.43, 'A+L', 'A+Y', 'A-G', 'A-I', 'A-N', 'A-S', 'C+E', 'C+I', 'C+K', 'C+L', 'C+N', 'C+R', 'C+W', 'C+Y', 'C-L', 'C-P', 'D+I', 'D+Y', 'D-K', 'D-W', 'E+K', 'E+P', 'E+Y', 'E-H', 'E-V', 'F+G', 'F+K', 'F-T', 'G+R', 'G+W', 'G-L', 'G-R', 'G-S', 'H+I', 'H+M', 'H+W', 'H-Q', 'I+Q', 'I-P', 'K', 'K+N', 'K+W', 'K-L', 'L+N', 'L-R', 'L-T', 'M', 'M+R', 'M-R', 'M-V', 'N+R', 'N+T', 'N+W', 'N-P', 'N-S', 'P-Q', 'P-V', 'Q-Y', 'T-W', 'aro_aro', 'aro_neg', 'corr', 'length', 'neg_neg', 'neg_non']
adds_rand =  ['pos_pos', 'A', 'K', 'L', 'R', 'A-H', 'A-R', 'C-K', 'C-L', 'C-R', 'D-K', 'D-L', 'D-R', 'E-K', 'E-R', 'F-L', 'F-R', 'G-H', 'G-M', 'G-R', 'H-K', 'H-R', 'I-L', 'I-R', 'K-M', 'K-P', 'K-R', 'L-M', 'L-N', 'L-Q', 'L-R', 'M-R', 'N-R', 'P-R', 'Q-R', 'R-S', 'R-T', 'R-V', 'R-W', 'R-Y', 'A+S', 'C+T', 'neg', 'pol_pol', 'non_non', 'aro_aro', 'aro_neg', 'neg_neg']
subs_rand =  ['H', 'M', 'Y', 'C-D', 'C-M', 'C-N', 'D-M', 'D-Q', 'D-T', 'E-N', 'E-V', 'F-Q', 'F-W', 'H-T', 'H-Y', 'I-W', 'M-N', 'M-Q', 'M-V', 'S-Y', 'T-V', 'A+C', 'A+D', 'A+R', 'C+D', 'C+E', 'E+F', 'F+I', 'G+N', 'H+R', 'S+T', 'pol_pos', 'aro_pos', 'neg_pos']

# receptors
feats_recep = [89.42, 90.2, 90.51, -1.99, -51, 90.24, 90.98, 90.51, 90.51, 'A+C', 'A+E', 'A+I', 'A+K', 'A+T', 'A-C', 'A-F', 'A-H', 'C+E', 'C+G', 'C+I', 'C+Y', 'C-K', 'C-T', 'D+F', 'D+G', 'D+H', 'D+I', 'D+N', 'D+P', 'D+S', 'E+G', 'E+S', 'E+T', 'E-N', 'E-S', 'F+R', 'F+T', 'F+Y', 'F-R', 'G+L', 'G+V', 'G-T', 'H-K', 'H-Q', 'H-T', 'I+K', 'K+W', 'M+Q', 'M-P', 'N-P', 'P-Q', 'P-R', 'Q-S', 'R-V', 'S-T', 'T+Y', 'T-V', 'W+Y', 'corr', 'pol_pos']
adds_recep =  ['pos_pos', 'A', 'K', 'R', 'W', 'A-R', 'C-R', 'D-K', 'D-R', 'E-K', 'E-R', 'F-R', 'G-R', 'H-V', 'H-W', 'L-R', 'P-R', 'Q-R', 'R-S', 'R-T', 'R-V', 'W-Y', 'C+W', 'D+Y', 'aro_aro', 'neg_neg']
subs_recep =  ['E', 'V', 'A-C', 'D-M', 'D-Y', 'E-N', 'G-Y', 'M-Q', 'M-S', 'P-T', 'Q-V', 'R-W', 'R-Y', 'A+C', 'C+Y', 'D+F', 'E+H', 'R+W', 'pol_pos']


classifiers ={
            'rand':   {'fa':'train_random.fa','feats':feats_rand,'adds':adds_rand,'subs':subs_rand},
            'recep':  {'fa':'train_receptor.fa','feats':feats_recep,'adds':adds_recep,'subs':subs_recep},
            }

###########################################################################################################

def check_entries(fasta_file):
    sf = open(fasta_file)
    peps, names, nonalphabetic = [],[],[]
    name, pep = '',''
    k = 0 
    for line in sf :
        k += 1
        name = pep+''
        pep = line.strip('\n')        
        if not '>' in pep :            
            if '>' in name :                
                name = name.strip('>').strip('\n').split()
                if len(name)> 0 :
                    name = name[0]
                else:
                    name = 'line_'+str(k)
            else:
                name = 'line_'+str(k)

            if pep.isalpha():
                peps += [pep]
                names += [name] 
            else:
                nonalphabetic += [['line_'+str(k) ,pep]]
    sf.close()
    return names, peps, nonalphabetic


def calc_predictions(names, peps):               
    L = len(peps)
    if not L :
        print("No valid peptides detected")
        return    

    print('Processing ...\n\n')
    S0 = datset_builder(peps,[])
    preds = []
    for clf in classifiers : 
        fa = classifiers[clf]['fa']
        feats = classifiers[clf]['feats'][9:]
        adds = classifiers[clf]['adds']
        subs = classifiers[clf]['subs']
        
        cpps, ncpps = from_fasta(clf+'_train.fa')
        data = datset_builder(cpps, ncpps)
        data = add_corr(data,adds,subs)
        data = engineer(data, 0.9)
        yr = data['cpp']
        R = data[feats]
        
        S0 = add_corr(S0,adds,subs)
        S0 = engineer(S0, 0.9)    
        S = S0[feats]    
        
        model.fit(R,yr)    
        pred = model.predict_proba(S)[:, 1]
        preds += [pred]
    probas = [(preds[0][i]+preds[1][i])/2 for i in range(L)]

    df = pd.DataFrame(columns=['Name','Class','Probability','Peptide'])

    classes = [] 
    for i in range(L): 
        if probas[i] >= 0.5  :
            df.loc[i] = [names[i] , 'CPP', probas[i], peps[i]]
        else : 
            df.loc[i] = [names[i] , 'non-CPP', probas[i], peps[i]]
    df = df.set_index('Name')
    print(df)
    csv = fasta_file.strip('.fa')+'.csv'
    df.to_csv(csv)
    print('\n\nThe results have been copied in "'+csv+'" file\n')


    if len(nonalphabetic) > 1 :
        print ('\nThe following entries contain were discarded')
        print('Possible causes: blanks or non-alphabetic characters')
        for a in nonalphabetic :
            print(a[0], a[1])
        print()
    
    return 1


import sys
args = sys.argv 
if len(args) > 1 :
    fasta_file = args[1]
else :
    fasta_file = input('\n\nPlease enter the name of the fasta file (including extension if exists) and hit "enter": ')
fasta_file = fasta_file.strip(' ')


#fasta_file = 'rand_test.fa'
print('\n\n_____________________________________________________________')
print('=============================================================') 
if exists(fasta_file):    
    names, peps, nonalphabetic = check_entries(fasta_file)
    if calc_predictions(names, peps):         
        print('Ended Successfuly')
else:
    print("\n")
    print('"',fasta_file,'"', "doesn't exist in the current/specified directory")
    print("Possible causes: Wrong spelling, Missing file extension, or Wrong path")
print('_____________________________________________________________')
print('=============================================================\n\n')



