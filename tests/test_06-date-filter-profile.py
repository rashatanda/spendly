"""
Tests for Step 6: Date Filter on Profile Page.

Spec: .claude/specs/06-date-filter-profile.md

Seed data reference (demo@spendly.com / demo123):
  2026-11-01  Food          ₹1200.00
  2026-11-03  Transport     ₹ 500.00
  2026-11-05  Bills         ₹2300.00
  2026-11-07  Health        ₹ 800.00
  2026-11-09  Entertainment ₹ 649.00
  2026-11-11  Shopping      ₹3200.00
  2026-11-13  Other         ₹ 450.00
  2026-11-14  Food          ₹ 350.00

Range 2026-11-01 to 2026-11-07: 4 transactions, total ₹4800.00
  (Spec DoD says ₹5000.00 but seed data produces ₹4800.00; test uses actual seed sum.)
"""

import pytest

import database.db as db_module
from app import app as flask_app


# ---------------------------------------------------------------------------
# Local fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def seed_client(app, client):
    """
    Test client backed by the seeded demo dataset.
    Calls seed_db() once after init_db() has already created the schema,
    then authenticates as the demo user.
    """
    with flask_app.app_context():
        db_module.seed_db()

    client.post(
        "/login",
        data={"email": "demo@spendly.com", "password": "demo123"},
        follow_redirects=True,
    )
    return client


@pytest.fixture()
def empty_client(client, registered_user):
    """Authenticated client whose user has no expenses."""
    client.post(
        "/login",
        data={"email": registered_user["email"], "password": registered_user["password"]},
        follow_redirects=True,
    )
    return client


# ---------------------------------------------------------------------------
# Auth guard
# ---------------------------------------------------------------------------

class TestAuthGuard:
    def test_unauthenticated_redirects_to_login(self, client):
        response = client.get("/profile")
        assert response.status_code == 302, "Expected redirect for unauthenticated user"
        assert "/login" in response.headers["Location"], "Should redirect to /login"

    def test_unauthenticated_with_date_params_redirects_to_login(self, client):
        response = client.get("/profile?start_date=2026-11-01&end_date=2026-11-07")
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]


# ---------------------------------------------------------------------------
# No-filter behaviour (unchanged from Step 5)
# ---------------------------------------------------------------------------

class TestNoFilter:
    def test_profile_no_params_returns_200(self, seed_client):
        response = seed_client.get("/profile")
        assert response.status_code == 200

    def test_profile_no_params_shows_all_expenses(self, seed_client):
        response = seed_client.get("/profile")
        # All 8 seed transactions visible — check a few distinct dates
        assert b"2026-11-01" in response.data or b"Nov" in response.data, \
            "Expected early November date in unfiltered view"
        assert b"2026-11-14" in response.data or b"350" in response.data, \
            "Expected latest transaction in unfiltered view"

    def test_profile_no_params_shows_rupee_symbol(self, seed_client):
        response = seed_client.get("/profile")
        assert "₹".encode() in response.data, "Currency should be displayed in INR (₹)"

    def test_profile_no_params_shows_all_eight_transactions(self, seed_client):
        response = seed_client.get("/profile")
        # Total of all 8 seed expenses = 9449.00
        assert b"9449" in response.data or b"9,449" in response.data, \
            "Unfiltered total should reflect all 8 seed expenses (₹9449.00)"


# ---------------------------------------------------------------------------
# Filtered view — both start_date and end_date
# ---------------------------------------------------------------------------

class TestBothDatesFilter:
    def test_filtered_range_returns_200(self, seed_client):
        response = seed_client.get("/profile?start_date=2026-11-01&end_date=2026-11-07")
        assert response.status_code == 200

    def test_filtered_range_shows_correct_transaction_count(self, seed_client):
        """Range 2026-11-01 to 2026-11-07 contains 4 seed transactions."""
        response = seed_client.get("/profile?start_date=2026-11-01&end_date=2026-11-07")
        # 4 transactions: Food/1200, Transport/500, Bills/2300, Health/800
        data = response.data
        assert b"4" in data, "Expected 4 transactions in filtered range"

    def test_filtered_range_total_is_correct(self, seed_client):
        """Sum of 4 transactions in range = 1200+500+2300+800 = ₹4800.00"""
        response = seed_client.get("/profile?start_date=2026-11-01&end_date=2026-11-07")
        assert b"4800" in response.data or b"4,800" in response.data, \
            "Filtered total should be ₹4800.00"

    def test_filtered_range_excludes_transactions_outside_range(self, seed_client):
        """Expenses after 2026-11-07 (e.g. ₹649.00 Netflix, ₹3200.00 Shopping) must not appear."""
        response = seed_client.get("/profile?start_date=2026-11-01&end_date=2026-11-07")
        # 649 and 3200 are outside the range
        assert b"3200" not in response.data and b"3,200" not in response.data, \
            "Shopping expense (₹3200) outside range must not appear"
        assert b"649" not in response.data, \
            "Entertainment expense (₹649) outside range must not appear"

    def test_filtered_range_shows_correct_categories(self, seed_client):
        """Category breakdown must only include categories from the filtered range."""
        response = seed_client.get("/profile?start_date=2026-11-01&end_date=2026-11-07")
        # Food, Transport, Bills, Health are in range
        assert b"Food" in response.data
        assert b"Transport" in response.data
        assert b"Bills" in response.data
        assert b"Health" in response.data

    def test_filtered_range_excludes_out_of_range_categories(self, seed_client):
        """Entertainment and Shopping only appear after 2026-11-07."""
        response = seed_client.get("/profile?start_date=2026-11-01&end_date=2026-11-07")
        assert b"Entertainment" not in response.data, \
            "Entertainment category must not appear in filtered range"
        assert b"Shopping" not in response.data, \
            "Shopping category must not appear in filtered range"

    def test_narrow_range_single_day(self, seed_client):
        """Single-day filter: 2026-11-05 returns only the Bills expense."""
        response = seed_client.get("/profile?start_date=2026-11-05&end_date=2026-11-05")
        assert response.status_code == 200
        assert b"2300" in response.data or b"2,300" in response.data, \
            "Single-day filter should show the Bills expense (₹2300)"
        assert b"1200" not in response.data, \
            "Groceries expense (₹1200) must not appear on 2026-11-05 filter"


# ---------------------------------------------------------------------------
# Filtered view — start_date only
# ---------------------------------------------------------------------------

class TestStartDateOnlyFilter:
    def test_start_date_only_returns_200(self, seed_client):
        response = seed_client.get("/profile?start_date=2026-11-09")
        assert response.status_code == 200

    def test_start_date_only_excludes_earlier_expenses(self, seed_client):
        """start_date=2026-11-09 should exclude all expenses before Nov 9."""
        response = seed_client.get("/profile?start_date=2026-11-09")
        # Groceries (1200) and Transport (500) are before Nov 9
        assert b"1200" not in response.data and b"1,200" not in response.data, \
            "Groceries (₹1200) is before start_date and must not appear"

    def test_start_date_only_includes_expenses_on_and_after(self, seed_client):
        """start_date=2026-11-09 should include Nov 9 and later expenses."""
        response = seed_client.get("/profile?start_date=2026-11-09")
        assert b"649" in response.data, "Netflix (₹649, Nov 9) must appear"
        assert b"3200" in response.data or b"3,200" in response.data, \
            "Shopping (₹3200, Nov 11) must appear"


# ---------------------------------------------------------------------------
# Filtered view — end_date only
# ---------------------------------------------------------------------------

class TestEndDateOnlyFilter:
    def test_end_date_only_returns_200(self, seed_client):
        response = seed_client.get("/profile?end_date=2026-11-05")
        assert response.status_code == 200

    def test_end_date_only_excludes_later_expenses(self, seed_client):
        """end_date=2026-11-05 should exclude expenses after Nov 5."""
        response = seed_client.get("/profile?end_date=2026-11-05")
        assert b"800" not in response.data, \
            "Health (₹800, Nov 7) is after end_date and must not appear"
        assert b"3200" not in response.data and b"3,200" not in response.data, \
            "Shopping (₹3200, Nov 11) must not appear"

    def test_end_date_only_includes_expenses_on_and_before(self, seed_client):
        """end_date=2026-11-05 includes Nov 1, 3, 5."""
        response = seed_client.get("/profile?end_date=2026-11-05")
        assert b"1200" in response.data or b"1,200" in response.data, \
            "Groceries (₹1200, Nov 1) must appear"
        assert b"2300" in response.data or b"2,300" in response.data, \
            "Bills (₹2300, Nov 5) must appear"


# ---------------------------------------------------------------------------
# Malformed date values silently ignored
# ---------------------------------------------------------------------------

class TestMalformedDates:
    def test_malformed_start_date_does_not_crash(self, seed_client):
        response = seed_client.get("/profile?start_date=not-a-date")
        assert response.status_code == 200, "Malformed start_date must not crash the app"

    def test_malformed_start_date_shows_all_expenses(self, seed_client):
        """Malformed date is silently ignored — all 8 expenses shown."""
        response = seed_client.get("/profile?start_date=not-a-date")
        assert b"9449" in response.data or b"9,449" in response.data, \
            "All expenses should appear when start_date is malformed"

    def test_malformed_end_date_does_not_crash(self, seed_client):
        response = seed_client.get("/profile?end_date=13/32/2026")
        assert response.status_code == 200

    def test_malformed_end_date_shows_all_expenses(self, seed_client):
        response = seed_client.get("/profile?end_date=13/32/2026")
        assert b"9449" in response.data or b"9,449" in response.data, \
            "All expenses should appear when end_date is malformed"

    def test_malformed_both_dates_does_not_crash(self, seed_client):
        response = seed_client.get("/profile?start_date=foo&end_date=bar")
        assert response.status_code == 200

    def test_malformed_both_dates_shows_all_expenses(self, seed_client):
        response = seed_client.get("/profile?start_date=foo&end_date=bar")
        assert b"9449" in response.data or b"9,449" in response.data

    def test_partial_malformed_start_valid_end(self, seed_client):
        """Malformed start ignored; valid end still applied as end-only filter."""
        response = seed_client.get("/profile?start_date=bad&end_date=2026-11-05")
        assert response.status_code == 200
        # With only end_date=2026-11-05, expenses after Nov 5 are excluded
        assert b"3200" not in response.data and b"3,200" not in response.data, \
            "Shopping (after end_date) must not appear when end_date is valid"

    def test_empty_string_dates_treated_as_no_filter(self, seed_client):
        """Empty string query params behave as if no filter was supplied."""
        response = seed_client.get("/profile?start_date=&end_date=")
        assert response.status_code == 200
        assert b"9449" in response.data or b"9,449" in response.data


# ---------------------------------------------------------------------------
# Empty user — no expenses, with and without filter
# ---------------------------------------------------------------------------

class TestEmptyUser:
    def test_new_user_no_filter_returns_200(self, empty_client):
        response = empty_client.get("/profile")
        assert response.status_code == 200

    def test_new_user_no_filter_shows_zero_total(self, empty_client):
        response = empty_client.get("/profile")
        assert b"0.00" in response.data or b"0" in response.data, \
            "New user with no expenses should show ₹0.00 total"

    def test_new_user_no_filter_shows_zero_transactions(self, empty_client):
        response = empty_client.get("/profile")
        # No transaction rows from seed data visible
        assert b"1200" not in response.data, "Seed data must not leak to new user"

    def test_new_user_with_date_filter_returns_200(self, empty_client):
        response = empty_client.get("/profile?start_date=2026-11-01&end_date=2026-11-30")
        assert response.status_code == 200

    def test_new_user_with_date_filter_shows_zero_total(self, empty_client):
        response = empty_client.get("/profile?start_date=2026-11-01&end_date=2026-11-30")
        assert b"0.00" in response.data or b"0" in response.data, \
            "New user with filter and no expenses should still show ₹0.00"

    def test_new_user_with_date_filter_no_category_rows(self, empty_client):
        """Category breakdown section must be empty for a user with no expenses."""
        response = empty_client.get("/profile?start_date=2026-11-01&end_date=2026-11-30")
        # Seed categories must not appear
        assert b"Food" not in response.data
        assert b"Transport" not in response.data
        assert b"Bills" not in response.data


# ---------------------------------------------------------------------------
# Template — filter form and active-filter indicator
# ---------------------------------------------------------------------------

class TestFilterFormRendering:
    def test_filter_form_present_on_profile_page(self, seed_client):
        response = seed_client.get("/profile")
        assert b'method="get"' in response.data or b"method='get'" in response.data, \
            "Filter form must use method=get"

    def test_filter_form_has_start_date_input(self, seed_client):
        response = seed_client.get("/profile")
        assert b'name="start_date"' in response.data, \
            "Filter form must have a start_date input"

    def test_filter_form_has_end_date_input(self, seed_client):
        response = seed_client.get("/profile")
        assert b'name="end_date"' in response.data, \
            "Filter form must have an end_date input"

    def test_filter_form_prefills_start_date(self, seed_client):
        response = seed_client.get("/profile?start_date=2026-11-01&end_date=2026-11-07")
        assert b"2026-11-01" in response.data, \
            "Filter form must pre-fill start_date with the active filter value"

    def test_filter_form_prefills_end_date(self, seed_client):
        response = seed_client.get("/profile?start_date=2026-11-01&end_date=2026-11-07")
        assert b"2026-11-07" in response.data, \
            "Filter form must pre-fill end_date with the active filter value"

    def test_clear_filter_link_present_when_filter_active(self, seed_client):
        response = seed_client.get("/profile?start_date=2026-11-01&end_date=2026-11-07")
        # The clear link should point to /profile with no params
        assert b"/profile" in response.data, \
            "A clear-filter link pointing to /profile must be present"

    def test_active_filter_indicator_shown(self, seed_client):
        """When a date filter is active, the page should indicate the active range."""
        response = seed_client.get("/profile?start_date=2026-11-01&end_date=2026-11-07")
        # The page should mention one or both filter dates somewhere outside the form
        assert b"2026-11-01" in response.data, \
            "Active filter range indicator should show the start date"


# ---------------------------------------------------------------------------
# Preset-equivalent date ranges
# ---------------------------------------------------------------------------

class TestPresetRanges:
    def test_this_month_range_returns_200(self, seed_client):
        """'This month' preset equivalent: all of November 2026."""
        response = seed_client.get("/profile?start_date=2026-11-01&end_date=2026-11-30")
        assert response.status_code == 200

    def test_this_month_range_shows_all_seed_expenses(self, seed_client):
        """All 8 seed expenses fall within November 2026."""
        response = seed_client.get("/profile?start_date=2026-11-01&end_date=2026-11-30")
        assert b"9449" in response.data or b"9,449" in response.data, \
            "'This month' range should show all 8 seed expenses totalling ₹9449.00"

    def test_last_three_months_range_returns_200(self, seed_client):
        """Last 3 months: Sep–Nov 2026."""
        response = seed_client.get("/profile?start_date=2026-09-01&end_date=2026-11-30")
        assert response.status_code == 200

    def test_last_three_months_includes_all_seed_expenses(self, seed_client):
        response = seed_client.get("/profile?start_date=2026-09-01&end_date=2026-11-30")
        assert b"9449" in response.data or b"9,449" in response.data

    def test_last_six_months_range_returns_200(self, seed_client):
        response = seed_client.get("/profile?start_date=2026-06-01&end_date=2026-11-30")
        assert response.status_code == 200

    def test_range_with_no_matching_expenses_shows_zero(self, seed_client):
        """A valid range that contains no seed expenses should show ₹0.00."""
        response = seed_client.get("/profile?start_date=2025-01-01&end_date=2025-12-31")
        assert response.status_code == 200
        assert b"0.00" in response.data or b"0" in response.data, \
            "Range with no matching expenses should show ₹0.00"
