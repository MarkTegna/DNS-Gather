"""Zone discovery for DNS-Gather"""

import subprocess
import re
import dns.resolver
import dns.zone
import dns.query
from typing import List
from dns_gather.models import ZoneInfo
from dns_gather.dns_manager import DNSManager


class ZoneDiscovery:
    """Discovers DNS zones on a server"""
    
    def __init__(self, dns_manager: DNSManager):
        """
        Initialize Zone Discovery
        
        Args:
            dns_manager: DNSManager instance for DNS operations
        """
        self.dns_manager = dns_manager
    
    def enumerate_zones(self) -> List[ZoneInfo]:
        """
        Enumerate all zones available on the DNS server using dnscmd
        
        Returns:
            List of ZoneInfo objects
        """
        zones = []
        
        try:
            # Use dnscmd to enumerate zones on Windows DNS server
            cmd = ['dnscmd', self.dns_manager.server, '/EnumZones']
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                # dnscmd failed - return empty list
                return zones
            
            # Parse dnscmd output
            # Format: " zone_name    zone_type    properties..."
            lines = result.stdout.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Skip header lines and command output
                if line.startswith('Enumerated') or line.startswith('Command completed'):
                    continue
                
                # Parse zone line - format: " zone_name    Primary/Secondary/etc    ..."
                parts = line.split()
                if len(parts) >= 2:
                    zone_name = parts[0]
                    zone_type = parts[1]
                    
                    # Skip special zones
                    if zone_name in ['TrustAnchors', '..cache', '..roothints']:
                        continue
                    
                    # Create ZoneInfo object
                    zone_info = ZoneInfo(
                        name=zone_name,
                        zone_type=zone_type,
                        serial=0,
                        transfer_status='Pending',
                        record_count=0,
                        error_message=''
                    )
                    zones.append(zone_info)
            
        except subprocess.TimeoutExpired:
            # Timeout - return empty list
            pass
        except FileNotFoundError:
            # dnscmd not found - not a Windows DNS server or not in PATH
            pass
        except Exception:
            # Other error - return empty list
            pass
        
        return zones
    
    def get_zone_metadata(self, zone_name: str) -> ZoneInfo:
        """
        Get metadata for a specific zone
        
        Args:
            zone_name: Name of the zone
        
        Returns:
            ZoneInfo object with metadata
        """
        zone_info = ZoneInfo(
            name=zone_name,
            zone_type='Unknown',
            serial=0,
            transfer_status='Pending',
            record_count=0,
            error_message=''
        )
        
        try:
            # Try to get SOA record to determine zone type and serial
            response = self.dns_manager.query(zone_name, 'SOA', 'IN')
            
            if response and len(response.answer) > 0:
                for rrset in response.answer:
                    if rrset.rdtype == dns.rdatatype.SOA:
                        soa = rrset[0]
                        zone_info.serial = soa.serial
                        zone_info.zone_type = 'Primary'  # Assume primary if we can query SOA
                        break
            
        except Exception as e:
            zone_info.error_message = f"Failed to get metadata: {str(e)}"
        
        return zone_info
    
    def discover_zones_from_list(self, zone_names: List[str]) -> List[ZoneInfo]:
        """
        Discover zones from a provided list of zone names
        
        Args:
            zone_names: List of zone names to discover
        
        Returns:
            List of ZoneInfo objects
        """
        zones = []
        
        for zone_name in zone_names:
            try:
                zone_info = self.get_zone_metadata(zone_name)
                zones.append(zone_info)
            except Exception as e:
                # Create zone info with error
                zone_info = ZoneInfo(
                    name=zone_name,
                    zone_type='Unknown',
                    serial=0,
                    transfer_status='Failed',
                    record_count=0,
                    error_message=f"Discovery failed: {str(e)}"
                )
                zones.append(zone_info)
        
        return zones
