"""Present answer accuracy separately from fidelity of probability outputs."""
import json
from pathlib import Path

INTRO = '''# Using Jev for probability questions: two different tasks

**Give Jev numerical options when you want it to select a probability answer. For a direct yes/no probability estimate, Noul was closest to the truth in this test.** These are different results, measured in different ways.

We tested Jev 1.13.0 on coins, dice, cards and other scenarios with exact mathematical answers. All 68 primary cases completed successfully. The main comparison uses the same 60 binary-event problems. Prompts were frozen before the run.

## 1. How should I ask for the correct numerical probability?

Use **Choice with numbers as the answers**. For example:

> A fair coin is flipped once. What is the probability of heads?
> Choose: **1/2, 1/100, 1/6, or 3/4.**

Jev selected **1/2**. Across all 60 problems, it selected the correct numerical probability **60 times out of 60**.

![Numerical-answer Choice selected the correct probability in all 60 problems. The exact answer was included among four options.](numerical-answer-accuracy.png)

**What this tells a builder:** when your task is selecting a probability from supplied candidates, this approach worked very well here. Read the selected number as the answer. A high probability assigned to the option “1/2” means support for that answer; it does not mean the coin itself is almost certain to land heads.

**Boundary of the result:** we supplied the exact answer among four candidates every time. This measures answer-selection accuracy, not calibration or free-form calculation. We did not compare multiple numerical-answer methods, test a fixed percentage grid, or test what happens when the correct answer is absent. So this is a successful tested approach, not proof that Choice is universally the best way to solve probability problems.

## 2. Which output most closely matches an event's actual probability?

Here the options are **outcomes**, not numbers. We compare the returned probability with the event's mathematical chance.

For the same fair-coin scenario, simplified wording makes the distinction clear:

| Method | What we ask | What we read | Saved result | Correct value |
|---|---|---|---:|---:|
| Numerical-answer Choice | “What is the probability?” Options: 1/2, 1/100, 1/6, 3/4 | The selected number | **50%** | 50% |
| Yes/no Noul | “Will the heads event occur?” | Probability of yes | **55%** | 50% |
| Outcome Choice | “Which outcome will occur?” Options: event occurs / does not occur | Probability assigned to the event | **88%** | 50% |
| Outcome Choice + probability instruction | Same outcome options, asking the output probabilities to represent mathematical chances | Probability assigned to the event | **96%** | 50% |

All four examples above come from case P001. The earlier **94% heads** result comes from a separate case, P061, whose options are explicitly named “heads” and “tails.”

**Noul was the closest direct estimate:** its mean absolute error was **5.56 percentage points**, versus **21.14** for ordinary outcome Choice. Adding an explicit probability instruction to outcome Choice increased the error to **29.41 points** in this run. This instruction does **not** refer to the numerical-answer method that scored 60/60.

![Direct event-probability estimates: Noul has the lowest mean absolute error among five tested variants. Numerical-answer accuracy is a different metric and is shown separately.](event-probability-error.png)

A 20-percentage-point error means, for example, returning 70% when the truth is 50%. Lower error is better. The chart compares five ways of obtaining an event probability on the same 60 cases, with no missing responses. The 60/60 numerical-answer result is deliberately shown in its own visual because counting correct answers is a different measurement.

## What should I use in practice?

| Your task | What this experiment supports | Important limit |
|---|---|---|
| Select a numerical probability from a finite set | Try **numerical-answer Choice** and read the selected value | The correct value must be represented; our exact-answer candidate sets were constructed using the known truth |
| Obtain a direct probability for a yes/no event | **Noul** is the best starting point among the methods tested here | It still made errors; validate its probabilities on examples from your application |
| Obtain a full distribution over several possible outcomes | Validate outcome Choice's distribution carefully before using it as real-world odds | We did not establish a reliable method for this task; independently estimating every outcome with Noul was not tested |
| Calculate exact odds from known counts or rules | Use deterministic calculations when practical | This is engineering guidance, not another model evaluated in the experiment |

Do not interpret the selected option's probability or Choice's separate `confidence` field as interchangeable with the event's chance. Do not assume independently asking about an event and its opposite will produce probabilities that add to 100%: Noul missed that total by **7.55 points on average**, and **25 points at worst**, here.

## Are these tests of “correct answers” and “calibration”?

Those are useful starting questions, but the precise questions answered here are:

1. **Can Jev select the correct numerical probability when it is offered as a candidate?** Yes, in 60/60 of these cases.
2. **How closely do Jev's probability outputs match known event probabilities?** Noul was closest among the direct-output methods tested.

The second is relevant to calibration, but we call the measured quantity **probability-estimation error**. A conventional calibration study would also ask whether events assigned, say, 70% happen about 70% of the time across relevant cases. This small, authored suite with analytically known chances does not establish calibration across real-world applications. The 60/60 result does not establish calibration of confidence in numerical answers, either.

The results reveal a difference in behavior across questions and outputs. They do not establish Jev's architecture or how it represents probability knowledge internally.

'''

def build(out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    result=json.loads((out/'results.json').read_text());s=result['summary']
    root=out.parent
    old=(out/'README.md').read_text()
    detail='## What we tested'+old.split('## What we tested',1)[1]
    replacements={
        'Choice: ordinary outcome question':'Outcome Choice',
        'Choice: explicit probability instructions':'Outcome Choice + probability instruction',
        'Choice: reversed option order':'Outcome Choice, reversed options',
        'Noul: will the event occur?':'Yes/no Noul',
        'Noul: 1 − probability of the opposite':'Noul via the opposite event',
        'Explicit probability Choice':'Outcome Choice + probability instruction',
        'Explicit Choice':'Outcome Choice + probability instruction',
        'explicit Choice':'outcome Choice + probability instruction',
        'Ordinary Choice':'Outcome Choice',
        'ordinary Choice':'outcome Choice',
        'Reversed Choice':'Outcome Choice, reversed options',
        'Numerical control':'Numerical-answer Choice control',
        'Copies and retrieval provenance are retained in the experiment.':'Retrieval provenance is included; third-party documentation snapshots remain in the original workspace.'
    }
    for a,b in replacements.items():detail=detail.replace(a,b)
    text=INTRO+detail
    (out/'README.md').write_text(text)
    # Preserve the repository-specific reproduction instructions.
    root_readme=root/'README.md'
    previous=root_readme.read_text() if root_readme.exists() else ''
    tail='\n## Reproduce the saved results'+previous.split('## Reproduce the saved results',1)[1] if '## Reproduce the saved results' in previous else ''
    for name in ['numerical-answer-accuracy.png','event-probability-error.png','binary-results.csv','multiclass-results.csv','results.json']:
        text=text.replace('('+name+')','(results/'+name+')')
    root_readme.write_text(text+tail)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,'axes.spines.top':False,'axes.spines.right':False})
    teal='#167a72';ink='#183044';muted='#526477'
    # A count visual, with no probability-error axis or competing metrics.
    fig=plt.figure(figsize=(12,6),facecolor='white')
    fig.text(.055,.90,'1. Want the correct probability number?',fontsize=24,weight='bold',color=ink)
    fig.text(.055,.83,'Use Choice with numerical answers: 1/2, 1/100, 1/6, 3/4.',fontsize=15,color=muted)
    fig.text(.055,.64,f'{s["numeric_correct"]}/{s["numeric_total"]}',fontsize=65,weight='bold',color=teal)
    fig.text(.06,.54,'correct numerical selections',fontsize=17,color=ink)
    ax=fig.add_axes([.52,.39,.43,.34]);ax.set_xlim(-.7,9.7);ax.set_ylim(-.7,5.7)
    for k in range(60):ax.scatter(k%10,5-k//10,s=170,color=teal if k<s['numeric_correct'] else '#cc7558',marker='s')
    ax.axis('off');fig.text(.54,.34,'Each square = one probability problem',fontsize=12,color=muted)
    fig.text(.06,.36,'Fair-coin example\nJev selected “1/2.”\nThat is the correct answer.',fontsize=16,linespacing=1.5,color=ink)
    fig.text(.055,.17,'Test condition: the exact answer was included among four options every time.',fontsize=13,color=ink)
    fig.text(.055,.105,'This measures answer accuracy. It does not measure calibration of API probability fields.',fontsize=12,color=muted)
    fig.text(.055,.045,'Jev 1.13.0  •  60 problems  •  Frozen questions  •  No failed responses',fontsize=10,color=muted)
    for ext in ['png','svg']:fig.savefig(out/f'numerical-answer-accuracy.{ext}',dpi=160,facecolor='white')
    plt.close(fig)
    # Error visual: all five methods estimate the same event probability.
    fig,ax=plt.subplots(figsize=(12,7.4),facecolor='white');fig.subplots_adjust(left=.39,right=.91,top=.74,bottom=.25)
    fig.text(.055,.925,'2. Want the event’s actual probability?',fontsize=24,weight='bold',color=ink)
    fig.text(.055,.865,'Noul was the closest direct estimate in this test.',fontsize=16,color=teal,weight='bold')
    fig.text(.055,.81,'Mean absolute error across the same 60 problems. Lower is better.',fontsize=13,color=muted)
    variants=['noul','complement_inverted','reversed','plain','explicit']
    names=['Yes/no Noul','Noul via the opposite event¹','Outcome Choice\n(reversed option order)','Outcome Choice','Outcome Choice\n+ probability instruction²']
    vals=[s['binary'][v]['mae_pp'] for v in variants]
    ax.barh(range(5),vals,color=[teal,'#75aaa4','#9aabb8','#6c8295','#bc775a'],height=.60)
    ax.set_yticks(range(5),names,fontsize=12);ax.invert_yaxis();ax.set_xlim(0,34);ax.set_xticks([0,5,10,15,20,25,30]);ax.set_xlabel('Average error (percentage points)',labelpad=10)
    ax.spines['left'].set_visible(False);ax.tick_params(axis='y',length=0,pad=15);ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True)
    for i,v in enumerate(vals):ax.text(v+.55,i,f'{v:.2f}',va='center',weight='bold',color=ink)
    fig.text(.055,.145,'¹ Subtract the probability of “not happening” from 100%.',fontsize=11,color=muted)
    fig.text(.055,.10,'² Options are outcomes, not numbers. This is different from the 60/60 numerical-answer test.',fontsize=11,color=muted)
    fig.text(.055,.04,'Jev 1.13.0  •  Noul still averaged 5.56 points of error; validate on your own application.',fontsize=11,color=muted)
    for ext in ['png','svg']:fig.savefig(out/f'event-probability-error.{ext}',dpi=160,facecolor='white')
    plt.close(fig)
    print('Wrote two separate result stories, README files and four figure assets.')
