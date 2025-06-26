"""
Abstract Base Classes for VM Assessment Processors

This module defines the interfaces that all input format processors must implement.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.vm_models import VMAssessment, VMSpec, BillOfMaterials


class VMAssessmentProcessor(ABC):
    """
    Abstract base class for all VM assessment input processors
    
    Each input format (RVTools, VMware, AWS, etc.) should implement this interface
    """
    
    def __init__(self, input_path: str, include_powered_off: bool = False):
        """
        Initialize the processor
        
        Args:
            input_path: Path to the input file/directory
            include_powered_off: Whether to include powered-off VMs
        """
        self.input_path = Path(input_path)
        self.include_powered_off = include_powered_off
        self.logger = logging.getLogger(self.__class__.__name__)
        
        if not self.input_path.exists():
            raise FileNotFoundError(f"Input path does not exist: {input_path}")
    
    @property
    @abstractmethod
    def supported_formats(self) -> List[str]:
        """Return list of supported file formats/extensions"""
        pass
    
    @property
    @abstractmethod
    def processor_name(self) -> str:
        """Return the name of this processor"""
        pass
    
    @abstractmethod
    def validate_input(self) -> bool:
        """
        Validate that the input can be processed by this processor
        
        Returns:
            True if input is valid for this processor
        """
        pass
    
    @abstractmethod
    def extract_vm_data(self) -> VMAssessment:
        """
        Extract VM data from the input and return standardized assessment
        
        Returns:
            VMAssessment object containing all discovered VMs
        """
        pass
    
    def process(self) -> VMAssessment:
        """
        Main processing method that orchestrates the extraction
        
        Returns:
            VMAssessment object with all VMs
        """
        self.logger.info(f"Starting {self.processor_name} processing of: {self.input_path}")
        
        if not self.validate_input():
            raise ValueError(f"Input validation failed for {self.processor_name}")
        
        assessment = self.extract_vm_data()
        
        # Filter powered-off VMs if requested
        if not self.include_powered_off:
            original_count = len(assessment.vms)
            assessment.vms = assessment.get_powered_on_vms()
            filtered_count = len(assessment.vms)
            self.logger.info(f"Filtered {original_count - filtered_count} powered-off VMs")
        
        assessment.source_format = self.processor_name
        
        self.logger.info(f"Processed {len(assessment.vms)} VMs from {self.processor_name}")
        return assessment


class CloudPricingCalculator(ABC):
    """
    Abstract base class for cloud pricing calculators
    
    Different cloud providers (Oracle, AWS, Azure, GCP) should implement this interface
    """
    
    def __init__(self, pricing_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the pricing calculator
        
        Args:
            pricing_config: Optional pricing configuration dictionary
        """
        self.pricing_config = pricing_config or {}
        import logging
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the cloud provider name"""
        pass
    
    @property
    @abstractmethod
    def currency(self) -> str:
        """Return the pricing currency"""
        pass
    
    @abstractmethod
    def calculate_vm_cost(self, vm: VMSpec) -> List[Dict[str, Any]]:
        """
        Calculate cost breakdown for a single VM
        
        Args:
            vm: VM specification
            
        Returns:
            List of cost line items (compute, memory, storage, licenses, etc.)
        """
        pass
    
    def calculate_assessment_cost(self, assessment: VMAssessment) -> BillOfMaterials:
        """
        Calculate total cost for an entire assessment
        
        Args:
            assessment: VM assessment to price
            
        Returns:
            Complete Bill of Materials
        """
        bom = BillOfMaterials(
            assessment_id=assessment.assessment_id,
            currency=self.currency,
            pricing_source=self.provider_name
        )
        
        for vm in assessment.vms:
            if not vm.is_powered_on and not assessment.metadata.get('include_powered_off', False):
                continue
                
            vm_costs = self.calculate_vm_cost(vm)
            
            for cost_item in vm_costs:
                from models.vm_models import BOMLineItem
                line_item = BOMLineItem(
                    vm_id=vm.vm_id,
                    vm_name=vm.vm_name,
                    os_type=vm.os_type,
                    component_type=cost_item['component_type'],
                    description=cost_item['description'],
                    quantity=cost_item['quantity'],
                    unit=cost_item['unit'],
                    unit_price=cost_item['unit_price'],
                    total_cost=cost_item['total_cost'],
                    currency=self.currency,
                    pricing_model=cost_item.get('pricing_model')
                )
                bom.add_line_item(line_item)
        
        self.logger.info(f"Calculated costs for {len(bom.line_items)} line items")
        return bom


class ReportGenerator(ABC):
    """
    Abstract base class for report generators
    
    Different output formats (CSV, Excel, PDF, JSON) should implement this interface
    """
    
    def __init__(self, output_path: Optional[str] = None):
        """
        Initialize the report generator
        
        Args:
            output_path: Optional output path for reports
        """
        self.output_path = Path(output_path) if output_path else None
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @property
    @abstractmethod
    def format_name(self) -> str:
        """Return the report format name"""
        pass
    
    @property
    @abstractmethod
    def file_extension(self) -> str:
        """Return the file extension for this format"""
        pass
    
    @abstractmethod
    def generate_assessment_report(self, assessment: VMAssessment, output_file: str) -> str:
        """
        Generate assessment report
        
        Args:
            assessment: VM assessment data
            output_file: Output file path
            
        Returns:
            Path to generated report file
        """
        pass
    
    @abstractmethod
    def generate_bom_report(self, bom: BillOfMaterials, output_file: str) -> str:
        """
        Generate Bill of Materials report
        
        Args:
            bom: Bill of Materials data
            output_file: Output file path
            
        Returns:
            Path to generated report file
        """
        pass
    
    def generate_combined_report(self, assessment: VMAssessment, bom: BillOfMaterials, 
                               base_filename: str) -> List[str]:
        """
        Generate both assessment and BOM reports
        
        Args:
            assessment: VM assessment data
            bom: Bill of Materials data
            base_filename: Base filename (without extension)
            
        Returns:
            List of generated file paths
        """
        files = []
        
        # Generate assessment report
        assessment_file = f"{base_filename}_assessment.{self.file_extension}"
        files.append(self.generate_assessment_report(assessment, assessment_file))
        
        # Generate BOM report
        bom_file = f"{base_filename}_bom.{self.file_extension}"
        files.append(self.generate_bom_report(bom, bom_file))
        
        return files


class ProcessorFactory:
    """
    Factory class to create appropriate processors based on input type
    """
    
    _processors = {}
    
    @classmethod
    def register_processor(cls, processor_class: type):
        """Register a processor class"""
        processor = processor_class.__name__
        cls._processors[processor] = processor_class
    
    @classmethod
    def get_processor(cls, input_path: str, **kwargs) -> VMAssessmentProcessor:
        """
        Get appropriate processor for the input
        
        Args:
            input_path: Path to input file/directory
            **kwargs: Additional arguments for processor
            
        Returns:
            Appropriate processor instance
        """
        input_file = Path(input_path)
        
        # Try each registered processor
        for processor_name, processor_class in cls._processors.items():
            try:
                processor = processor_class(input_path, **kwargs)
                if processor.validate_input():
                    return processor
            except Exception:
                continue
        
        raise ValueError(f"No suitable processor found for input: {input_path}")
    
    @classmethod
    def list_supported_formats(cls) -> Dict[str, List[str]]:
        """
        List all supported formats by processor
        
        Returns:
            Dictionary mapping processor names to supported formats
        """
        formats = {}
        for processor_name, processor_class in cls._processors.items():
            # Create a temporary instance to get supported formats
            try:
                temp_instance = processor_class.__new__(processor_class)
                formats[processor_name] = temp_instance.supported_formats
            except Exception:
                formats[processor_name] = ["Unknown"]
        
        return formats