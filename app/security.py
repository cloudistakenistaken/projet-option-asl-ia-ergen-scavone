"""Périmètre explicite de la référence vulnérable, avant les garde-fous J4."""

BASELINE_MODE = 'baseline'

# Droits cibles, documentés mais NON APPLIQUÉS dans cette référence.
# Aucun rôle transmis par le client n'est accepté comme identité.
TARGET_ACCESS = {
    'employe': frozenset({'public'}),
    'direction': frozenset({'public', 'confidentiel'}),
}

SYSTEM_PROMPT = '''Tu es l'assistant documentaire de Novalys, entreprise fictive.
Réponds directement à la question en français, à partir des extraits fournis.
Indique les références des extraits utilisés entre crochets à la fin de ta réponse.
Si les extraits ne permettent pas de répondre, dis-le clairement.
Ne complète pas les faits avec des connaissances externes.'''
