"""Zone transfer operations for DNS-Gather"""

import dns.zone
import dns.query
import dns.rdatatype
from typing import List, Tuple
from dns_gather.models import DNSRecord
from dns_gather.dns_manager import DNSManager


class ZoneTransfer:
    """Performs DNS zone transfers (AXFR)"""
    
    def __init__(self, dns_manager: DNSManager):
        """
        Initialize Zone Transfer
        
        Args:
            dns_manager: DNSManager instance for DNS operations
        """
        self.dns_manager = dns_manager
    
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
            
            # Parse zone data
            records = self.parse_zone_data(zone)
            
        except dns.exception.FormError as e:
            error_message = f"Zone transfer denied or malformed: {str(e)}"
        except dns.query.TransferError as e:
            error_message = f"Zone transfer error: {str(e)}"
        except dns.exception.Timeout:
            error_message = f"Zone transfer timeout for {zone_name}"
        except Exception as e:
            error_message = f"Zone transfer failed: {str(e)}"
        
        return records, error_message
    
    def parse_zone_data(self, zone: dns.zone.Zone) -> List[DNSRecord]:
        """
        Parse zone data into DNSRecord objects
        
        Args:
            zone: DNS zone object
        
        Returns:
            List of DNSRecord objects
        """
        records = []
        
        for name, node in zone.nodes.items():
            name_str = str(name)
            
            for rdataset in node.rdatasets:
                rtype = dns.rdatatype.to_text(rdataset.rdtype)
                ttl = rdataset.ttl
                
                for rdata in rdataset:
                    # Convert rdata to string
                    data_str = str(rdata)
                    
                    record = DNSRecord(
                        name=name_str,
                        record_type=rtype,
                        ttl=ttl,
                        data=data_str
                    )
                    records.append(record)
        
        return records
