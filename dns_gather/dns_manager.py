"""DNS connection and management for DNS-Gather"""

from typing import Optional, Tuple
import dns.resolver
import dns.query
import dns.tsigkeyring
import dns.message


class DNSManager:
    """Manages DNS connections and operations"""

    def __init__(self, server: str, port: int = 53, timeout: int = 10, use_tcp: bool = True):
        """
        Initialize DNS Manager

        Args:
            server: DNS server address (IP or hostname)
            port: DNS server port
            timeout: Connection timeout in seconds
            use_tcp: Use TCP for queries (required for zone transfers)
        """
        self.server = server
        self.port = port
        self.timeout = timeout
        self.use_tcp = use_tcp
        self.tsig_keyring = None
        self.tsig_keyname = None
        self.connected = False

    def set_tsig_key(self, keyname: str, secret: str,
                     algorithm: str = 'hmac-sha256') -> None:
        """
        Set TSIG authentication key

        Args:
            keyname: TSIG key name
            secret: TSIG key secret (base64 encoded)
            algorithm: TSIG algorithm (default: hmac-sha256)
        """
        # algorithm parameter kept for API compatibility but not used
        # dnspython determines algorithm from keyring
        self.tsig_keyname = keyname
        self.tsig_keyring = dns.tsigkeyring.from_text({
            keyname: secret
        })

    def test_connection(self) -> Tuple[bool, str]:
        """
        Test connection to DNS server

        Returns:
            Tuple of (success, message)
        """
        try:
            # Try a simple query to test connectivity
            query = dns.message.make_query('version.bind', 'TXT', 'CH')

            if self.use_tcp:
                dns.query.tcp(
                    query,
                    self.server,
                    timeout=self.timeout,
                    port=self.port
                )
            else:
                dns.query.udp(
                    query,
                    self.server,
                    timeout=self.timeout,
                    port=self.port
                )

            self.connected = True
            return True, f"Successfully connected to {self.server}:{self.port}"

        except dns.exception.Timeout:
            return False, f"Connection timeout to {self.server}:{self.port}"
        except ConnectionRefusedError:
            return False, f"Connection refused by {self.server}:{self.port}"
        except Exception as exc:
            return False, f"Connection failed: {str(exc)}"

    def connect(self) -> bool:
        """
        Establish connection to DNS server

        Returns:
            True if connection successful
        """
        success, _ = self.test_connection()
        return success

    def query(self, qname: str, rdtype: str = 'A',
              rdclass: str = 'IN') -> Optional[dns.message.Message]:
        """
        Perform a DNS query

        Args:
            qname: Query name
            rdtype: Record type (A, AAAA, NS, etc.)
            rdclass: Record class (IN, CH, etc.)

        Returns:
            DNS response message or None on failure
        """
        try:
            query_msg = dns.message.make_query(qname, rdtype, rdclass)

            if self.tsig_keyring:
                query_msg.use_tsig(self.tsig_keyring, self.tsig_keyname)

            if self.use_tcp:
                response = dns.query.tcp(
                    query_msg,
                    self.server,
                    timeout=self.timeout,
                    port=self.port
                )
            else:
                response = dns.query.udp(
                    query_msg,
                    self.server,
                    timeout=self.timeout,
                    port=self.port
                )

            return response

        except Exception:
            return None
