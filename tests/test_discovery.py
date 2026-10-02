from app.discovery import is_allowed, link_priority


def test_domain_allowlist():
    assert is_allowed("https://scholarships.gov.in/foo", "scholarships.gov.in")
    assert not is_allowed("https://example.com/foo", "scholarships.gov.in")


def test_scholarship_links_prioritized():
    assert link_priority("https://example.gov.in/scholarship/apply") > link_priority("https://example.gov.in/about")
