from src.analytics import analytics_buffer, _flush_now


def test_flush_analytics(auth_client):
    # Clear buffer initially
    analytics_buffer.clear()

    # Create a link
    r = auth_client.post(
        "/api/shorten",
        json={"url": "https://example.com/flush", "custom_code": "flushtest"},
    )
    assert r.status_code == 201

    # Add clicks to buffer manually
    analytics_buffer["flushtest"] += 5

    # Flush
    _flush_now()

    # Verify buffer is clear
    assert "flushtest" not in analytics_buffer or analytics_buffer["flushtest"] == 0

    # Verify DB has 5 clicks
    r = auth_client.get("/api/stats/flushtest")
    assert r.status_code == 200
    assert r.json()["click_count"] == 5

    # Add more clicks and flush again
    analytics_buffer["flushtest"] += 3
    _flush_now()

    r = auth_client.get("/api/stats/flushtest")
    assert r.status_code == 200
    assert r.json()["click_count"] == 8
