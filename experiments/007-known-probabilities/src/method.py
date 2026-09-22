MODEL='jev-1.13.0'
EXPLICIT='Predict the unobserved outcome of the stated random process. Your option probabilities should represent the mathematical chances of the outcomes, not confidence that an outcome is the most likely. Use only the supplied information.'
def payload(row):
 state={'scenario':row['state']}
 if 'outcomes' in row:
  options=row['outcomes']
  questions={'plain':{'type':'choice','instructions':'Which outcome will occur?','criteria':options},'explicit':{'type':'choice','instructions':EXPLICIT,'criteria':options},'reversed':{'type':'choice','instructions':'Which outcome will occur?','criteria':dict(reversed(list(options.items())))}}
 else:
  state['event']=row['event'];options={'event_occurs':'The event described in `event` occurs.','event_does_not_occur':'The event described in `event` does not occur.'}
  questions={'plain':{'type':'choice','instructions':'Which outcome will occur?','criteria':options},'explicit':{'type':'choice','instructions':EXPLICIT,'criteria':options},'reversed':{'type':'choice','instructions':'Which outcome will occur?','criteria':dict(reversed(list(options.items())))},'noul':{'type':'noul','instructions':'Will the event described in `event` occur?'},'complement':{'type':'noul','instructions':'Will the event described in `event` NOT occur?'},'numeric':{'type':'choice','instructions':'What is the exact mathematical probability that the event described in `event` occurs? Choose the correct numerical answer. Fractions denote exact probabilities.','criteria':{k:'Probability = '+v for k,v in row['numeric_options'].items()}}}
 return {'model':MODEL,'state':state,'questions':questions}
