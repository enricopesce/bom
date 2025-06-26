"""
Processor Factory for creating appropriate VM assessment processors based on input type.
"""

import os
from typing import Dict, Type
from .base_processor import VMAssessmentProcessor
from .rvtools_processor import RVToolsProcessor


class ProcessorFactory:
    """Factory class for creating VM assessment processors based on input type."""
    
    def __init__(self):
        self._processors: Dict[str, Type[VMAssessmentProcessor]] = {
            'rvtools': RVToolsProcessor
        }
    
    def register_processor(self, name: str, processor_class: Type[VMAssessmentProcessor]):
        """Register a new processor type."""
        self._processors[name] = processor_class
    
    def create_processor(self, input_path: str) -> VMAssessmentProcessor:
        """
        Create appropriate processor based on input file type.
        
        Args:
            input_path: Path to the input file
            
        Returns:
            VMAssessmentProcessor instance
            
        Raises:
            ValueError: If input type is not supported
        """
        # Determine processor type based on file extension and content
        if input_path.lower().endswith('.zip'):
            # For now, assume ZIP files are RVTools exports
            return self._processors['rvtools'](input_path)
        
        # Future: Add support for other formats
        # elif input_path.lower().endswith('.json'):
        #     return self._processors['aws'](input_path)
        # elif input_path.lower().endswith('.xml'):
        #     return self._processors['vmware'](input_path)
        
        raise ValueError(f"Unsupported input file format: {input_path}")
    
    def get_supported_formats(self) -> Dict[str, str]:
        """Get supported input formats and their descriptions."""
        formats = {
            'rvtools': 'RVTools ZIP export files containing VM inventory data'
        }
        # Future formats can be added here
        return formats