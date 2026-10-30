class TrackerException(Exception):
    """Base class"""
class InvalidProductUrlException(TrackerException):
    """The given link is not valid"""
class PageFetchException(TrackerException):
    def __init__(self, url, reason):
        self.url = url
        self.reason = reason
        super().__init__(f"Could not download {url}: {reason}")

class DatabaseConnectionException(TrackerException):
    """Could not connect to SQL Server"""
class NotificationException(TrackerException):
    """Sending email failed"""