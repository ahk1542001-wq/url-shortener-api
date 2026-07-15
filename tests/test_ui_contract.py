from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
SCRIPT = (ROOT / "static" / "script.js").read_text(encoding="utf-8")
STYLE = (ROOT / "static" / "style.css").read_text(encoding="utf-8")
TREE = (ROOT / "static" / "tree.html").read_text(encoding="utf-8")


def test_brand_palette_is_consistent_across_private_and_public_ui():
    for source in (STYLE, TREE):
        assert "#2F3A1D" in source
        assert "#CFFF74" in source


def test_mobile_navigation_is_top_only_and_respects_hidden_state():
    assert 'id="main-top-nav"' in INDEX
    assert 'id="main-dock"' not in INDEX
    assert "#main-top-nav:not(.hidden)" in STYLE
    assert "#main-top-nav.hidden" in STYLE
    assert ".nav-btn-text" in STYLE
    assert "display: block" in STYLE
    assert ">Analytics</span>" in INDEX


def test_view_routing_resets_stale_scroll_position():
    assert "history.scrollRestoration = 'manual'" in SCRIPT
    assert "window.scrollTo({ top: 0, left: 0, behavior: 'auto' })" in SCRIPT


def test_mobile_portfolio_separates_content_stats_and_actions():
    assert "#links-list .link-item" in STYLE
    assert "#links-list .link-stats" in STYLE
    assert "#links-list .portfolio-actions-group" in STYLE


def test_link_tree_ui_supports_five_profiles_with_picker_and_switching():
    assert 'id="profile-selection-view"' in INDEX
    assert 'id="profiles-grid"' in INDEX
    assert 'id="add-profile-btn"' in INDEX
    assert 'id="profile-count-badge"' in INDEX
    assert 'class="top-nav-btn switch-profile-btn"' in INDEX
    assert "max_profiles" in SCRIPT


def test_qr_generation_is_local_and_external_qr_services_are_absent():
    assert 'src="/static/qrcode.min.js"' in INDEX
    assert (ROOT / "static" / "qrcode.min.js").is_file()
    combined = INDEX + SCRIPT + TREE
    assert "api.qrserver.com" not in combined
    assert "cdn.jsdelivr.net/npm/qrcode" not in combined


def test_new_links_stay_separate_from_tree_but_legacy_flag_is_preserved_on_edit():
    assert "show_on_tree: false" in SCRIPT
    assert "show_on_tree: currentEditShowOnTree" in SCRIPT
    assert "Show on my public Link Tree" not in INDEX


def test_removed_mode_toggle_is_not_referenced():
    assert "mode-toggle" not in INDEX
    assert "mode-toggle" not in SCRIPT


def test_avatar_upload_reads_structured_api_errors():
    assert "data.error?.message || data.detail || 'Upload failed'" in SCRIPT


def test_public_tree_link_cards_keep_icons_compact():
    assert ".link-arrow" in TREE
    assert "width: 18px" in TREE
    assert "min-height: 58px" in TREE
    assert "text-align: center" in TREE
    assert "position: absolute" in TREE


def test_public_tree_footer_logo_has_dark_background_contrast():
    assert "filter: brightness(0) invert(1)" in TREE
    assert "height: 24px" in TREE
