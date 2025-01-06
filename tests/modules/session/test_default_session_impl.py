import unittest

from modules.session.impl.default_session_manager import DefaultSessionManager


class TestDefaultSessionManager(unittest.TestCase):
    SESSION_ID = "pywce"

    def test_save(self):
        session_key = "foo"
        session_data = "bar"

        session_manager = DefaultSessionManager()
        session = session_manager.session(self.SESSION_ID)

        session.save(self.SESSION_ID, session_key, session_data)

        self.assertEqual(
            session.get(self.SESSION_ID, session_key),
            session_data
        )


if __name__ == '__main__':
    unittest.main()
