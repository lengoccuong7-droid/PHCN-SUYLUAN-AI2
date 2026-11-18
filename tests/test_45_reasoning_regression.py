"""Regression tests for PHCN AI 4.5; synthetic cases only."""
import runpy
from core.clinical_engine import analyze_case
from core.feature_extractor import extract_features

_CASES = runpy.run_path('tests/test_case13_14_regression.py')


def test_case13_frozen_shoulder_is_ranked_first_from_objective_arom_prom_and_er():
    result = analyze_case(_CASES['_ca13']())
    assert result['detailed_hypotheses'][0]['key'] == 'shoulder_frozen'
    assert result['temporal_state'] == 'chronic'
    assert 'sensory_symptoms' not in result['features_extracted']
    assert not result['narrative_analysis']['contradictions']


def test_case14_itbs_is_ranked_first_and_negated_symptoms_stay_absent():
    result = analyze_case(_CASES['_ca14']())
    features = set(result['features_extracted'])
    assert result['detailed_hypotheses'][0]['key'] == 'knee_it_band_syndrome'
    assert result['temporal_state'] == 'subacute'
    assert not {'instability', 'locking', 'mechanism_valgus', 'lcl_tenderness', 'sensory_symptoms'} & features
    assert not result['narrative_analysis']['contradictions']


def test_negated_knee_findings_do_not_become_positive_features():
    data = {
        'region': 'Khớp gối',
        'history': 'Không tràn dịch, khóa khớp, mất vững hoặc tê bàn chân. Không có chấn thương valgus.',
    }
    features = extract_features(data, 'Khớp gối')
    assert not {'effusion', 'locking', 'instability', 'sensory_symptoms', 'mechanism_valgus'} & features['codes']
    assert {'locking', 'instability', 'sensory_symptoms'} <= features['negated_features']


def test_dynamic_valgus_is_not_a_valgus_injury_mechanism():
    data = {'region': 'Khớp gối', 'inspection': 'Squat một chân có valgus động và sụt chậu đối bên.'}
    features = extract_features(data, 'Khớp gối')
    assert 'mechanism_valgus' not in features['codes']
