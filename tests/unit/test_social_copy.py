from engine.editorial.social_copy import publication_description

def test_tags_are_unique_and_at_the_end():
    assert publication_description('Entenda #política esta ideia. #política #debate')=='Entenda esta ideia.\n\n#política #debate'

def test_missing_copy_has_a_non_claim_fallback():
    assert publication_description('','Título do corte')=='Título do corte\n\n#Conteúdo #Reflexão'

def test_question_and_direct_address_survive_hashtag_normalization():
    body='O que pesa mais para você? Pense no programa, além da identidade.'
    assert publication_description(body+' #política #debate')==body+'\n\n#política #debate'

def test_generation_prompt_requires_question_first_and_no_third_person_summary():
    from pathlib import Path
    prompt=(Path(__file__).resolve().parents[2]/'engine/prompts/analysis_v1.txt').read_text(encoding='utf-8')
    assert 'PRIMEIRA frase deve ser uma pergunta' in prompt
    assert 'sem narrar o vídeo na terceira pessoa' in prompt
    assert '3 a 5 hashtags' in prompt
