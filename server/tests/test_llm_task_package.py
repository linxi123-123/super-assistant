from server.llm_gateway import FORBIDDEN_OUTPUTS, REQUIRED_OUTPUT_SCHEMA, build_task_package


def test_task_package_contains_privacy_and_output_contract():
    package = build_task_package(
        "market_advisor",
        "今天股市怎么样",
        [{"source": "manual"}],
        {"holdings_summary": [{"holding_summary": "一只港股大型互联网平台股"}]},
        ["no_direct_trading_advice"],
    )

    assert package["task_type"] == "market_advisor"
    assert package["audit_metadata"]["privacy_gateway"] == "enabled"
    assert package["required_output_schema"] == REQUIRED_OUTPUT_SCHEMA
    assert "不得编造行情" in package["forbidden_outputs"]
    assert "no_direct_trading_advice" in package["constraints"]


def test_forbidden_outputs_cover_core_commercial_risks():
    joined = " ".join(FORBIDDEN_OUTPUTS)

    assert "买入" in joined
    assert "卖出" in joined
    assert "实时" in joined
    assert "敏感信息" in joined
