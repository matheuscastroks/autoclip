"""Normalize publishing copy without inventing claims or popularity scores."""
import re

def publication_description(description,title=''):
    tags=list(dict.fromkeys(re.findall(r'#[\w]+',description)))[:5]
    body=' '.join(re.sub(r'#[\w]+','',description).split()).strip()
    if not tags:tags=['#Conteúdo','#Reflexão']
    return (body or title).strip()+'\n\n'+' '.join(tags)
