from abc import ABC, abstractmethod

class BaseDatabase(ABC):

    @abstractmethod
    def start_up(self):
        """Initialize the database connection"""

    @abstractmethod
    def teardown(self):
        """Close the database connection"""

    @abstractmethod
    def get_session(self):
        """Get a database session."""   