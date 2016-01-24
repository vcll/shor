# -*- coding: utf-8 -*-
import numpy as np
import time
import os
import pandas as pd
from fractions import gcd
import matplotlib.pyplot as plt
from multiprocessing import Process, Queue

##### FUNCIONS #####

##########################################
##               REGSIZE                ##
##########################################
def RegSize(n):
    len(bin(n)[2:])
    size=0
    while(n!=0):
        n=n>>1
        size+=1
    return size

##########################################
##       EXPONENTIATION FUNCTION        ##
##########################################
def ExpF(y,x,N):
    result=1
    while(x>0):
        if(x % 2 ==1):
            result=(result*y)%N
        x=x>>1
        y=(y*y)%N
    return result


##########################################
##       CONTINUED FRACTION APR.        ##
##########################################
def continued_fraction(x, y):
    #This applies the continued fraction expansion to two numbers x/y
    #x is the numerator and y is the denominator
#    x = int(x)
#    y = int(y)
    tmp = x//y
    if tmp*y == x:
        return [tmp, ]
  
    list = continued_fraction(y, x - tmp*y)
    list.insert(0, tmp)
    return list


def process_exp(floor,ceil,y,N):
        que.put([ExpF(y,i,N) for i in xrange(floor,ceil)])

def process_reg(floor,ceil,y,N):
        que.put([[i,q**(-0.5),0]  for i in xrange(floor,ceil)])


#################################################################


N=341
#N=1073
#N=629
#N=41*53
print "Escriu un número a factoritzar:"
N=int(input())

t1=time.clock()
solution=False

que=Queue()

while(not solution):

    y=np.random.random_integers(1,high=N)   
    print "############################# y = ",y," ##################################"
    
    # Fa falta un if per anar provant diferents valors fins que r sigui tal que: 
    sqr=np.sqrt(N)
    if sqr-int(sqr)==0:
        p=sqr
        q=sqr
        print "Found!!! \n p: ",p,"\t q: ",q,"\n p·q:",p*q,"\t N:",N
        solution=True
    elif gcd(y,N) != 1:
        print "Solució trobada! Cas no trivial:"
        p=gcd(y,N)
        q=N/p
        print p,q
        solution=True
    else:
        # Nomber of qbits
        n=len(bin(N*N)[2:]) 
        q=int(np.exp2(n))
        # Cas on l'ordre del register és igual al de ancilla
        # Directament ja fem l'exponenciació de l'ancilla
        repeat_quant=True
        que=Queue()
        while(repeat_quant):
            t000=time.clock()
            p1 = Process(target=process_reg, args=(0,q/4,y,N))
            p2 = Process(target=process_reg, args=(q/4,2*q/4,y,N))
            p3 = Process(target=process_reg, args=(2*q/4,3*q/4,y,N))
            p4 = Process(target=process_reg, args=(3*q/4,q,y,N))
            
            p1.start()
            p2.start()
            p3.start()
            p4.start()
            
            r1=que.get()
            r2=que.get()
            r3=que.get()
            r4=que.get()
            r=r1+r2+r3+r4
            print "Fet!!", time.clock()-t000
            reg=pd.DataFrame(r, columns=['state','prob','ancilla'])
            t001=time.clock()
            print "Time used creating the register ",t001-t000

            # Exponentiation
            p1 = Process(target=process_exp, args=(0,q/4,y,N))
            p2 = Process(target=process_exp, args=(q/4,2*q/4,y,N))
            p3 = Process(target=process_exp, args=(2*q/4,3*q/4,y,N))
            p4 = Process(target=process_exp, args=(3*q/4,q,y,N))

            p1.start()
            p2.start()
            p3.start()
            p4.start()
            
            r1=que.get()
            r2=que.get()
            r3=que.get()
            r4=que.get()
            r=r1+r2+r3+r4
            reg.ancilla=r
            t002=time.clock()
            print "Time used with the exponentiation ",t002-t001




            # Measure on the ancilla 
            phi3=reg.set_index(['ancilla'])
             
            control=True
            while(control):
                try:
                    measure=reg.ancilla[np.random.random_integers(0,high=len(reg))]
                    phi3=phi3.loc[reg.ancilla[measure]]
                    control=False
                except:
                    pass
#            phi3=phi3.loc[measure]

            #Normalising the probability
            prob=1./np.sqrt(len(phi3))
            reg.loc[reg.ancilla==measure,'prob']=prob
            reg.loc[reg.ancilla!=measure,'prob']=0.

            #print "Mesura ancilla:", measure
            suma=sum(abs(np.power(reg.prob,2)))
            # Check if it is well normalised
            if (suma!=1):
                reg.prob=reg.prob/np.sqrt(suma)
                suma=sum(abs(np.power(reg.prob,2)))
                

            #print "Suma prob despres de mesura",suma


            phi3=None
            measure=None
            # Quantum fourier transform
            #reg.loc[:,'qft']=np.fft.fft(reg.prob)*np.power(q,-0.5)
            reg.prob=np.fft.fft(reg.prob)*np.power(q,-0.5)

            #while(repeat_quant):
            # Weigted measure of k  
            k=np.random.choice(reg.state,p=abs(np.power(reg.prob,2)))
            print "k measured: ",k
            if k==0:
                repeat_quant=True
                # The first peak is always in k=0. We don't want this
            else:
                ri=1 # Multiplicitat del pic
                secpeak=False
                # For a k different than 0, only the 2nd peak (1st p. is k=0) will give 
                # us a good value of r. And instead of choosing a random number of
                # k each time, one can divide the value of k  until one obtain
                # the correct (or almost) value for the 2nd peak
                while(not secpeak):

                    rlist=[int(ri*1.*q/k), round(ri*1.*q/k)]

                    for item in rlist:
                        if (item==0):
                            r=-1 # Error code
                        elif item%2==1:
                            r=-2
                        elif(item>=N):
                            r=-3
                        elif int(np.power(2,item))%N!=1:
                            r=-4 # Error code
                        else: 
                            r=item
                            break
                    #print 'r: ',r
                    if r<=0:
                        pass
                    else:
                        secpeak=True
                        x=int(ExpF(y,int(r*0.5),N))
                        print "x : ", x, "\t y: ",y,"\t r: ",r
                        if (x==1)or(x==-1):
                            pass # Choose another y
                        else:
                            p=gcd(int(x+1),N)
                            q=gcd(int(x-1),N)
                            if p==1 or q==1:
                                solution=False
                            else:
                                solution=True
                                print "Found!!! \n p: ",p,"\t q: ",q,"\n p·q:",p*q,"\t N:",N
                                print "Qbits used: ",2*n, "\t y=", y 
                        repeat_quant=False
                    ri+=1
                    if ri>=300000:
                        secpeak=True
                        print "Not foud. Starting again"
                    #    print "So many time trying. Computing another k"
            
            reg=None
t2=time.clock()
print "Time used: ", t2-t1 
