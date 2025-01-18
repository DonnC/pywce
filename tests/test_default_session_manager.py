import unittest

from pywce import DictSessionManager


class TestSessionManager(unittest.TestCase):
    def setUp(self):
        # TODO: setup your session manager implementation
        session_manager = DictSessionManager()

        self.session_id = "pywce"
        self.session_key = "foo"
        self.session_data = "bar"

        self.session = session_manager.session(session_id=self.session_id)

    def test_save(self):
        self.session.save(self.session_id, self.session_key, self.session_data)

        self.assertEqual(
            self.session.get(session_id=self.session_id, key=self.session_key),
            self.session_data,
            "Saved session doesn't match expected data"
        )

    def test_prop(self):
        self.session.save_prop(
            session_id=self.session_id,
            prop_key=self.session_key,
            data=self.session_data
        )

        props = self.session.get_user_props(session_id=self.session_id)

        self.assertDictEqual(
            props,
            {self.session_key: self.session_data},
            "Saved session props doesn't match expected data"
        )

        self.assertEqual(
            self.session.get_from_props(session_id=self.session_id, prop_key=self.session_key),
            self.session_data,
            "Saved session user prop doesn't match expected data"
        )

    def test_evict(self):
        self.session.save(
            session_id=self.session_id,
            key="k1",
            data="data1"
        )

        self.assertIn(
            "k1",
            self.session.fetch_all(session_id=self.session_id)
        )

        self.session.evict(session_id=self.session_id, key="k1")

        self.assertIsNone(
            self.session.get(session_id=self.session_id, key="k1")
        )

    def test_global(self):
        self.assertDictEqual(
            self.session.fetch_all(session_id=self.session_id, is_global=True),
            {},
            "It seems that the global session is not empty"
        )

        self.session.save_global(
            key=self.session_key,
            data=self.session_data
        )

        self.assertIn(
            self.session_key,
            self.session.fetch_all(session_id=self.session_id, is_global=True)
        )

        self.assertEqual(
            self.session.get_global(key=self.session_key),
            self.session_data,
        )

    def test_clear(self):
        self.session.save(self.session_id, self.session_key, self.session_data)

        self.session.save_global(
            key=self.session_key,
            data=self.session_data
        )

        self.assertIsNotNone(
            self.session.fetch_all(session_id=self.session_id)
        )

        self.session.clear(session_id=self.session_id)

        self.assertDictEqual(
            self.session.fetch_all(session_id=self.session_id),
            {}
        )

        self.session.clear_global()

        self.assertDictEqual(
            self.session.fetch_all(session_id=self.session_id, is_global=True),
            {},
            "It seems that the global session is not cleared properly"
        )


if __name__ == '__main__':
    unittest.main()
