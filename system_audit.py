#!/usr/bin/env python3
"""
System Audit Runner
Executes comprehensive data integrity check and generates optimization report
"""
from data_integrity_service import data_integrity_service
import json

def main():
    print("Starting comprehensive system audit...")
    
    # Perform full audit
    results = data_integrity_service.perform_full_system_audit()
    
    # Generate detailed report
    report = data_integrity_service.generate_optimization_report()
    
    # Save results to file
    with open('audit_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    with open('optimization_report.md', 'w') as f:
        f.write(report)
    
    print("Audit complete. Results saved to audit_results.json and optimization_report.md")
    print("\n" + "="*50)
    print(report)

if __name__ == "__main__":
    main()