from app.source_utils import is_low_value_url, looks_primary


def test_company_domain_counts_as_primary() -> None:
    assert looks_primary("https://examplecapital.com/about", "Jane Founder", "Example Capital")


def test_regulator_domain_counts_as_primary() -> None:
    assert looks_primary("https://www.difc.ae/public-register/example", "Jane Founder", None)


def test_low_value_social_url() -> None:
    assert is_low_value_url("https://twitter.com/person")
