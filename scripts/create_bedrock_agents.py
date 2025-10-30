#!/usr/bin/env python3
import boto3
import json
import time
import sys

bedrock_agent = boto3.client('bedrock-agent', region_name='us-east-1')

ROLE_ARN = "arn:aws:iam::211125632542:role/DevAgentBedrockAgentRole"

# Agent definitions
agents = [
    {
        'name': 'DevAgent-CodeReview',
        'description': 'Specialized agent for security and code quality review',
        'instruction': """You are a senior security engineer performing code reviews.

Your job: Identify security vulnerabilities and code quality issues.

For EACH issue found, provide:
1. Severity (CRITICAL, HIGH, MEDIUM, LOW)
2. Type (sql_injection, hardcoded_secret, etc)
3. Line number if visible
4. What's wrong
5. How to fix it

Return ONLY JSON format:
{
  "issues": [
    {
      "severity": "CRITICAL",
      "type": "sql_injection",
      "line": 47,
      "message": "SQL injection vulnerability",
      "description": "User input directly in SQL query",
      "suggestion": "Use parameterized queries"
    }
  ],
  "summary": "Found N critical issues"
}"""
    },
    {
        'name': 'DevAgent-Testing',
        'description': 'Specialized agent for automated test generation',
        'instruction': """You are a test automation expert for Python/pytest.

Your job: Generate comprehensive unit tests for code.

Provide:
1. Test cases for happy path
2. Edge cases and boundaries
3. Error scenarios
4. Mocks for dependencies

Return ONLY JSON:
{
  "test_cases": [
    {
      "name": "test_authenticate_valid_credentials",
      "description": "Test with valid credentials",
      "code": "def test_...(): ..."
    }
  ],
  "estimated_coverage": 0.95,
  "summary": "Generated N test cases"
}"""
    },
    {
        'name': 'DevAgent-Documentation',
        'description': 'Specialized agent for documentation generation',
        'instruction': """You are a technical writer for API documentation.

Your job: Generate OpenAPI specs and README sections.

Provide:
1. OpenAPI 3.0 endpoint definitions
2. Request/response examples
3. README sections

Return ONLY JSON:
{
  "openapi": {...},
  "readme_sections": {...},
  "summary": "Generated documentation"
}"""
    },
    {
        'name': 'DevAgent-Supervisor',
        'description': 'Supervisor agent coordinating all specialist agents',
        'instruction': """You are the supervisor coordinator for code analysis.

Your job: Receive code and coordinate specialist agents.

Workflow:
1. Use Code Review Agent for security & quality
2. Use Testing Agent for tests
3. Use Documentation Agent for docs
4. Consolidate results

Return consolidated JSON:
{
  "code_review": {...},
  "testing": {...},
  "documentation": {...},
  "summary": "Complete analysis"
}"""
    }
]

def create_agents():
    """Create all Bedrock agents"""
    
    created_agents = {}
    
    for agent_def in agents:
        print(f"\n📋 Creating agent: {agent_def['name']}...")
        
        try:
            response = bedrock_agent.create_agent(
                agentName=agent_def['name'],
                description=agent_def['description'],
                foundationModel='amazon.nova-pro-v1:0',
                instruction=agent_def['instruction'],
                agentResourceRoleArn=ROLE_ARN,
                idleSessionTTLInSeconds=600
            )
            
            agent_id = response['agent']['agentId']
            created_agents[agent_def['name']] = agent_id
            
            print(f"✅ Created: {agent_id}")
        
        except Exception as e:
            print(f"❌ Failed: {str(e)}")
            return None
    
    return created_agents

def prepare_agents(agent_ids):
    """Prepare agents for use"""
    
    print("\n⏳ Preparing agents...")
    
    for name, agent_id in agent_ids.items():
        print(f"Preparing: {name}...")
        
        try:
            bedrock_agent.prepare_agent(agentId=agent_id)
            print(f"✅ Prepared: {agent_id}")
            time.sleep(2)
        
        except Exception as e:
            print(f"⚠️ Warning: {str(e)}")

def create_aliases(agent_ids):
    """Create aliases for agents"""
    
    print("\n🔗 Creating aliases...")
    
    aliases = {}
    
    for name, agent_id in agent_ids.items():
        print(f"Creating alias for: {name}...")
        
        try:
            response = bedrock_agent.create_agent_alias(
                agentId=agent_id,
                agentAliasName='production'
            )
            
            alias_id = response['agentAlias']['agentAliasId']
            aliases[name] = alias_id
            
            print(f"✅ Alias: {alias_id}")
        
        except Exception as e:
            print(f"⚠️ Warning: {str(e)}")
    
    return aliases

def save_config(agent_ids, aliases):
    """Save configuration to .env"""
    
    print("\n💾 Saving configuration to .env...")
    
    config = f"""
# ===== Bedrock Agents with Amazon Nova =====

# Supervisor Agent (Orchestrator)
BEDROCK_SUPERVISOR_AGENT_ID={agent_ids.get('DevAgent-Supervisor', '')}
BEDROCK_SUPERVISOR_ALIAS_ID={aliases.get('DevAgent-Supervisor', 'TSTALIASID')}

# Code Review Agent
BEDROCK_CODE_REVIEW_AGENT_ID={agent_ids.get('DevAgent-CodeReview', '')}
BEDROCK_CODE_REVIEW_ALIAS_ID={aliases.get('DevAgent-CodeReview', 'TSTALIASID')}

# Testing Agent
BEDROCK_TESTING_AGENT_ID={agent_ids.get('DevAgent-Testing', '')}
BEDROCK_TESTING_ALIAS_ID={aliases.get('DevAgent-Testing', 'TSTALIASID')}

# Documentation Agent
BEDROCK_DOCS_AGENT_ID={agent_ids.get('DevAgent-Documentation', '')}
BEDROCK_DOCS_ALIAS_ID={aliases.get('DevAgent-Documentation', 'TSTALIASID')}
"""
    
    with open('.env', 'a') as f:
        f.write(config)
    
    print("✅ Configuration saved to .env")

def main():
    """Main function"""
    
    print("🤖 Creating Bedrock Agents with Amazon Nova...\n")
    
    # Step 1: Create agents
    agent_ids = create_agents()
    
    if not agent_ids:
        print("\n❌ Failed to create agents!")
        sys.exit(1)
    
    print(f"\n✅ Created {len(agent_ids)} agents:")
    for name, agent_id in agent_ids.items():
        print(f"   {name}: {agent_id}")
    
    # Step 2: Prepare agents
    prepare_agents(agent_ids)
    
    # Step 3: Create aliases
    aliases = create_aliases(agent_ids)
    
    print(f"\n✅ Created {len(aliases)} aliases")
    
    # Step 4: Save configuration
    save_config(agent_ids, aliases)
    
    print("\n" + "="*60)
    print("🎉 All agents created and configured!")
    print("="*60)
    
    print("\n📋 Agent IDs:")
    for name, agent_id in agent_ids.items():
        print(f"   {name}: {agent_id}")
    
    print("\n🔗 Aliases:")
    for name, alias_id in aliases.items():
        print(f"   {name}: {alias_id}")
    
    print("\n📝 Next step: Run 'source .env' to load configuration")
    print("✅ Then test: python -m app.agents.multi_agent_orchestrator")

if __name__ == "__main__":
    main()
