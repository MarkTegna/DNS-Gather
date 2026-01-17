"""Zone transfer operations for DNS-Gather"""

import dns.zone
import dns.query
import dns.rdatatype
import dns.resolver
from typing import List, Tuple
from dns_gather.models import DNSRecord
from dns_gather.dns_manager import DNSManager


class ZoneTransfer:
    """Performs DNS zone transfers (AXFR)"""
    
    def __init__(self, dns_manager: DNSManager, logger=None):
        """
        Initialize Zone Transfer
        
        Args:
            dns_manager: DNSManager instance for DNS operations
            logger: Optional logger for validation warnings
        """
        self.dns_manager = dns_manager
        self.logger = logger
        self.validation_warnings = []
    
    def perform_axfr(self, zone_name: str) -> Tuple[List[DNSRecord], str]:
        """
        Perform AXFR zone transfer
        
        Args:
            zone_name: Name of the zone to transfer
        
        Returns:
            Tuple of (list of DNSRecord objects, error message)
        """
        records = []
        error_message = ''
        self.validation_warnings = []  # Reset warnings for each zone
        
        try:
            # Perform zone transfer
            zone = dns.zone.from_xfr(
                dns.query.xfr(
                    self.dns_manager.server,
                    zone_name,
                    timeout=self.dns_manager.timeout,
                    port=self.dns_manager.port,
                    keyring=self.dns_manager.tsig_keyring,
                    keyname=self.dns_manager.tsig_keyname
                )
            )
            
            # Parse zone data with validation
            records = self.parse_zone_data(zone, zone_name)
            
            # Log validation warnings
            if self.validation_warnings and self.logger:
                for warning in self.validation_warnings:
                    self.logger.warning(warning)
            
        except dns.exception.FormError as e:
            error_message = f"Zone transfer denied or malformed: {str(e)}"
        except dns.query.TransferError as e:
            error_message = f"Zone transfer error: {str(e)}"
        except dns.exception.Timeout:
            error_message = f"Zone transfer timeout for {zone_name}"
        except Exception as e:
            error_message = f"Zone transfer failed: {str(e)}"
        
        return records, error_message
    
    def parse_zone_data(self, zone: dns.zone.Zone, zone_name: str) -> List[DNSRecord]:
        """
        Parse zone data into DNSRecord objects with validation
        
        Args:
            zone: DNS zone object
            zone_name: Name of the zone being parsed
        
        Returns:
            List of DNSRecord objects
        """
        records = []
        
        for name, node in zone.nodes.items():
            name_str = str(name)
            
            # Build full FQDN for validation
            if name_str == '@':
                fqdn = zone_name
            elif name_str.endswith('.'):
                fqdn = name_str.rstrip('.')
            else:
                fqdn = f"{name_str}.{zone_name}".rstrip('.')
            
            for rdataset in node.rdatasets:
                rtype = dns.rdatatype.to_text(rdataset.rdtype)
                ttl = rdataset.ttl
                
                for rdata in rdataset:
                    # Convert rdata to string
                    data_str = str(rdata)
                    
                    # Validate hostname matching for relevant record types
                    self._validate_hostname_match(name_str, fqdn, rtype, data_str, zone_name)
                    
                    record = DNSRecord(
                        name=name_str,
                        record_type=rtype,
                        ttl=ttl,
                        data=data_str
                    )
                    records.append(record)
        
        return records
    
    def _validate_hostname_match(self, record_name: str, fqdn: str, record_type: str, 
                                  data: str, zone_name: str) -> None:
        """
        Validate that DNS record names match the actual hostname
        
        Args:
            record_name: The record name (e.g., "www", "@")
            fqdn: The fully qualified domain name
            record_type: The DNS record type (A, AAAA, CNAME, etc.)
            data: The record data
            zone_name: The zone name
        """
        # Only validate record types that should have hostname matching
        if record_type not in ['A', 'AAAA', 'CNAME']:
            return
        
        # Extract hostname from record name (part before first dot)
        if record_name == '@':
            hostname_part = zone_name.split('.')[0]
        elif '.' in record_name:
            hostname_part = record_name.split('.')[0]
        else:
            hostname_part = record_name
        
        # For CNAME records, validate against the target
        if record_type == 'CNAME':
            # Extract target hostname (part before first dot)
            target = data.rstrip('.')
            if '.' in target:
                target_hostname = target.split('.')[0]
            else:
                target_hostname = target
            
            # Check if hostnames match
            if hostname_part.lower() != target_hostname.lower():
                warning = (f"Zone {zone_name}: CNAME mismatch - "
                          f"Record '{record_name}' (hostname: {hostname_part}) "
                          f"points to '{target}' (hostname: {target_hostname})")
                self.validation_warnings.append(warning)
        
        # For A/AAAA records, we can't validate against IP addresses directly,
        # but we can check if the record name looks like it should match a pattern
        # This is a basic check - you may want to customize based on your naming conventions
        elif record_type in ['A', 'AAAA']:
            # Check for common mismatches (e.g., "web" pointing to "app" server)
            # This is a placeholder for more sophisticated validation
            # You can add custom logic here based on your organization's naming conventions
            pass
