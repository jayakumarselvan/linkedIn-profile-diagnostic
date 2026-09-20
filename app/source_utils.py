from urllib.parse import urlparse

PRIMARY_HINTS = (
    ".gov",
    "adgm.com",
    "dfsa.ae",
    "difc.ae",
    "sec.gov",
    "linkedin.com/company",
)

LOW_VALUE_HOSTS = (
    "facebook.com",
    "instagram.com",
    "x.com",
    "twitter.com",
    "tiktok.com",
)


def host_of(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def looks_primary(url: str, subject_name: str, company_name: str | None) -> bool:
    host = host_of(url)
    if any(hint in host for hint in PRIMARY_HINTS):
        return True

    normalized_host = host.replace("-", "").replace(".", "")
    for value in (subject_name, company_name):
        if not value:
            continue
        normalized_value = "".join(ch for ch in value.lower() if ch.isalnum())
        if normalized_value and normalized_value in normalized_host:
            return True
    return False


def is_low_value_url(url: str) -> bool:
    host = host_of(url)
    return any(host == domain or host.endswith(f".{domain}") for domain in LOW_VALUE_HOSTS)
