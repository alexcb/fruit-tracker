import hashlib
import random
import string


def auth_user(cursor, email, password):
    cursor.execute('SELECT id, salt, password FROM mad.users where email = %s', (email,))

    row = cursor.fetchone()
    if row is None:
        return 0, False

    user_id, salt, stored_hashed_password = row

    hashed_password = hashlib.sha512((password + salt).encode('utf8')).hexdigest()

    if hashed_password != stored_hashed_password:
        return 0, False

    return user_id, True


def create_new_session(cursor, user_id):
    sid = ''.join(random.choice(string.ascii_lowercase) for i in range(250))
    cursor.execute('INSERT INTO mad.sessions (sid, user_id) VALUES (%s, %s) ON CONFLICT (user_id) DO UPDATE SET sid = excluded.sid', (sid, user_id))

    return sid


def validate_sid(cursor, sid):
    cursor.execute('SELECT u.email, u.admin FROM mad.sessions s LEFT JOIN mad.users u ON (s.user_id = u.id) WHERE s.sid = %s AND u.active = true', (sid,))
    row = cursor.fetchone()
    if row is None:
        return None, False

    email, admin = row

    return email, admin

