class TrackerException(Exception):
    """Base class"""
class InvalidProductUrlException(TrackerException):
    """The given link is not valid"""
class PageFetchException(TrackerException):
    """Downloading a product page failed"""
class DatabaseConnectionException(TrackerException):
    """Could not connect to SQL Server"""
class NotificationException(TrackerException):
    """Sending email failed"""