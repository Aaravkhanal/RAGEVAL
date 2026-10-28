"""Unit tests for evidence span localization."""

from ragtruth.core.schemas import Chunk
from ragtruth.evaluator.span_localizer import SpanLocalizer


def test_span_localization_exact_sentence():
    chunk = Chunk(
        id="c_bio",
        doc_id="d_bio",
        text=(
            "Veloceptin is a humanized monoclonal IgG1 antibody. "
            "Median progression-free survival reached 14.8 months in the combination cohort. "
            "Discontinuation due to adverse events was 9.4%."
        ),
        chunk_index=0,
        token_count=30,
        start_char=0,
        end_char=180,
    )

    claim = "Median progression-free survival was 14.8 months in clinical trials"
    match = SpanLocalizer.find_best_evidence_span(claim, chunk, is_supporting=True)

    assert match is not None
    assert match.is_supporting is True
    assert "14.8 months" in match.exact_span
    assert match.start_char >= 0
    assert match.end_char > match.start_char
    assert chunk.text[match.start_char : match.end_char] == match.exact_span
