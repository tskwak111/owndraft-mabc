from owndraft.patterns.catalog import load_pattern_catalog

REQUIRED_CODES = {
    "era_background_intro",
    "importance_inflation",
    "unsupported_future_outlook",
    "abstract_positive_effect",
    "promotional_superlative",
    "vague_authority",
    "false_balance",
    "empty_implication",
    "conclusion_repetition",
    "meta_roadmap",
    "vague_problem_statement",
    "unjustified_social_generalization",
    "mechanical_triple_list",
    "uniform_paragraph_length",
    "repeated_claim_explain_summary",
    "excessive_headings",
    "unnecessary_ordinal_structure",
    "uniform_sentence_length",
    "rhetorical_question_answer",
    "pros_cons_conclusion_template",
    "parallel_grammar_overfit",
    "oversized_conclusion",
    "beyond_x_to_y",
    "connector_repetition",
    "can_do_ending_repetition",
    "aspect_phrase_overuse",
    "nominalization_overuse",
    "passive_voice_overuse",
    "translationese",
    "dash_colon_overuse",
    "triple_adjective_list",
    "excessive_hedging",
    "automatic_conclusion_marker",
    "importance_possibility_repetition",
    "not_x_but_y_drama",
    "fake_depth_phrase",
    "empty_adverb",
    "decoration_overuse",
    "chatbot_greeting_closing",
    "mismatched_formality",
}


def test_catalog_contains_exactly_40_unique_rules():
    rules = load_pattern_catalog()
    assert len(rules) == 40
    assert len({rule.code for rule in rules}) == 40
    assert all(rule.description_ko for rule in rules)
    assert all(rule.default_action in {"keep", "rewrite", "delete", "ask"} for rule in rules)


def test_catalog_matches_required_codes():
    rules = load_pattern_catalog()
    assert {rule.code for rule in rules} == REQUIRED_CODES


def test_catalog_categories_and_examples_present():
    rules = load_pattern_catalog()
    assert all(rule.category in {"content", "structure", "expression"} for rule in rules)
    assert all(rule.severity in {"low", "medium", "high"} for rule in rules)
    assert all(isinstance(rule.examples, list) and rule.examples for rule in rules)
    assert all(isinstance(rule.exemptions, list) for rule in rules)


def test_catalog_regexes_compile():
    import re

    rules = load_pattern_catalog()
    for rule in rules:
        for pattern in rule.regexes:
            re.compile(pattern)
