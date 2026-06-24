from server.privacy_redactor import build_sanitized_context, redact_profile, redact_text


def test_redact_text_masks_direct_sensitive_values():
    text = "我的手机号是 13800138000，邮箱 me@example.com，成本 123.45，仓位 30%"

    redacted = redact_text(text)

    assert "13800138000" not in redacted
    assert "me@example.com" not in redacted
    assert "123.45" not in redacted
    assert "30%" not in redacted
    assert "[REDACTED]" in redacted


def test_redact_profile_keeps_useful_market_context_without_position_details():
    profile = {
        "watchlist": [{"symbol": "0700.HK", "name": "腾讯控股", "market": "港股"}],
        "holdings": [
            {
                "symbol": "0700.HK",
                "name": "腾讯控股",
                "market": "港股",
                "cost_basis_optional": "321",
                "position_size_optional": "40%",
                "risk_tolerance": "中",
                "notes": "成本 321，仓位 40%",
            },
            {"symbol": "SECRET", "name": "机密", "market": "其他", "sensitivity_level": "P4_SECRET"},
        ],
        "projects": [{"name": "个人超级军师", "stage": "FAST-MVP"}],
    }

    sanitized = redact_profile(profile)
    serialized = str(sanitized)

    assert "腾讯控股" in serialized
    assert "321" not in serialized
    assert "40%" not in serialized
    assert "机密" not in serialized
    assert "商业级个人助理项目" in serialized


def test_build_sanitized_context_redacts_manual_context_before_llm():
    context = build_sanitized_context("今天股市怎么样", {}, "账户金额 500000，地址 北京市朝阳区")

    assert context["user_query"] == "今天股市怎么样"
    assert "500000" not in context["manual_context"]
    assert "北京市朝阳区" not in context["manual_context"]
