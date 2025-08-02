#!/usr/bin/env python3
"""
Command-line tool to validate company research YAML files.

Usage:
    python utils/validate_research.py <yaml_file>
"""

import sys
import argparse
from pathlib import Path

from company_research_validator import CompanyResearchValidator


def main():
    parser = argparse.ArgumentParser(
        description="Validate company research YAML files against schema"
    )
    parser.add_argument(
        "yaml_file",
        type=Path,
        help="Path to YAML file to validate"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed validation errors"
    )
    
    args = parser.parse_args()
    
    if not args.yaml_file.exists():
        print(f"Error: File '{args.yaml_file}' not found")
        sys.exit(1)
    
    print(f"Validating: {args.yaml_file}")
    print("-" * 50)
    
    is_valid, errors = CompanyResearchValidator.validate_yaml_file(args.yaml_file)
    
    if is_valid:
        print("✓ Valid company research YAML")
        sys.exit(0)
    else:
        print("✗ Invalid company research YAML")
        print()
        if args.verbose or len(errors) <= 5:
            print(CompanyResearchValidator.format_errors(errors))
        else:
            print(CompanyResearchValidator.format_errors(errors[:5]))
            print(f"\n... and {len(errors) - 5} more errors")
            print("\nUse --verbose to see all errors")
        sys.exit(1)


if __name__ == "__main__":
    main()