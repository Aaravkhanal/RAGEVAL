"""Conservative lexical evidence matching; diagnostic, not semantic NLI."""
import re

STOP = set('the a an is are was were be been of to in on at for by with and or it this that has have had its as from'.split())
NEG = {'not','no','never','without','neither','cannot','canceled','cancelled','discontinued'}


def words(text):
    tokens=re.findall(r'[a-z]+',text.lower())
    return {t[:-1] if t.endswith('s') and len(t)>4 else t for t in tokens if t not in STOP}


def numbers(text):
    return set(re.findall(r'(?<!\w)\d+(?:,\d{3})*(?:\.\d+)?%?',text))


def clause_score(premise, claim):
    h=words(claim)
    sentences=re.split(r'(?<=[.!?])\s+',premise)
    candidates=sorted(sentences,key=lambda p:len(words(p)&h)/max(len(h),1),reverse=True)
    best=candidates[0] if candidates else premise
    p=words(best)
    overlap=len(h&p)/max(len(h),1)
    content=(h-NEG)
    shared=content&p
    # A contradictory assertion needs a shared relation, not just a proper name.
    relations=shared & {'revenue','churn','margin','landed','launch','launched','cause','caused','contain','feature','reported','rate','latency','mammal','bird'}
    negated=bool(h&NEG)!=bool(p&NEG)
    if negated and len(shared)>=2 and (relations or overlap>=0.5):
        return 'contradiction'
    hn,pn=numbers(claim),numbers(best)
    if hn-pn and relations and len(shared)>=3:
        return 'contradiction'
    # Named destination substitutions share a relation and subject but disagree
    # about the complement. Do not infer contradiction from unrelated numbers.
    relation=r'\b(landed|located|born)\s+(?:in|on|at)\s+(.+?)(?:[.!?]|$)'
    hm,pm=re.search(relation,claim,re.I),re.search(relation,best,re.I)
    if hm and pm and hm.group(1).lower()==pm.group(1).lower() and len(shared)>=2:
        if not words(hm.group(2)) <= words(pm.group(2)):
            return 'contradiction'
    if hn-pn:
        return 'neutral'
    if overlap>=0.7:
        return 'entailment'
    return 'neutral'


def score(premise, hypothesis):
    clauses=[c.strip() for c in re.split(r'\s+(?:and|but|additionally|furthermore)\s+',hypothesis,flags=re.I) if c.strip()]
    states=[clause_score(premise,c) for c in clauses]
    if len(states)>1 and 'entailment' in states and any(s!='entailment' for s in states):
        return {'entailment':0.4,'neutral':0.5,'contradiction':0.1}
    state=states[0] if len(states)==1 else ('contradiction' if all(s=='contradiction' for s in states) else 'entailment' if all(s=='entailment' for s in states) else 'neutral')
    return {'entailment':0.85,'neutral':0.1,'contradiction':0.05} if state=='entailment' else {'entailment':0.05,'neutral':0.15,'contradiction':0.8} if state=='contradiction' else {'entailment':0.05,'neutral':0.85,'contradiction':0.1}
