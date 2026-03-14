import os
from src.domain.interfaces import BaseDataLoader
from src.infrastructure.loaders.csv_loader import CSVDataLoader
from src.infrastructure.loaders.json_loader import JSONDataLoader

class DataLoaderFactory:
    @staticmethod
    def get_loader(file_path: str) -> BaseDataLoader:
        _, ext = os.path.splitext(file_path)
        if ext.lower() == '.csv':
            return CSVDataLoader()
        elif ext.lower() == '.json':
            return JSONDataLoader()
        else:
            raise ValueError(f"Unsupported file format: {ext}")
