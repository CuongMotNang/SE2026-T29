from unittest.mock import patch

from scripts.persistence_check import PersistenceCheck

BOOKING_ID = "5f0c7a52-3c1e-4b8e-9a51-2a9b0f6d1c11"


def test_seed_books_first_free_slot():
    check = PersistenceCheck(base_url="http://mock-service")
    responses = [
        (200, [{"starts_at": "2026-10-23T08:00:00+07:00"}]),
        (201, {"id": BOOKING_ID, "status": "booked"}),
    ]
    with patch.object(check, "_http_request", side_effect=responses) as http:
        res = check.seed()
    assert res.success
    assert res.details == {"id": BOOKING_ID, "starts_at": "2026-10-23T08:00:00+07:00"}
    assert http.call_args_list[1].kwargs["body"]["starts_at"] == "2026-10-23T08:00:00+07:00"


def test_seed_fails_when_no_free_slot():
    check = PersistenceCheck(base_url="http://mock-service")
    with patch.object(check, "_http_request", return_value=(200, [])):
        res = check.seed()
    assert not res.success
    assert "No free slot" in res.message


def test_verify_finds_booking_on_later_page():
    check = PersistenceCheck(base_url="http://mock-service")
    other = [{"id": f"other-{i}", "status": "booked"} for i in range(100)]
    responses = [
        (200, {"items": other, "total": 101, "limit": 100, "offset": 0}),
        (200, {"items": [{"id": BOOKING_ID, "status": "booked"}], "total": 101}),
    ]
    with patch.object(check, "_http_request", side_effect=responses):
        res = check.verify(BOOKING_ID)
    assert res.success


def test_verify_fails_when_booking_missing():
    check = PersistenceCheck(base_url="http://mock-service")
    with patch.object(check, "_http_request", return_value=(200, {"items": [], "total": 0})):
        res = check.verify(BOOKING_ID)
    assert not res.success
    assert "not found" in res.message


def test_verify_fails_when_booking_cancelled():
    check = PersistenceCheck(base_url="http://mock-service")
    page = {"items": [{"id": BOOKING_ID, "status": "cancelled"}], "total": 1}
    with patch.object(check, "_http_request", return_value=(200, page)):
        res = check.verify(BOOKING_ID)
    assert not res.success
    assert "cancelled" in res.message
