from interviewlens.common.schemas import AudioMetrics, Transcript
from interviewlens.reasoning.evidence_assembly import assemble_evidence
from interviewlens.reasoning.evidence_validation import validate
from interviewlens.reasoning.vlm_reasoning import VLMReasoner


def _sample_evidence():
    transcript = Transcript(text="um so I worked on it", words=[])
    metrics = AudioMetrics(
        words_per_minute=120, filler_word_count=2, filler_word_rate=0.2,
        long_pause_count=1, long_pause_timestamps=[(1.0, 2.5)], speaking_time_s=8.0,
    )
    return assemble_evidence("Tell me about a challenge.", transcript, metrics, [], fps=30)


def test_vlm_reasoner_mock_output():
    evidence = _sample_evidence()
    reasoner = VLMReasoner()
    output = reasoner.reason(evidence)
    assert output.observations
    assert output.suggestions


def test_evidence_validation_passes_on_mock():
    evidence = _sample_evidence()
    reasoner = VLMReasoner()
    output = reasoner.reason(evidence)
    result = validate(evidence, output)
    assert 0.0 <= result.reliability_score <= 1.0
