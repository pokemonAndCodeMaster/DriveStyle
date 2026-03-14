from abc import ABC, abstractmethod
from typing import Any, List
from src.domain.models import CarFollowingSegment

class BaseDataLoader(ABC):
    @abstractmethod
    def load_data(self, source: str) -> List[CarFollowingSegment]:
        """Load data from a source and return a list of CarFollowingSegment objects."""
        pass

class BaseIdentifier(ABC):
    @abstractmethod
    def identify(self, segment: CarFollowingSegment) -> Any:
        """Perform identification on a segment."""
        pass

class BaseVisualizer(ABC):
    @abstractmethod
    def plot_results(self, data: Any, output_path: str):
        """Visualize identification results."""
        pass
