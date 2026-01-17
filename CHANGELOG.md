# Changelog

All notable changes to DNS-Gather will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-01-16

### Added
- **Dual-Server Support**: Separate DNS servers for zone discovery and zone transfers
  - New `zone_discovery_server` configuration option
  - Allows using primary DNS for zone enumeration and secondary DNS for transfers
  - Automatic fallback to single server if not configured
  - Independent connection testing for both servers
- **Automatic Zone Discovery**: Windows dnscmd integration for zone enumeration
  - No PowerShell dependency required
  - Command: `dnscmd <server_ip> /EnumZones`
  - Automatic parsing of zone names and types
  - Skips special system zones (TrustAnchors, ..cache, ..roothints)
  - 30-second timeout prevents hanging
  - Graceful error handling (returns empty list on failure)
- **Updated Specification**: Complete spec documentation for new features
  - Updated requirements document with dual-server criteria
  - Updated design document with dnscmd implementation details
  - Updated tasks document with completed implementation
  - Added SPEC_UPDATES.md documenting all changes

### Changed
- **Configuration Defaults**: Updated for production use
  - `server_address`: Changed to `192.168.168.55` (zone transfer server)
  - `zone_discovery_server`: Added with default `10.9.1.81` (zone discovery server)
  - `output_directory`: Changed from `./output` to `./Reports`
  - `log_directory`: Changed from `./logs` to `./Logs`
- **Zone Discovery**: Completely rewritten for automatic enumeration
  - Removed manual zone input requirement
  - Implemented dnscmd command execution
  - Added zone list parsing logic
  - Improved error resilience

### Performance
- **Zone Discovery**: 1,885 zones discovered in ~1 second (tested on 10.9.1.81)
- **Zone Transfer**: 99.8% success rate (1,881 of 1,885 zones transferred)
- **Dual-Server**: Eliminates REFUSED errors by using secondary server for transfers

### Technical Details
- **Version:** 0.1.0 (MINOR increment for new features)
- **Build Date:** 2026-01-16
- **Platform:** Windows (dnscmd requirement)
- **DNS Server:** Windows DNS Server (for zone discovery)

### Documentation
- Added DNSCMD_IMPLEMENTATION.md explaining dnscmd usage
- Added SPEC_UPDATES.md documenting specification changes
- Updated README.md with dual-server configuration examples

### Testing
- All 109 tests passing
- Tested with production DNS servers (10.9.1.81 and 192.168.168.55)
- Verified dual-server workflow
- Confirmed dnscmd zone discovery functionality

## [0.0.1] - 2026-01-16

### Added
- Initial release of DNS-Gather
- DNS server connection with TCP/UDP support
- TSIG authentication support for secure zone transfers
- Automatic DNS zone discovery
- AXFR zone transfer functionality
- Excel workbook export with formatted sheets
- Zone List summary sheet with all zones
- Individual sheets for each zone with DNS records
- Support for all standard DNS record types (A, AAAA, CNAME, MX, NS, SOA, TXT, PTR, SRV, etc.)
- Timestamped output files (YYYYMMDD-HH-MM format)
- ASCII-only logging for Windows compatibility
- Comprehensive error handling and reporting
- Configuration file support (DNS-Gather.ini)
- Configurable DNS server settings
- Configurable output directories
- Configurable Excel formatting
- Configurable logging levels
- Progress indicators for long operations
- Summary display after completion
- Build scripts for creating Windows executable
- Distribution packaging scripts
- Comprehensive test suite (109+ tests)
- Property-based testing for correctness validation
- Unit testing for component validation

### Features
- **DNS Operations**
  - Connect to any DNS server
  - Test connection before operations
  - Configurable timeout and port
  - TCP/UDP protocol support
  - TSIG authentication for secure transfers

- **Zone Discovery**
  - Automatic zone enumeration
  - Zone metadata collection
  - Error resilience for failed discoveries
  - Support for multiple zone types

- **Zone Transfer**
  - AXFR zone transfer support
  - All DNS record type parsing
  - Graceful handling of transfer denials
  - Error reporting for failed transfers

- **Excel Export**
  - Formatted workbooks with headers
  - Auto-adjusted column widths
  - Sheet name sanitization
  - Timestamped filenames
  - Zone summary sheet
  - Individual zone sheets

- **Logging**
  - ASCII-compatible log files
  - Timestamped log filenames
  - Configurable log levels
  - Operation tracking
  - Error logging

- **Configuration**
  - INI file configuration
  - Default configuration creation
  - Configuration validation
  - Commented options for guidance

### Technical Details
- **Language:** Python 3.11+
- **Platform:** Windows
- **Dependencies:** dnspython, openpyxl, pytest, hypothesis
- **Build Tool:** PyInstaller
- **Testing:** pytest with hypothesis for property-based testing
- **Author:** Mark Oldham

### Known Issues
- Excel file locking on Windows may cause test teardown errors (tests pass, cleanup fails)
- Property-based tests for Excel export may timeout on slower systems

### Future Enhancements
- Support for incremental zone transfers (IXFR)
- Multiple DNS server support
- Zone comparison functionality
- Additional export formats (CSV, JSON)
- GUI interface option
- Scheduled/automated runs
- Email notifications
- Zone change detection

---

## Version Format

This project uses the following version format: `MAJOR.MINOR.PATCH[LETTER]`

- **MAJOR:** Incompatible API changes or major new features
- **MINOR:** New features in a backwards compatible manner
- **PATCH:** Backwards compatible bug fixes
- **LETTER:** Automatic builds during development (a, b, c, etc.)

### Build Types
- **Automatic builds:** Add/increment letter suffix (e.g., 0.0.1a, 0.0.1b)
- **User builds:** Remove letter and increment PATCH (e.g., 0.0.1b → 0.0.2)

---

[0.1.0]: https://github.com/MarkTegna/DNS-Gather/releases/tag/v0.1.0
[0.0.1]: https://github.com/MarkTegna/DNS-Gather/releases/tag/v0.0.1
