'''
authors:
Elise Vidal - evidal@artfx.fr
Angele Sionneau - asionneau@artfx.fr
'''

from datetime import datetime, timedelta

def get_date_as_datetime_obj(date_string):
        '''
        Converts a string object representing a date, like this %d/%m/%y to a datetime object

        :param date_string: string
        returns: datetime
        '''
        datetime_obj = datetime.strptime(date_string, '%d/%m/%y')
        return datetime_obj

def get_time_as_datetime_obj(time_string):
    '''
    Converts a string object representing a date, like this '%H:%M:%S' or this to a datetime object
    
    :param time_string: string
    returns: datetime
    '''
    return datetime.strptime(time_string,'%H:%M:%S')

def get_date_as_string(datetime_obj):
    '''
    Converts datetime object to string format %d/%m/%y.

    :param datetime_obj: datetime
    Returns: string
    '''
    date_string = datetime_obj.strftime('%d/%m/%y')
    return date_string

def get_date_delta(newest_date, oldest_date):
    """
        Returns a timedelta object of two giving dates.
        Checks and converts if necessarey to datetime format before
        calculating delta

        :param newest_date: str or datetime
        :param oldest_date: str or datetime
        returns: timedelta
    """
    try:
        return newest_date - oldest_date
    except TypeError:
        try:
            newest_date = get_time_as_datetime_obj(newest_date)
        except TypeError:
            pass
        try:
            oldest_date = get_time_as_datetime_obj(oldest_date)
        except TypeError:
            pass

        delta = timedelta(hours=newest_date.hour, minutes=newest_date.minute, seconds=newest_date.second) - timedelta(hours=oldest_date.hour, minutes=oldest_date.minute, seconds=oldest_date.second)
        return  delta

def get_week_definition():
    '''
    Get the week definition of the current week
    format monday %d/%m/%y - wednesday %d/%m/%y

    :return: string
    '''
    today = datetime.now()
    day_of_week = today.weekday()

    to_beginning_of_week = timedelta(days=day_of_week)
    monday = today - to_beginning_of_week

    to_end_of_week = timedelta(days=4 - day_of_week)
    wednesday = today + to_end_of_week

    mon = get_date_as_string(monday)
    wed = get_date_as_string(wednesday)

    return f"{mon} - {wed}"
