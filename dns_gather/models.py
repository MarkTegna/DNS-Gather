"""Data models for DNS-Gather"""

from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class ZoneInfo:
    """Information about a DNS zone"""
    name: str
    zone_type: str  # "Primary", "Secondary", "Stub", "Unknown"
    serial: int
    transfer_status: str  # "Success", "Denied", "Failed", "Pending"
    record_count: int
    error_message: str
    
    def to_dict(self) -> dict:
        """Convert to dictionary for Excel export"""
        return {
            'Zone Name': self.name,
            'Zone Type': self.zone_type,
            'Record Count': self.record_count,
            'Transfer Status': self.transfer_status,
            'Error Message': self.error_message
        }


@dataclass
class DNSRecord:
    """A DNS record from a zone"""
    name: str
    record_type: str  # A, AAAA, CNAME, MX, NS, SOA, TXT, PTR, SRV, etc.
    ttl: int
    data: str
    
    def to_dict(self) -> dict:
        """Convert to dictionary for Excel export"""
        return {
            'Record Name': self.name,
            'Record Type': self.record_type,
            'TTL': self.ttl,
            'Data': self.data
        }


@dataclass
class ApplicationState:
    """Application execution state and statistics"""
    zones_discovered: int
    zones_transferred: int
    zones_failed: int
    total_records: int
    errors: List[str]
    start_time: datetime
    end_time: datetime
    
    def get_summary(self) -> dict:
        """Generate summary statistics"""
        duration = (self.end_time - self.start_time).total_seconds()
        return {
            'zones_discovered': self.zones_discovered,
            'zones_transferred': self.zones_transferred,
            'zones_failed': self.zones_failed,
            'total_records': self.total_records,
            'duration_seconds': duration,
            'error_count': len(self.errors)
        }
