"""Unit tests for carrier_intel_mcp._detect_search_type."""

import sys
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

_repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(_repo_root))
sys.path.insert(
    0,
    str(_repo_root / "plugins" / "searchcarriers-carrier-intel" / "scripts"),
)

from carrier_intel_mcp import _detect_search_type  # noqa: E402


class TestDotNumber:
    """Pure digits → DOT search intent."""

    def test_seven_digit_dot(self):
        assert _detect_search_type("1234567") == ("dot", "1234567")

    def test_single_digit(self):
        assert _detect_search_type("5") == ("dot", "5")

    def test_large_dot_number(self):
        assert _detect_search_type("99999999") == ("dot", "99999999")

    def test_leading_zeros(self):
        assert _detect_search_type("0012345") == ("dot", "0012345")


class TestMcNumber:
    """Starts with "MC" + digits → docket search intent."""

    def test_mc_prefix_uppercase(self):
        assert _detect_search_type("MC123456") == ("mc", "123456")

    def test_mc_prefix_lowercase(self):
        assert _detect_search_type("mc123456") == ("mc", "123456")

    def test_mc_mixed_case(self):
        assert _detect_search_type("Mc999999") == ("mc", "999999")

    def test_mc_with_hyphen_is_not_mc(self):
        # "MC-123456" has a hyphen, so upper[2:] = "-123456" which is not .isdigit()
        # Falls through to superSearchTerm
        param, value = _detect_search_type("MC-123456")
        assert param == "text"


class TestVin:
    """17-char alphanumeric → vin."""

    def test_valid_vin(self):
        assert _detect_search_type("SYNTHETICVIN00001") == ("vin", "SYNTHETICVIN00001")

    def test_vin_exactly_17_chars(self):
        vin = "A" * 17
        assert _detect_search_type(vin) == ("vin", vin)

    def test_16_chars_not_vin(self):
        # 16 chars is not a VIN — falls to other checks
        query = "A" * 16
        param, _ = _detect_search_type(query)
        assert param != "vin"

    def test_18_chars_not_vin(self):
        query = "A" * 18
        param, _ = _detect_search_type(query)
        assert param != "vin"

    def test_17_digits_is_dot_not_vin(self):
        # Pure digits: DOT intent wins over VIN (digits check comes first)
        query = "1" * 17
        assert _detect_search_type(query) == ("dot", query)


class TestScac:
    """2-4 uppercase alpha → scac."""

    def test_two_letter_scac(self):
        assert _detect_search_type("JB") == ("scac", "JB")

    def test_four_letter_scac(self):
        assert _detect_search_type("KLLM") == ("scac", "KLLM")

    def test_three_letter_scac(self):
        assert _detect_search_type("UPS") == ("scac", "UPS")

    def test_five_letters_not_scac(self):
        # 5 uppercase letters → too long for SCAC, falls to superSearchTerm
        param, _ = _detect_search_type("ABCDE")
        assert param == "text"

    def test_lowercase_not_scac(self):
        # Must be uppercase to match SCAC
        param, _ = _detect_search_type("jbht")
        assert param == "text"

    def test_single_letter_not_scac(self):
        # 1 char is below the 2-char minimum
        param, _ = _detect_search_type("A")
        assert param == "text"

    def test_mixed_case_not_scac(self):
        param, _ = _detect_search_type("Jb")
        assert param == "text"


class TestSuperSearchTerm:
    """Fallback for anything that doesn't match a specific pattern."""

    def test_company_name(self):
        assert _detect_search_type("Sample Logistics Enterprises") == (
            "text",
            "Sample Logistics Enterprises",
        )

    def test_partial_name(self):
        assert _detect_search_type("Example Freight") == ("text", "Example Freight")

    def test_alphanumeric_mix_short(self):
        # e.g. "ABC1" — has digits so not pure alpha, only 4 chars so not VIN
        assert _detect_search_type("ABC1") == ("text", "ABC1")


class TestWhitespace:
    """Leading/trailing whitespace should be stripped."""

    def test_dot_with_spaces(self):
        assert _detect_search_type("  1234567  ") == ("dot", "1234567")

    def test_mc_with_spaces(self):
        assert _detect_search_type("  MC123456  ") == ("mc", "123456")

    def test_scac_with_spaces(self):
        assert _detect_search_type("  KLLM  ") == ("scac", "KLLM")


class TestSearchTypeProperties:
    """Properties that must hold across broad identifier input sets."""

    @given(st.text(alphabet="0123456789", min_size=1, max_size=24))
    def test_any_nonempty_digit_string_is_dot(self, query):
        assert _detect_search_type(query) == ("dot", query)

    @given(st.text(alphabet="0123456789", min_size=1, max_size=16))
    def test_mc_prefix_is_case_insensitive_and_removed(self, digits):
        assert _detect_search_type(f"mC{digits}") == ("mc", digits)
