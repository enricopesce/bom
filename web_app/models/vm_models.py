"""
Standardized VM Data Models

This module defines the standardized data structures for VM assessment
that can be used across different input formats (RVTools, VMware, AWS, etc.)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime
import uuid


class PowerState(Enum):
    """Standardized VM power states"""
    POWERED_ON = "poweredOn"
    POWERED_OFF = "poweredOff"
    SUSPENDED = "suspended"
    UNKNOWN = "unknown"


class OSType(Enum):
    """Standardized operating system types"""
    WINDOWS = "Windows"
    LINUX = "Linux"
    UNIX = "Unix"
    OTHER = "Other"
    UNKNOWN = "Unknown"


class StorageType(Enum):
    """Storage/disk types"""
    BLOCK = "Block"
    OBJECT = "Object"
    FILE = "File"
    UNKNOWN = "Unknown"


@dataclass
class VMStorage:
    """Standardized VM storage information"""
    capacity_gb: float
    used_gb: Optional[float] = None
    provisioned_gb: Optional[float] = None
    storage_type: StorageType = StorageType.BLOCK
    datastore: Optional[str] = None
    path: Optional[str] = None


@dataclass
class VMNetwork:
    """Standardized VM network interface information"""
    interface_name: Optional[str] = None
    mac_address: Optional[str] = None
    ip_addresses: List[str] = field(default_factory=list)
    network_name: Optional[str] = None
    connected: bool = True


@dataclass
class VMSpec:
    """
    Standardized VM specification that can be populated from any assessment tool
    
    This is the core data model that all input processors should populate
    """
    # Core identification
    vm_id: str  # Unique identifier (UUID, instance ID, etc.)
    vm_name: str
    
    # Compute resources
    cpu_cores: int
    memory_gb: float
    
    # Storage
    storage: List[VMStorage] = field(default_factory=list)
    
    # Operating System
    os_type: OSType = OSType.UNKNOWN
    os_config: Optional[str] = None
    os_version: Optional[str] = None
    
    # Power and state
    power_state: PowerState = PowerState.UNKNOWN
    
    # Network
    networks: List[VMNetwork] = field(default_factory=list)
    
    # Infrastructure context
    cluster: Optional[str] = None
    host: Optional[str] = None
    datacenter: Optional[str] = None
    folder: Optional[str] = None
    
    # Metadata
    annotation: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    creation_date: Optional[datetime] = None
    last_modified: Optional[datetime] = None
    
    # Assessment metadata
    source_format: Optional[str] = None  # e.g., "rvtools", "aws", "vmware"
    assessment_date: Optional[datetime] = None
    
    @property
    def total_storage_gb(self) -> float:
        """Calculate total storage capacity across all disks"""
        return sum(storage.capacity_gb for storage in self.storage)
    
    @property
    def total_used_storage_gb(self) -> float:
        """Calculate total used storage across all disks"""
        return sum(storage.used_gb or 0 for storage in self.storage)
    
    @property
    def is_powered_on(self) -> bool:
        """Check if VM is powered on"""
        return self.power_state == PowerState.POWERED_ON
    
    @property
    def primary_ip(self) -> Optional[str]:
        """Get primary IP address"""
        for network in self.networks:
            if network.ip_addresses:
                return network.ip_addresses[0]
        return None
    
    def add_storage(self, capacity_gb: float, used_gb: Optional[float] = None, 
                   storage_type: StorageType = StorageType.BLOCK, 
                   datastore: Optional[str] = None) -> None:
        """Add storage to the VM"""
        self.storage.append(VMStorage(
            capacity_gb=capacity_gb,
            used_gb=used_gb,
            storage_type=storage_type,
            datastore=datastore
        ))
    
    def add_network(self, interface_name: Optional[str] = None, 
                   mac_address: Optional[str] = None,
                   ip_addresses: Optional[List[str]] = None,
                   network_name: Optional[str] = None) -> None:
        """Add network interface to the VM"""
        self.networks.append(VMNetwork(
            interface_name=interface_name,
            mac_address=mac_address,
            ip_addresses=ip_addresses or [],
            network_name=network_name
        ))
    
    @classmethod
    def create_with_defaults(cls, vm_id: str, vm_name: str, cpu_cores: int, memory_gb: float) -> 'VMSpec':
        """Create a VM spec with minimal required fields"""
        return cls(
            vm_id=vm_id or str(uuid.uuid4()),
            vm_name=vm_name,
            cpu_cores=cpu_cores,
            memory_gb=memory_gb,
            assessment_date=datetime.now()
        )


@dataclass
class BOMLineItem:
    """Standardized Bill of Materials line item"""
    vm_id: str
    vm_name: str
    os_type: OSType
    component_type: str  # e.g., "Compute", "Memory", "Storage", "License"
    description: str
    quantity: float
    unit: str  # e.g., "OCPU", "GB", "Instance"
    unit_price: float
    total_cost: float
    currency: str = "EUR"
    pricing_model: Optional[str] = None  # e.g., "on-demand", "reserved"
    
    @property
    def monthly_cost(self) -> float:
        """Get monthly cost (assuming total_cost is monthly)"""
        return self.total_cost
    
    @property
    def annual_cost(self) -> float:
        """Calculate annual cost"""
        return self.total_cost * 12


@dataclass
class VMAssessment:
    """
    Container for a complete VM assessment with metadata
    """
    vms: List[VMSpec] = field(default_factory=list)
    assessment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    assessment_name: Optional[str] = None
    source_format: Optional[str] = None
    assessment_date: datetime = field(default_factory=datetime.now)
    total_vms: int = 0
    powered_on_vms: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Calculate derived fields after initialization"""
        self.total_vms = len(self.vms)
        self.powered_on_vms = sum(1 for vm in self.vms if vm.is_powered_on)
    
    def add_vm(self, vm: VMSpec) -> None:
        """Add a VM to the assessment"""
        vm.assessment_date = self.assessment_date
        vm.source_format = self.source_format
        self.vms.append(vm)
        self.total_vms = len(self.vms)
        self.powered_on_vms = sum(1 for vm in self.vms if vm.is_powered_on)
    
    def get_powered_on_vms(self) -> List[VMSpec]:
        """Get only powered-on VMs"""
        return [vm for vm in self.vms if vm.is_powered_on]
    
    def get_vms_by_os(self, os_type: OSType) -> List[VMSpec]:
        """Get VMs filtered by OS type"""
        return [vm for vm in self.vms if vm.os_type == os_type]
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get assessment summary statistics"""
        powered_on = self.get_powered_on_vms()
        
        return {
            'total_vms': self.total_vms,
            'powered_on_vms': self.powered_on_vms,
            'powered_off_vms': self.total_vms - self.powered_on_vms,
            'total_cpu_cores': sum(vm.cpu_cores for vm in powered_on),
            'total_memory_gb': sum(vm.memory_gb for vm in powered_on),
            'total_storage_gb': sum(vm.total_storage_gb for vm in powered_on),
            'os_distribution': self._get_os_distribution(),
            'assessment_date': self.assessment_date,
            'source_format': self.source_format
        }
    
    def _get_os_distribution(self) -> Dict[str, int]:
        """Get distribution of VMs by OS type"""
        distribution = {}
        for vm in self.vms:
            os_name = vm.os_type.value
            distribution[os_name] = distribution.get(os_name, 0) + 1
        return distribution


@dataclass
class BillOfMaterials:
    """
    Complete Bill of Materials for an assessment
    """
    assessment_id: str
    line_items: List[BOMLineItem] = field(default_factory=list)
    currency: str = "EUR"
    pricing_date: datetime = field(default_factory=datetime.now)
    pricing_source: Optional[str] = None
    notes: Optional[str] = None
    
    @property
    def total_monthly_cost(self) -> float:
        """Calculate total monthly cost"""
        return sum(item.monthly_cost for item in self.line_items)
    
    @property
    def total_annual_cost(self) -> float:
        """Calculate total annual cost"""
        return sum(item.annual_cost for item in self.line_items)
    
    def get_cost_by_component(self) -> Dict[str, float]:
        """Get cost breakdown by component type"""
        breakdown = {}
        for item in self.line_items:
            component = item.component_type
            breakdown[component] = breakdown.get(component, 0) + item.monthly_cost
        return breakdown
    
    def get_cost_by_os(self) -> Dict[str, float]:
        """Get cost breakdown by OS type"""
        breakdown = {}
        for item in self.line_items:
            os_type = item.os_type.value
            breakdown[os_type] = breakdown.get(os_type, 0) + item.monthly_cost
        return breakdown
    
    def add_line_item(self, item: BOMLineItem) -> None:
        """Add a line item to the BOM"""
        item.currency = self.currency
        self.line_items.append(item)


# Utility functions for data conversion
def detect_os_type(os_string: str) -> OSType:
    """Detect OS type from string description"""
    if not os_string:
        return OSType.UNKNOWN
    
    os_lower = os_string.lower()
    if 'windows' in os_lower or 'microsoft' in os_lower:
        return OSType.WINDOWS
    elif any(unix_like in os_lower for unix_like in ['ubuntu', 'centos', 'oracle linux', 'debian', 'suse', 'linux', 'rhel', 'unix', 'aix', 'solaris', 'bsd']):
        return OSType.LINUX
    else:
        return OSType.OTHER


def detect_power_state(power_string: str) -> PowerState:
    """Detect power state from string description"""
    if not power_string:
        return PowerState.UNKNOWN
    
    power_lower = power_string.lower()
    if 'on' in power_lower or 'running' in power_lower:
        return PowerState.POWERED_ON
    elif 'off' in power_lower or 'stopped' in power_lower:
        return PowerState.POWERED_OFF
    elif 'suspend' in power_lower:
        return PowerState.SUSPENDED
    else:
        return PowerState.UNKNOWN