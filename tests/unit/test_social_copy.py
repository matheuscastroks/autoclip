from engine.editorial.social_copy import publication_description

def test_tags_are_unique_and_at_the_end():
    assert publication_description('Entenda #política esta ideia. #política #debate')=='Entenda esta ideia.\n\n#política #debate'

def test_missing_copy_has_a_non_claim_fallback():
    assert publication_description('','Título do corte')=='Título do corte\n\n#Conteúdo #Reflexão'
