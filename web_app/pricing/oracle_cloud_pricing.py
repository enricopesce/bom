"""
Oracle Cloud Infrastructure Pricing Calculator

Concrete implementation of CloudPricingCalculator for Oracle Cloud
"""

import json
from typing import List, Dict, Any, Optional
from pathlib import Path

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from processors.base_processor import CloudPricingCalculator
from models.vm_models import VMSpec, OSType


class OracleCloudPricingCalculator(CloudPricingCalculator):
    """
    Oracle Cloud Infrastructure pricing calculator
    """
    
    def __init__(self, pricing_config_file: str = "pricing.json"):
        """
        Initialize with pricing configuration
        
        Args:
            pricing_config_file: Path to pricing configuration JSON file
        """
        pricing_config = self._load_pricing_config(pricing_config_file)
        super().__init__(pricing_config)
        
        # Cache commonly used values
        self.hours_per_month = self.pricing_config.get("pricing_metadata", {}).get("hours_per_month", 744)
        self._currency = self.pricing_config.get("pricing_metadata", {}).get("currency", "EUR")
    
    @property
    def provider_name(self) -> str:
        return "Oracle Cloud Infrastructure"
    
    @property
    def currency(self) -> str:
        return self._currency
    
    def _load_pricing_config(self, config_file: str) -> Dict[str, Any]:
        """Load pricing configuration from JSON file"""
        try:
            config_path = Path(config_file)
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    print(f"Loaded pricing configuration from: {config_file}")
                    return config
            else:
                print(f"Pricing config file not found: {config_file}, using defaults")
        except Exception as e:
            print(f"Error loading pricing config: {e}, using defaults")
        
        return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Fallback default pricing configuration"""
        return {
            "pricing_metadata": {
                "currency": "EUR",
                "hours_per_month": 744,
                "pricing_source": "Oracle Cloud Infrastructure Price List",
                "region": "Global"
            },
            "compute_pricing": {
                "ocpu": {"unit_price": 0.0279, "unit": "OCPU/hour"}
            },
            "memory_pricing": {
                "memory_gb": {"unit_price": 0.00186, "unit": "GB/hour"}
            },
            "storage_pricing": {
                "block_volume": {"unit_price": 0.023715, "unit": "GB/month"},
                "block_volume_vpu": {"unit_price": 0.001581, "unit": "VPU/month"}
            },
            "licensing_pricing": {
                "windows_server": {"unit_price": 0.08556, "unit": "OCPU/hour"}
            }
        }
    
    def calculate_vm_cost(self, vm: VMSpec) -> List[Dict[str, Any]]:
        """
        Calculate cost breakdown for a single VM
        
        Args:
            vm: VM specification
            
        Returns:
            List of cost line items
        """
        cost_items = []
        
        if not vm.is_powered_on:
            return cost_items
        
        ocpu_count = self._calculate_ocpu_count(vm.cpu_cores)
        
        # 1. Compute (OCPU)
        if ocpu_count > 0:
            ocpu_hourly = self.pricing_config["compute_pricing"]["ocpu"]["unit_price"]
            ocpu_monthly = ocpu_hourly * self.hours_per_month
            
            cost_items.append({
                "component_type": "Compute",
                "description": f"OCPU ({ocpu_count} OCPU for {vm.cpu_cores} vCPU)",
                "quantity": float(ocpu_count),
                "unit": "OCPU",
                "unit_price": ocpu_monthly,
                "total_cost": ocpu_count * ocpu_monthly,
                "pricing_model": "on-demand"
            })
        
        # 2. Memory
        if vm.memory_gb > 0:
            memory_hourly = self.pricing_config["memory_pricing"]["memory_gb"]["unit_price"]
            memory_monthly = memory_hourly * self.hours_per_month
            
            cost_items.append({
                "component_type": "Memory",
                "description": f"Memory ({vm.memory_gb:.1f} GB)",
                "quantity": vm.memory_gb,
                "unit": "GB",
                "unit_price": memory_monthly,
                "total_cost": vm.memory_gb * memory_monthly,
                "pricing_model": "on-demand"
            })
        
        # 3. Storage
        total_storage_gb = vm.total_storage_gb
        if total_storage_gb > 0:
            # Block Volume Storage
            storage_monthly = self.pricing_config["storage_pricing"]["block_volume"]["unit_price"]
            
            cost_items.append({
                "component_type": "Storage",
                "description": f"Block Volume Storage ({total_storage_gb:.1f} GB)",
                "quantity": total_storage_gb,
                "unit": "GB",
                "unit_price": storage_monthly,
                "total_cost": total_storage_gb * storage_monthly,
                "pricing_model": "on-demand"
            })
            
            # Block Volume VPUs (10 VPUs per GB)
            vpu_count = total_storage_gb * 10
            vpu_monthly = self.pricing_config["storage_pricing"]["block_volume_vpu"]["unit_price"]
            
            cost_items.append({
                "component_type": "Storage Performance",
                "description": f"Block Volume VPUs ({vpu_count:.1f} VPUs)",
                "quantity": vpu_count,
                "unit": "VPU",
                "unit_price": vpu_monthly,
                "total_cost": vpu_count * vpu_monthly,
                "pricing_model": "on-demand"
            })
        
        # 4. Windows Licensing
        if vm.os_type == OSType.WINDOWS and ocpu_count > 0:
            windows_hourly = self.pricing_config["licensing_pricing"]["windows_server"]["unit_price"]
            windows_monthly = windows_hourly * self.hours_per_month
            
            cost_items.append({
                "component_type": "OS License",
                "description": f"Windows Server License ({ocpu_count} OCPU)",
                "quantity": float(ocpu_count),
                "unit": "OCPU",
                "unit_price": windows_monthly,
                "total_cost": ocpu_count * windows_monthly,
                "pricing_model": "on-demand"
            })
        
        return cost_items
    
    def _calculate_ocpu_count(self, cpu_cores: int) -> int:
        """
        Calculate OCPU count from vCPU cores
        
        Oracle Cloud: 1 OCPU = 2 vCPUs, minimum 1 OCPU
        """
        if cpu_cores <= 0:
            return 0
        if cpu_cores == 1:
            return 1
        return (cpu_cores + 1) // 2  # Round up
    
    def get_pricing_summary(self) -> Dict[str, Any]:
        """Get summary of current pricing configuration"""
        return {
            "provider": self.provider_name,
            "currency": self.currency,
            "hours_per_month": self.hours_per_month,
            "compute_hourly": self.pricing_config["compute_pricing"]["ocpu"]["unit_price"],
            "memory_hourly": self.pricing_config["memory_pricing"]["memory_gb"]["unit_price"],
            "storage_monthly": self.pricing_config["storage_pricing"]["block_volume"]["unit_price"],
            "vpu_monthly": self.pricing_config["storage_pricing"]["block_volume_vpu"]["unit_price"],
            "windows_license_hourly": self.pricing_config["licensing_pricing"]["windows_server"]["unit_price"]
        }