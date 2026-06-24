from server.services.memory_lifecycle_service import determine_memory_write_policy


def test_pass_answer_allows_candidate_memory():
    result = determine_memory_write_policy({"grade": "pass", "fail_reasons": []}, False, [])

    assert result["mode"] == "candidate_allowed"
    assert result["can_generate_candidate"] is True


def test_warn_answer_blocks_candidate_memory():
    result = determine_memory_write_policy({"grade": "warn", "fail_reasons": []}, False, [])

    assert result["mode"] == "summary_only"
    assert result["can_generate_candidate"] is False


def test_failed_or_downgraded_answer_blocks_candidate_memory():
    failed = determine_memory_write_policy({"grade": "fail", "fail_reasons": []}, False, [])
    downgraded = determine_memory_write_policy({"grade": "pass", "fail_reasons": []}, True, [])

    assert failed["can_generate_candidate"] is False
    assert downgraded["can_generate_candidate"] is False


def test_privacy_warning_blocks_memory_candidate():
    result = determine_memory_write_policy({"grade": "pass", "fail_reasons": []}, False, ["privacy_risk_detected"])

    assert result["mode"] == "block"
    assert result["can_generate_candidate"] is False
