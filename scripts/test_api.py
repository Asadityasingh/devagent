#!/usr/bin/env python3
# scripts/test_api.py
import httpx
import json
from rich.console import Console
from rich.table import Table

console = Console()

async def test_analyze_code():
    """Test code analysis endpoint"""
    
    # Test code with vulnerabilities
    test_code = """
def authenticate(username, password):
    query = f"SELECT * FROM users WHERE username='{username}'"
    cursor.execute(query)
    return cursor.fetchone()

def get_config():
    api_key = "sk-1234567890abcdef"
    return {"api_key": api_key}
"""
    
    request_data = {
        "language": "python",
        "code": test_code,
        "filename": "auth.py",
        "review_depth": "thorough"
    }
    
    console.print("\n[bold cyan]Testing DevAgent Swarm API[/bold cyan]\n")
    console.print(f"[yellow]Analyzing {len(test_code)} characters of Python code...[/yellow]\n")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/analyze/code",
            json=request_data,
            timeout=30.0
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Display results
            console.print(f"[green]✅ Analysis complete![/green]")
            console.print(f"Request ID: {result['request_id']}")
            console.print(f"Execution time: {result['execution_time_ms']}ms\n")
            
            review = result['results']['code_review']
            console.print(f"[bold]{review['summary']}[/bold]\n")
            
            # Issues table
            if review['issues']:
                table = Table(title="Issues Found")
                table.add_column("Severity", style="bold")
                table.add_column("Type")
                table.add_column("Line")
                table.add_column("Message")
                
                for issue in review['issues']:
                    severity_color = {
                        'CRITICAL': 'red',
                        'HIGH': 'orange1',
                        'MEDIUM': 'yellow',
                        'LOW': 'blue'
                    }.get(issue['severity'], 'white')
                    
                    table.add_row(
                        f"[{severity_color}]{issue['severity']}[/{severity_color}]",
                        issue['type'],
                        str(issue.get('line', 'N/A')),
                        issue['message']
                    )
                
                console.print(table)
            
            # Metrics
            console.print("\n[bold]Metrics:[/bold]")
            for key, value in review['metrics'].items():
                console.print(f"  {key}: {value}")
        else:
            console.print(f"[red]❌ Error: {response.status_code}[/red]")
            console.print(response.text)

if __name__ == "__main__":
    import asyncio
    
    # Install rich: pip install rich httpx
    asyncio.run(test_analyze_code())
