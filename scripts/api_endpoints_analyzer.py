#!/usr/bin/env python3
"""
API Endpoints Analyzer

This script analyzes all the extracted API documentation files to provide
a comprehensive overview of all available endpoints across all sports APIs.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Set

class APIEndpointsAnalyzer:
    """Analyzes API endpoints from extracted documentation files."""
    
    def __init__(self):
        self.current_dir = Path(__file__).parent
        self.extracted_dir = self.current_dir / "extracted_pdfs"
        self.results = {}
        
    def extract_endpoints_from_file(self, file_path: Path) -> Dict:
        """Extract endpoints from a single API documentation file."""
        api_name = file_path.stem.replace("API_Sports___Documentation_", "").replace("API_", "").replace("___", " ")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract base URL
        base_url_match = re.search(r'https://[^/\s]+\.api-sports\.io', content)
        base_url = base_url_match.group(0) if base_url_match else "Unknown"
        
        # Extract endpoints using regex patterns
        endpoints = []
        
        # Pattern 1: GET/endpoint_name
        get_pattern = r'GET/([a-zA-Z0-9/_-]+)'
        get_matches = re.findall(get_pattern, content)
        
        # Pattern 2: "get": "endpoint_name"
        quote_pattern = r'"get":\s*"([^"]+)"'
        quote_matches = re.findall(quote_pattern, content)
        
        # Pattern 3: get"endpoint_name"
        direct_pattern = r'get"([^"]+)"'
        direct_matches = re.findall(direct_pattern, content)
        
        # Combine all matches
        all_endpoints = set()
        for match in get_matches + quote_matches + direct_matches:
            if match and not match.startswith('http'):
                all_endpoints.add(match)
        
        # Extract parameters for each endpoint
        endpoint_details = {}
        for endpoint in sorted(all_endpoints):
            # Look for parameter descriptions near the endpoint
            endpoint_section = self.extract_endpoint_section(content, endpoint)
            parameters = self.extract_parameters(endpoint_section)
            endpoint_details[endpoint] = {
                'parameters': parameters,
                'description': self.extract_description(endpoint_section)
            }
        
        return {
            'api_name': api_name,
            'base_url': base_url,
            'endpoints': endpoint_details,
            'total_endpoints': len(endpoint_details)
        }
    
    def extract_endpoint_section(self, content: str, endpoint: str) -> str:
        """Extract the section of content related to a specific endpoint."""
        # Look for the endpoint in the content
        patterns = [
            rf'GET/{re.escape(endpoint)}',
            rf'"get":\s*"{re.escape(endpoint)}"',
            rf'get"{re.escape(endpoint)}"',
            rf'{re.escape(endpoint)}\s*\n'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                start = max(0, match.start() - 500)
                end = min(len(content), match.end() + 1000)
                return content[start:end]
        
        return ""
    
    def extract_parameters(self, section: str) -> List[str]:
        """Extract parameters from an endpoint section."""
        parameters = []
        
        # Look for parameter patterns
        param_patterns = [
            r'QUERY PARAMETERS\s*\n(.*?)(?=\n[A-Z]|\n\n|$)',
            r'Parameters:\s*\n(.*?)(?=\n[A-Z]|\n\n|$)',
            r'HEADER PARAMETERS\s*\n(.*?)(?=\n[A-Z]|\n\n|$)'
        ]
        
        for pattern in param_patterns:
            matches = re.findall(pattern, section, re.DOTALL | re.IGNORECASE)
            for match in matches:
                # Extract individual parameter names
                param_names = re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*\n', match)
                parameters.extend(param_names)
        
        return list(set(parameters))
    
    def extract_description(self, section: str) -> str:
        """Extract description from an endpoint section."""
        # Look for description patterns
        desc_patterns = [
            r'([A-Z][^.]*\.)',
            r'Get ([^.]*\.)',
            r'Returns ([^.]*\.)'
        ]
        
        for pattern in desc_patterns:
            match = re.search(pattern, section)
            if match:
                return match.group(1).strip()
        
        return "No description available"
    
    def analyze_all_apis(self) -> Dict:
        """Analyze all API documentation files."""
        txt_files = list(self.extracted_dir.glob("*.txt"))
        
        for file_path in txt_files:
            if file_path.name != "extraction_summary.md":
                try:
                    api_data = self.extract_endpoints_from_file(file_path)
                    self.results[api_data['api_name']] = api_data
                    print(f"✅ Analyzed: {api_data['api_name']} ({api_data['total_endpoints']} endpoints)")
                except Exception as e:
                    print(f"❌ Error analyzing {file_path.name}: {e}")
        
        return self.results
    
    def generate_summary_report(self) -> str:
        """Generate a comprehensive summary report."""
        report = []
        report.append("# 🏆 Complete API Endpoints Analysis Report")
        report.append("=" * 60)
        report.append(f"📊 Total APIs Analyzed: {len(self.results)}")
        report.append(f"📈 Total Endpoints Found: {sum(api['total_endpoints'] for api in self.results.values())}")
        report.append("")
        
        # Overall statistics
        all_endpoints = set()
        all_parameters = set()
        
        for api_name, api_data in self.results.items():
            for endpoint in api_data['endpoints']:
                all_endpoints.add(endpoint)
                for param in api_data['endpoints'][endpoint]['parameters']:
                    all_parameters.add(param)
        
        report.append("## 📈 Overall Statistics")
        report.append(f"- **Unique Endpoints**: {len(all_endpoints)}")
        report.append(f"- **Unique Parameters**: {len(all_parameters)}")
        report.append("")
        
        # API-specific reports
        for api_name, api_data in sorted(self.results.items()):
            report.append(f"## 🏈 {api_name.upper()} API")
            report.append(f"**Base URL**: `{api_data['base_url']}`")
            report.append(f"**Total Endpoints**: {api_data['total_endpoints']}")
            report.append("")
            
            # Group endpoints by category
            categories = self.categorize_endpoints(api_data['endpoints'])
            
            for category, endpoints in categories.items():
                report.append(f"### {category}")
                for endpoint in sorted(endpoints):
                    params = api_data['endpoints'][endpoint]['parameters']
                    desc = api_data['endpoints'][endpoint]['description']
                    report.append(f"- **`{endpoint}`**")
                    if params:
                        report.append(f"  - Parameters: {', '.join(params)}")
                    if desc and desc != "No description available":
                        report.append(f"  - Description: {desc}")
                    report.append("")
        
        # Common endpoints across APIs
        report.append("## 🔄 Common Endpoints Across APIs")
        common_endpoints = self.find_common_endpoints()
        for endpoint, apis in common_endpoints.items():
            report.append(f"- **`{endpoint}`**: {', '.join(apis)}")
        report.append("")
        
        # Parameter analysis
        report.append("## 📋 Parameter Analysis")
        param_usage = self.analyze_parameter_usage()
        for param, count in sorted(param_usage.items(), key=lambda x: x[1], reverse=True)[:20]:
            report.append(f"- **`{param}`**: Used in {count} endpoints")
        report.append("")
        
        return "\n".join(report)
    
    def categorize_endpoints(self, endpoints: Dict) -> Dict[str, List[str]]:
        """Categorize endpoints by their function."""
        categories = {
            'Core Data': [],
            'Teams': [],
            'Players': [],
            'Fixtures/Matches': [],
            'Statistics': [],
            'Leagues/Competitions': [],
            'Utility': []
        }
        
        for endpoint in endpoints:
            if any(word in endpoint.lower() for word in ['team', 'teams']):
                categories['Teams'].append(endpoint)
            elif any(word in endpoint.lower() for word in ['player', 'players']):
                categories['Players'].append(endpoint)
            elif any(word in endpoint.lower() for word in ['fixture', 'match', 'game', 'fight']):
                categories['Fixtures/Matches'].append(endpoint)
            elif any(word in endpoint.lower() for word in ['stat', 'statistic']):
                categories['Statistics'].append(endpoint)
            elif any(word in endpoint.lower() for word in ['league', 'competition', 'season']):
                categories['Leagues/Competitions'].append(endpoint)
            elif any(word in endpoint.lower() for word in ['timezone', 'country', 'search']):
                categories['Utility'].append(endpoint)
            else:
                categories['Core Data'].append(endpoint)
        
        # Remove empty categories
        return {k: v for k, v in categories.items() if v}
    
    def find_common_endpoints(self) -> Dict[str, List[str]]:
        """Find endpoints that are common across multiple APIs."""
        endpoint_apis = {}
        
        for api_name, api_data in self.results.items():
            for endpoint in api_data['endpoints']:
                if endpoint not in endpoint_apis:
                    endpoint_apis[endpoint] = []
                endpoint_apis[endpoint].append(api_name)
        
        # Return only endpoints used in multiple APIs
        return {endpoint: apis for endpoint, apis in endpoint_apis.items() if len(apis) > 1}
    
    def analyze_parameter_usage(self) -> Dict[str, int]:
        """Analyze how frequently parameters are used across endpoints."""
        param_usage = {}
        
        for api_data in self.results.values():
            for endpoint_data in api_data['endpoints'].values():
                for param in endpoint_data['parameters']:
                    param_usage[param] = param_usage.get(param, 0) + 1
        
        return param_usage
    
    def save_report(self, report: str, filename: str = "api_endpoints_analysis.md"):
        """Save the analysis report to a file."""
        output_file = self.current_dir / filename
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        return output_file

def main():
    """Main function to run the API endpoints analysis."""
    print("🔍 Starting API Endpoints Analysis...")
    print("=" * 50)
    
    analyzer = APIEndpointsAnalyzer()
    
    # Analyze all APIs
    results = analyzer.analyze_all_apis()
    
    print(f"\n📊 Analysis Complete!")
    print(f"📈 Total APIs: {len(results)}")
    print(f"🎯 Total Endpoints: {sum(api['total_endpoints'] for api in results.values())}")
    
    # Generate and save report
    report = analyzer.generate_summary_report()
    output_file = analyzer.save_report(report)
    
    print(f"\n📄 Report saved to: {output_file}")
    print("\n🎯 Key Findings:")
    
    # Show top APIs by endpoint count
    sorted_apis = sorted(results.items(), key=lambda x: x[1]['total_endpoints'], reverse=True)
    print(f"🏆 Most Comprehensive API: {sorted_apis[0][0]} ({sorted_apis[0][1]['total_endpoints']} endpoints)")
    
    # Show common endpoints
    common_endpoints = analyzer.find_common_endpoints()
    if common_endpoints:
        most_common = max(common_endpoints.items(), key=lambda x: len(x[1]))
        print(f"🔄 Most Common Endpoint: '{most_common[0]}' (used in {len(most_common[1])} APIs)")

if __name__ == "__main__":
    main() 