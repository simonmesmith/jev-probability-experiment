"""Author synthetic cases and exact rational answers before any inference."""
from fractions import Fraction as F
from itertools import product, combinations
from math import comb
import random
from common import ROOT,dump
cases=[];gold={}
def add(group,state,event,p,derivation,options=None):
 i=f'P{len(cases)+1:03d}';p=F(p)
 row={'id':i,'group':group,'state':state,'event':event}
 if options:row['outcomes']=options
 else:
  pool=[F(0),F(1,100),F(1,20),F(1,10),F(1,6),F(1,4),F(1,3),F(1,2),F(2,3),F(3,4),F(9,10),F(99,100),F(1)]
  rng=random.Random(i);distractors=rng.sample([v for v in pool if v!=p],3);values=[p,*distractors];rng.shuffle(values)
  row['numeric_options']={f'answer_{k+1}':str(v) for k,v in enumerate(values)}
  correct=next(k for k,v in row['numeric_options'].items() if F(v)==p)
 cases.append(row)
 gold[i]={'p':float(p),'fraction':str(p),'derivation':derivation}
 if not options:gold[i]['numeric_correct']=correct
 return i

# Coins: exact enumeration independently agrees with the binomial formula.
for n,k in [(1,1),(1,0),(2,0),(2,1),(2,2),(3,1),(3,2),(4,2),(5,0),(5,3),(8,4),(10,10)]:
 p=F(comb(n,k),2**n);assert p==F(sum(sum(v)==k for v in product([0,1],repeat=n)),2**n)
 add('coins',f'A fair coin is flipped {n} time(s). Flips are independent. No outcomes have been observed.',f'Exactly {k} of the {n} flips land heads.',p,f'C({n},{k}) / 2^{n} = {p}')
for h,n,k in [(F(1,10),1,1),(F(9,10),1,1),(F(1,4),2,2),(F(3,4),2,1),(F(1,5),3,0),(F(4,5),3,2)]:
 p=comb(n,k)*h**k*(1-h)**(n-k)
 add('biased_coins',f'A coin lands heads with probability {h} and tails otherwise. It is flipped {n} time(s) independently. No outcomes are observed.',f'Exactly {k} flips land heads.',p,f'C({n},{k})*({h})^{k}*(1-{h})^{n-k} = {p}')
die=list(product(range(1,7),repeat=2))
for description,predicate in [('The sum is 2.',lambda a,b:a+b==2),('The sum is 7.',lambda a,b:a+b==7),('The sum is at least 10.',lambda a,b:a+b>=10),('Both dice show the same number.',lambda a,b:a==b),('At least one die shows 6.',lambda a,b:a==6 or b==6),('The sum is even.',lambda a,b:(a+b)%2==0),('The first die is greater than the second.',lambda a,b:a>b),('The product is odd.',lambda a,b:(a*b)%2==1),('The sum is 13.',lambda a,b:a+b==13),('The sum is between 2 and 12 inclusive.',lambda a,b:2<=a+b<=12)]:
 count=sum(predicate(a,b) for a,b in die)
 add('dice','Two fair six-sided dice numbered 1 through 6 are rolled independently. Neither result is observed.',description,F(count,36),f'Enumerate 36 ordered pairs; {count} satisfy the event.')
deck=list(product(['hearts','diamonds','clubs','spades'],range(1,14)))
for description,predicate in [('The card is a heart.',lambda s,r:s=='hearts'),('The card is red.',lambda s,r:s in ['hearts','diamonds']),('The card is an ace.',lambda s,r:r==1),('The card is a face card (jack, queen or king).',lambda s,r:r>=11),('The card is a red ace.',lambda s,r:r==1 and s in ['hearts','diamonds']),('The card is a heart or an ace (or both).',lambda s,r:s=='hearts' or r==1),('The card is the queen of spades.',lambda s,r:s=='spades' and r==12),('The card is neither a heart nor an ace.',lambda s,r:s!='hearts' and r!=1)]:
 count=sum(predicate(s,r) for s,r in deck)
 add('cards','One card is drawn uniformly from a standard 52-card deck with no jokers. The card is not observed.',description,F(count,52),f'Enumerate 52 cards; {count} satisfy the event.')
for red,blue,n,k,replace in [(1,9,1,1,False),(9,1,1,1,False),(3,7,2,2,False),(3,7,2,2,True),(5,5,2,1,False),(5,5,2,1,True),(2,8,3,0,False),(7,3,3,2,False),(1,9,2,2,False),(10,0,2,2,False)]:
 if replace:p=comb(n,k)*F(red,red+blue)**k*F(blue,red+blue)**(n-k);deriv=f'C({n},{k})*({red}/{red+blue})^{k}*({blue}/{red+blue})^{n-k}'
 else:
  p=F(comb(red,k)*comb(blue,n-k),comb(red+blue,n));deriv=f'C({red},{k})*C({blue},{n-k})/C({red+blue},{n})'
  balls=[1]*red+[0]*blue;assert p==F(sum(sum(v)==k for v in combinations(balls,n)),comb(red+blue,n))
 add('sampling',f'A bag contains {red} red and {blue} blue balls. Draw {n} balls uniformly {"with replacement, mixing after every draw" if replace else "without replacement"}. No colors are observed.',f'Exactly {k} drawn balls are red.',p,deriv+' = '+str(p))
for lo,hi,description,predicate in [(1,10,'The integer is even.',lambda x:x%2==0),(1,100,'The integer is 1.',lambda x:x==1),(1,100,'The integer is at most 99.',lambda x:x<=99),(0,9,'The integer is at least 8.',lambda x:x>=8),(1,12,'The integer is divisible by 3.',lambda x:x%3==0),(1,20,'The integer is prime.',lambda x:x in [2,3,5,7,11,13,17,19])]:
 count=sum(predicate(x) for x in range(lo,hi+1))
 add('uniform_integers',f'An integer is selected uniformly from {lo} through {hi} inclusive. Its value is not observed.',description,F(count,hi-lo+1),f'{count} favorable values / {hi-lo+1} equally likely values.')
for base,sens,fp in [(F(1,100),F(9,10),F(1,10)),(F(1,2),F(9,10),F(1,10)),(F(1,1000),F(99,100),F(1,100)),(F(1,10),F(4,5),F(1,5))]:
 p=base*sens/(base*sens+(1-base)*fp)
 add('conditional',f'A factory makes items. Fraction {base} are defective. A detector flags a defective item with probability {sens}, and flags a nondefective item with probability {fp}. An item is sampled uniformly from production and is observed to be flagged.', 'The sampled item is defective.',p,f'Bayes: ({base}*{sens})/({base}*{sens}+(1-{base})*{fp}) = {p}')
for state,event,p,deriv in [
 ('A fair six-sided die numbered 1 through 6 is rolled. You learn only that the result is even.','The result is 6.',F(1,3),'Possible results {2,4,6}; one of three is 6.'),
 ('One card is drawn uniformly from a standard 52-card deck. You learn only that it is red.','The card is a heart.',F(1,2),'13 hearts among 26 red cards.'),
 ('A bag has 3 red and 7 blue balls. Two balls are drawn uniformly without replacement. The first is observed to be red; the second has not been observed.','The second ball is red.',F(2,9),'After removing a red ball, 2 of 9 remaining balls are red.'),
 ('A prize is placed uniformly behind one of three doors. You choose door 1. A host who knows the location always opens a different, empty door and always offers a switch. If both other doors are empty, the host chooses between them uniformly. You switch to the remaining unopened door.','You win the prize.',F(2,3),'Switching wins exactly when the original choice is wrong: 2/3.')]:add('conditional',state,event,p,deriv)
assert len(cases)==60

def multi(state,items,deriv):
 opts={k:d for k,d,p in items};probs={k:float(p) for k,d,p in items}
 assert sum(F(p) for k,d,p in items)==1
 i=add('multiclass',state,'',0,deriv,opts);gold[i]={'distribution':probs,'fractions':{k:str(p) for k,d,p in items},'derivation':deriv}
multi('A fair coin is flipped once. No result has been observed.',[('heads','The coin lands heads.',F(1,2)),('tails','The coin lands tails.',F(1,2))],'Two equally likely sides.')
multi('A fair six-sided die numbered 1 through 6 is rolled. No result has been observed.',[(f'face_{i}',f'The die shows {i}.',F(1,6)) for i in range(1,7)],'Six equally likely faces.')
multi('One card is drawn uniformly from a standard 52-card deck. No card is observed.',[(s,'The card is '+s+'.',F(1,4)) for s in ['hearts','diamonds','clubs','spades']],'13 cards in each of four suits.')
multi('A fair coin is flipped twice independently. No results are observed.',[(f'heads_{k}',f'Exactly {k} flips are heads.',F(comb(2,k),4)) for k in range(3)],'Binomial(2, 1/2).')
multi('Two fair six-sided dice numbered 1 through 6 are rolled independently. No results are observed.',[(f'sum_{k}',f'The sum is {k}.',F(sum(a+b==k for a,b in die),36)) for k in range(2,13)],'Count each sum among 36 equally likely ordered pairs.')
multi('One ball is drawn uniformly from a bag containing 1 red, 2 blue and 7 green balls. No color is observed.',[(c,f'The ball is {c}.',F(n,10)) for c,n in [('red',1),('blue',2),('green',7)]],'Color counts divided by 10.')
multi('A pointer stops uniformly around a circular spinner. Red occupies 180 degrees, blue 90 degrees, green 60 degrees and yellow 30 degrees. The result has not been observed.',[(c,f'The pointer stops on {c}.',F(n,360)) for c,n in [('red',180),('blue',90),('green',60),('yellow',30)]],'Sector angles divided by 360.')
multi('Two fair coins are flipped independently. Their ordered outcomes have not been observed.',[(v,f'The first coin is {v[0]} and the second is {v[1]}, where H means heads and T tails.',F(1,4)) for v in ['HH','HT','TH','TT']],'Four equally likely ordered pairs.')
dump(ROOT/'data/cases.json',cases);dump(ROOT/'data/answers.json',gold)
print(f'Created {len(cases)} cases, including 60 binary and 8 multiclass. Exact enumeration checks passed.')
