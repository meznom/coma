import datetime

def current_date_as_string():
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'
