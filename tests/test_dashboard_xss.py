"""Static XSS regressions for dashboard DOM rendering."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_dashboard_dynamic_api_fields_use_text_content():
    template = (ROOT / "web" / "templates" / "dashboard.html").read_text(encoding="utf-8")

    assert "tr.appendChild(tdText(row.device" in template
    assert "tr.appendChild(tdText(row.interface" in template
    assert "tr.appendChild(tdText(row.ip" in template
    assert "title.textContent=(row.device||'')+' - '+(row.interface||'')" in template
    assert "sub.textContent=parts.join(' | ');" in template


def test_settings_user_table_uses_dom_text_nodes():
    template = (ROOT / "web" / "templates" / "settings.html").read_text(encoding="utf-8")

    assert "tdUser.textContent=u.username" in template
    assert "tdCreated.textContent=u.created_at" in template
    assert "op.textContent=rn" in template


def test_dashboard_template_does_not_interpolate_api_rows_into_inner_html():
    template = (ROOT / "web" / "templates" / "dashboard.html").read_text(encoding="utf-8")
    risky_fragments = [
        "innerHTML=row.",
        "innerHTML=(row.",
        "innerHTML=''+row.",
        "innerHTML=`${row.",
        "+row.device+",
        "+row.interface+",
        "+row.ip+",
    ]
    assert all(fragment not in template for fragment in risky_fragments)
