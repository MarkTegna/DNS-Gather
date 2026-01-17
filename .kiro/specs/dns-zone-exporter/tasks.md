# Implementation Plan: DNS-Gather

## Overview

This implementation plan breaks down the DNS-Gather application into discrete coding tasks. Each task builds on previous work to create a complete Windows executable that connects to DNS servers, performs zone transfers, and exports data to Excel workbooks.

## Tasks

- [x] 1. Set up project structure and version management
  - Create directory structure (dns_gather/, tests/, build_scripts/)
  - Create version.py with initial version 0.0.1
  - Create requirements.txt with dependencies (dnspython>=2.6.0, openpyxl>=3.1.0, pytest, hypothesis, pytest-mock)
  - Create build scripts (clear_python_cache.ps1, increment_build.py)
  - _Requirements: 8.1, 8.2_

- [ ] 2. Implement data models and configuration management
  - [x] 2.1 Create data models (ZoneInfo, DNSRecord, ApplicationState)
    - Write dataclasses in models.py with to_dict() methods
    - _Requirements: 2.2, 3.2, 4.3, 4.5_

  - [x] 2.2 Write property test for data model serialization
    - **Property: Data model round-trip**
    - *For any* valid data model instance, converting to dict and back should preserve all fields
    - _Requirements: 2.2, 3.2_

  - [x] 2.3 Implement ConfigManager class
    - Write config_manager.py with load_config(), create_default_config(), get(), validate_config()
    - Create default DNS-Gather.ini with all sections and commented options
    - Support dual-server configuration (server_address and zone_discovery_server)
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [x] 2.4 Write property test for configuration handling
    - **Property 14: Configuration File Reading**
    - **Property 15: Invalid Configuration Handling**
    - _Requirements: 5.1, 5.3, 5.4, 5.5, 5.6, 5.7_

  - [x] 2.5 Write unit tests for ConfigManager
    - Test default config creation
    - Test invalid config value handling
    - Test dual-server configuration
    - _Requirements: 5.2, 5.3, 5.4, 5.7_

- [ ] 3. Implement ASCII logging system
  - [x] 3.1 Create ASCIILogger class
    - Write logger.py with ASCII character mapping
    - Implement info(), warning(), error(), debug(), log_operation() methods
    - Create timestamped log files using YYYYMMDD-HH-MM format
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [x] 3.2 Write property test for ASCII compliance
    - **Property 17: ASCII Character Compliance**
    - _Requirements: 6.2, 7.4_

  - [x] 3.3 Write property test for log file creation
    - **Property 18: Timestamped Log File Creation**
    - _Requirements: 6.3_

  - [x] 3.4 Write unit tests for logger
    - Test log file creation with timestamp format
    - Test ASCII character replacement
    - Test error logging
    - _Requirements: 6.1, 6.2, 6.3_

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement DNS connection and authentication
  - [x] 5.1 Create DNSManager class
    - Write dns_manager.py with connect(), set_tsig_key(), test_connection()
    - Implement connection handling with timeout and TCP support
    - _Requirements: 1.3, 1.4, 1.5_

  - [x] 5.2 Write property test for DNS connection
    - **Property 1: DNS Connection Establishment**
    - _Requirements: 1.3, 1.4_

  - [x] 5.3 Write property test for TSIG authentication
    - **Property 2: TSIG Authentication Support**
    - _Requirements: 1.5_

  - [x] 5.4 Write unit tests for DNSManager
    - Test connection to mock DNS server
    - Test connection timeout handling
    - Test TSIG authentication setup
    - _Requirements: 1.3, 1.4, 1.5_

- [ ] 6. Implement zone discovery
  - [x] 6.1 Create ZoneDiscovery class
    - Write zone_discovery.py with enumerate_zones(), get_zone_metadata()
    - Implement automatic zone enumeration using Windows dnscmd command
    - Parse dnscmd /EnumZones output to extract zone names and types
    - Skip special system zones (TrustAnchors, ..cache, ..roothints)
    - Handle zone discovery errors gracefully
    - No PowerShell dependency required
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.7, 2.8_

  - [x] 6.2 Write property test for zone discovery
    - **Property 3: Zone Discovery Completeness**
    - **Property 4: Zone Discovery Error Resilience**
    - _Requirements: 2.1, 2.2, 2.4, 2.5, 2.8_

  - [x] 6.3 Write unit tests for zone discovery
    - Test zone enumeration with mock DNS server
    - Test empty zone list handling
    - Test partial failure handling
    - Test dnscmd command execution and parsing
    - _Requirements: 2.1, 2.3, 2.4, 2.8_

- [ ] 7. Implement zone transfer
  - [x] 7.1 Create ZoneTransfer class
    - Write zone_transfer.py with perform_axfr(), parse_zone_data()
    - Implement AXFR zone transfer using dnspython
    - Parse all DNS record types (A, AAAA, CNAME, MX, NS, SOA, TXT, PTR, SRV)
    - Handle zone transfer denials and errors
    - _Requirements: 3.1, 3.2, 3.3_

  - [x] 7.2 Write property test for zone transfer
    - **Property 5: Zone Transfer Execution**
    - **Property 6: Record Type Collection Completeness**
    - **Property 7: Zone Transfer Error Resilience**
    - _Requirements: 3.1, 3.2, 3.3_

  - [x] 7.3 Write unit tests for zone transfer
    - Test AXFR with mock zone data
    - Test all record type parsing
    - Test zone transfer denial handling
    - _Requirements: 3.1, 3.2, 3.3_

- [x] 8. Checkpoint - Ensure all tests pass
  - All 89 tests passing (32 property tests, 57 unit tests)
  - Tasks 1-7 complete

- [x] 9. Implement Excel export functionality
  - [x] 9.1 Create ExcelExporter class
    - Write excel_exporter.py with create_workbook(), create_zone_list_sheet(), create_zone_sheet()
    - Implement sanitize_sheet_name() for Excel compatibility
    - Implement apply_formatting() for header styling
    - Generate timestamped filenames using YYYYMMDD-HH-MM format
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_

  - [x] 9.2 Write property test for Excel workbook creation
    - **Property 8: Excel Workbook Creation**
    - _Requirements: 4.1_

  - [x] 9.3 Write property test for zone list sheet structure
    - **Property 9: Zone List Sheet Structure**
    - _Requirements: 4.2, 4.3_

  - [x] 9.4 Write property test for zone sheet creation
    - **Property 10: Zone Sheet Creation**
    - **Property 11: Zone Sheet Structure**
    - _Requirements: 4.4, 4.5_

  - [x] 9.5 Write property test for sheet name sanitization
    - **Property 12: Sheet Name Sanitization**
    - _Requirements: 4.6_

  - [x] 9.6 Write property test for timestamped filename
    - **Property 13: Timestamped Filename Format**
    - _Requirements: 4.7_

  - [x] 9.7 Write unit tests for Excel exporter
    - Test workbook creation with sample data
    - Test sheet name sanitization with special characters
    - Test column formatting
    - Test empty zone handling
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_

- [x] 10. Implement main controller and user interface
  - [x] 10.1 Create DNSGatherApp class
    - Write main.py with run(), display_welcome(), display_summary()
    - Implement dual-server support (zone_discovery_server and server_address)
    - Initialize separate DNSManager instances for discovery and transfers
    - Test connections to both servers
    - Coordinate all components (DNS, zone discovery, zone transfer, Excel export)
    - Display progress indicators using ASCII characters
    - _Requirements: 1.1, 1.2, 1.6, 1.7, 1.8, 7.1, 7.3, 7.4_

  - [x] 10.2 Write property test for error logging
    - **Property 16: Error Logging Completeness**
    - **Property 19: User-Friendly Error Messages**
    - _Requirements: 6.1, 6.4, 6.5_

  - [x] 10.3 Write unit tests for main controller
    - Test welcome message display with version and author
    - Test summary display
    - Test dual-server configuration handling
    - Test ASCII character usage in console output
    - _Requirements: 1.6, 1.7, 1.8, 7.1, 7.3, 7.4, 8.6, 8.7_

- [x] 11. Integration and end-to-end testing
  - [x] 11.1 Wire all components together
    - Connect DNSGatherApp with all managers and exporters
    - Implement error handling and recovery
    - Add progress indicators for long operations
    - _Requirements: 1.1, 1.2, 2.5, 3.4, 4.8_

  - [x] 11.2 Write integration tests
    - Test complete workflow with mock DNS server
    - Test error recovery scenarios
    - Test partial success scenarios (some zones fail)
    - _Requirements: 2.4, 3.3_

- [x] 12. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 13. Create build and distribution scripts
  - [x] 13.1 Create PyInstaller build script
    - Write build_executable.py with PyInstaller configuration
    - Include DNS-Gather.ini in distribution
    - Configure for Windows .exe output
    - _Requirements: 8.1, 8.2, 8.4, 8.5_

  - [x] 13.2 Create distribution packaging script
    - Write create_distribution.ps1 to create versioned ZIP file
    - Copy executable and config to dist directory
    - Create Archive directory and copy ZIP
    - _Requirements: 8.3, 8.4_

  - [x] 13.3 Update increment_build.py for version management
    - Implement automatic build versioning (letter suffix)
    - Implement user build versioning (remove letter, increment PATCH)
    - Update version.py with new version
    - _Requirements: 8.6, 8.7_

  - [x] 13.4 Test executable build
    - Build executable and verify it runs without Python
    - Test on clean Windows system
    - Verify all dependencies are included
    - _Requirements: 8.2, 8.5_

- [x] 14. Create documentation
  - [x] 14.1 Write README.md
    - Include usage instructions
    - Include configuration options
    - Include author name "Mark Oldham"
    - Include version information
    - _Requirements: 8.6, 8.7_

  - [x] 14.2 Create CHANGELOG.md
    - Document initial version 0.0.1
    - Include feature list
    - _Requirements: 8.6, 8.7_

- [x] 15. Final checkpoint - Complete testing and validation
  - Run all unit tests
  - Run all property tests
  - Build executable
  - Test executable on Windows
  - Verify all requirements are met
  - All tasks complete!

## Notes

- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Build process follows version management steering rules (automatic builds use letter suffix)
