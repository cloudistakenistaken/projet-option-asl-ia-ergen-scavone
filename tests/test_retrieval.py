import pytest

from app.config import Settings
from app.ingest import read_passages
from app.retrieval import IndexNotReady, Passage, Repository


@pytest.fixture
def settings(tmp_path):
    return Settings(_env_file=None, chroma_dir=tmp_path / 'index',
                    corpus_dir=tmp_path / 'corpus')


def test_persistence_ranking_and_stale_passages(settings):
    repo = Repository(settings, create=True)
    public = Passage('conges', '25 jours', 'public/conges.md', 'public', 0)
    old = Passage('ancien', 'Ancien document', 'public/ancien.md', 'public', 0)
    repo.synchronize([public, old], [[1., 0.], [0., 1.]])
    assert repo.search([[1., 0.]], 5)[0].source == 'public/conges.md'
    new = Passage('aurore', '420 000 euros', 'confidentiel/aurore.md', 'confidentiel', 0)
    repo.synchronize([public, new], [[1., 0.], [0., 1.]])
    repo.synchronize([public, new], [[1., 0.], [0., 1.]])
    reopened = Repository(settings)
    assert reopened.collection.count() == 2
    assert set(reopened.collection.get(include=[])['ids']) == {'conges', 'aurore'}
    result = reopened.search([[0., 1.]], 1)[0]
    assert result.classification == 'confidentiel'  # Référence sans ACL.
    assert result.text == '420 000 euros'
    assert result.distance == pytest.approx(0, abs=1e-5)


def test_missing_empty_and_changed_index(settings):
    with pytest.raises(IndexNotReady, match='absent'):
        Repository(settings)
    repo = Repository(settings, create=True)
    with pytest.raises(IndexNotReady, match='vide'):
        repo.search([[1., 0.]], 1)
    changed = settings.model_copy(update={'embedding_revision': 'autre-revision'})
    with pytest.raises(IndexNotReady, match='Configuration différente'):
        Repository(changed, create=True)
    assert repo.collection.metadata == settings.index_metadata


def test_empty_sync_keeps_existing_index(settings):
    repo = Repository(settings, create=True)
    repo.synchronize([Passage('x', 'Texte', 'public/x.md', 'public', 0)], [[1., 0.]])
    with pytest.raises(ValueError, match='vide'):
        repo.synchronize([], [])
    assert repo.collection.count() == 1


class OnePassageEmbedder:
    def split(self, text, size, overlap):
        return [text] if text else []


def test_corpus_metadata_and_stable_ids(settings):
    path = settings.corpus_dir / 'confidentiel/aurore.md'
    path.parent.mkdir(parents=True)
    path.write_text('Données fictives Aurore', encoding='utf-8')
    first = read_passages(settings, OnePassageEmbedder())
    assert first == read_passages(settings, OnePassageEmbedder())
    assert first[0].source == 'confidentiel/aurore.md'
    assert first[0].classification == 'confidentiel'
    path.write_text('Version modifiée', encoding='utf-8')
    assert first[0].id != read_passages(settings, OnePassageEmbedder())[0].id


def test_unknown_classification_and_empty_corpus_fail(settings):
    with pytest.raises(ValueError, match='Aucun document'):
        read_passages(settings, OnePassageEmbedder())
    settings.corpus_dir.mkdir()
    (settings.corpus_dir / 'sans-classe.md').write_text('Document')
    with pytest.raises(ValueError, match='Classification inconnue'):
        read_passages(settings, OnePassageEmbedder())
