from pysession.session_impl.default_session_manager import DefaultSessionManager

session_id = 'pywce'

session_manager = DefaultSessionManager()

session = session_manager.session(session_id)

session.save(session_id, 'age', '21')

print('Saved session data: ', session.get(session_id, 'age'))