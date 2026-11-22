import unittest
from datetime import datetime, timedelta, timezone

from vac_core.engine import Grant, evaluate


NOW = datetime(2026, 11, 23, 0, 0, tzinfo=timezone.utc)


def grant(**changes):
    values = dict(
        grant_id="g-1", owner_id="owner-1", subject_id="agent-1",
        resource="profile:summary", purpose="answer_question",
        expires_at=NOW + timedelta(hours=1), revoked_at=None,
    )
    values.update(changes)
    return Grant(**values)


class AuthorizationTests(unittest.TestCase):
    def decide(self, item, **changes):
        args = dict(owner_id="owner-1", subject_id="agent-1",
                    resource="profile:summary", purpose="answer_question",
                    now=NOW)
        args.update(changes)
        return evaluate(grant=item, **args)

    def test_exact_active_grant_allows(self):
        self.assertTrue(self.decide(grant()).allowed)

    def test_missing_grant_denies(self):
        self.assertEqual(evaluate(grant=None, owner_id="owner-1",
                         subject_id="agent-1", resource="r", purpose="p",
                         now=NOW).reason, "no_matching_grant")

    def test_wrong_owner_denies(self):
        self.assertEqual(self.decide(grant(), owner_id="intruder").reason, "owner_mismatch")

    def test_wrong_subject_denies(self):
        self.assertEqual(self.decide(grant(), subject_id="other-agent").reason, "subject_mismatch")

    def test_wrong_resource_denies(self):
        self.assertEqual(self.decide(grant(), resource="private:all").reason, "resource_mismatch")

    def test_wrong_purpose_denies(self):
        self.assertEqual(self.decide(grant(), purpose="train_model").reason, "purpose_mismatch")

    def test_revoked_grant_denies(self):
        item = grant(revoked_at=NOW - timedelta(seconds=1))
        self.assertEqual(self.decide(item).reason, "revoked")

    def test_expired_grant_denies_at_boundary(self):
        item = grant(expires_at=NOW)
        self.assertEqual(self.decide(item).reason, "expired")

    def test_naive_timestamp_denies(self):
        item = grant(expires_at=datetime(2026, 11, 23))
        self.assertEqual(self.decide(item).reason, "invalid_timestamp")

    def test_incomplete_grant_denies(self):
        self.assertEqual(self.decide(grant(purpose="")).reason, "incomplete_grant")


if __name__ == "__main__":
    unittest.main()
