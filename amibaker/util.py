import datetime

class EpochDateTime(datetime.datetime):
    """
    Very simple class to override the datetime.datetime's __str__ function
    so that it returns the epoch time instead of the default
    """
    
    def __init__(self, *args, **kwargs):
        self.epoch_dt = datetime.datetime(1970,1,1)
        super(EpochDateTime, self).__init__(*args, **kwargs)

    def __str__(self):
        return '{0:.0f}'.format((self - self.epoch_dt).total_seconds())
