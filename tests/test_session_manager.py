import unittest

from pywce import ISessionManager, DefaultSessionManager


class TestSessionManager(unittest.TestCase):
    def setUp(self):
        self.init_session = DefaultSessionManager()
        self.test_session_id = "test_session"
        self.session_manager = self.init_session.session(self.test_session_id)

    def test_prop_key(self):
        self.assertEqual(self.session_manager.prop_key, self.init_session.DEFAULT_PROP_KEY)

    def test_session(self):
        result = self.session_manager.session(self.test_session_id)
        self.assertIsInstance(result, ISessionManager)

    def test_save_and_get(self):
        test_data = "test_value"
        self.session_manager.save(self.test_session_id, "test_key", test_data)
        result = self.session_manager.get(self.test_session_id, "test_key")
        self.assertEqual(result, test_data)

    def test_save_all_and_fetch_all(self):
        test_data = {"key1": "value1", "key2": "value2"}
        self.session_manager.save_all(self.test_session_id, test_data)
        result = self.session_manager.fetch_all(self.test_session_id, False)
        result.pop(self.init_session.DEFAULT_PROP_KEY)
        self.assertEqual(result, test_data)

    def test_save_global_and_get_global(self):
        test_data = "global_value"
        self.session_manager.save_global("global_key", test_data)
        result = self.session_manager.get_global("global_key")
        self.assertEqual(result, test_data)

    def test_save_prop_and_get_from_props(self):
        test_data = "prop_value"
        self.session_manager.save_prop(self.test_session_id, "test_prop", test_data)
        result = self.session_manager.get_from_props(self.test_session_id, "test_prop")
        self.assertEqual(result, test_data)

    def test_get_user_props(self):
        test_data = "prop_value"
        self.session_manager.save_prop(self.test_session_id, "test_prop", test_data)
        result = self.session_manager.get_user_props(self.test_session_id)
        self.assertEqual(result, {"test_prop": test_data})

    def test_evict(self):
        self.session_manager.save(self.test_session_id, "test_key", "test_value")
        self.session_manager.evict(self.test_session_id, "test_key")
        result = self.session_manager.get(self.test_session_id, "test_key")
        self.assertIsNone(result)

    def test_evict_all(self):
        test_data = {"key1": "value1", "key2": "value2"}
        self.session_manager.save_all(self.test_session_id, test_data)
        self.session_manager.evict_all(self.test_session_id, ["key1", "key2"])
        result = self.session_manager.fetch_all(self.test_session_id, False)
        result.pop(self.init_session.DEFAULT_PROP_KEY)
        self.assertEqual(result, {})

    def test_evict_global(self):
        self.session_manager.save_global("global_key", "global_value")
        self.session_manager.evict_global("global_key")
        result = self.session_manager.get_global("global_key")
        self.assertIsNone(result)

    def test_clear(self):
        test_data = {"key1": "value1", "key2": "value2"}
        self.session_manager.save_all(self.test_session_id, test_data)
        self.session_manager.clear(self.test_session_id)
        result = self.session_manager.fetch_all(self.test_session_id, False)
        self.assertEqual(result, {})

    def test_clear_with_retain_keys(self):
        test_data = {"key1": "value1", "key2": "value2"}
        self.session_manager.save_all(self.test_session_id, test_data)
        self.session_manager.clear(self.test_session_id, retain_keys=["key1"])
        result = self.session_manager.fetch_all(self.test_session_id, False)
        result.pop(self.init_session.DEFAULT_PROP_KEY)
        self.assertEqual(result, {"key1": "value1"})

    def test_clear_global(self):
        self.session_manager.save_global("global_key", "global_value")
        self.session_manager.clear_global()
        result = self.session_manager.fetch_all(self.test_session_id, True)
        self.assertEqual(result, {})

    def test_evict_prop(self):
        self.session_manager.save_prop(self.test_session_id, "test_prop", "test_value")
        result = self.session_manager.evict_prop(self.test_session_id, "test_prop")
        self.assertTrue(result)
        self.assertIsNone(self.session_manager.get_from_props(self.test_session_id, "test_prop"))

    def test_key_in_session(self):
        self.session_manager.save(self.test_session_id, "test_key", "test_value")
        self.session_manager.save_global("global_key", "global_value")

        # Test with check_global=True
        self.assertTrue(self.session_manager.key_in_session(self.test_session_id, "test_key", True))
        self.assertTrue(self.session_manager.key_in_session(self.test_session_id, "global_key", True))

        # Test with check_global=False
        self.assertTrue(self.session_manager.key_in_session(self.test_session_id, "test_key", False))
        self.assertFalse(self.session_manager.key_in_session(self.test_session_id, "global_key", False))

if __name__ == '__main__':
    unittest.main()
