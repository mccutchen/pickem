import datetime

def close(d):
    delta = d - datetime.datetime.now()
    hours = delta.seconds / (60 * 60)
    return delta.days == 0 and 0 < hours <= 12
