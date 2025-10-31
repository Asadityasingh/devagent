# create_memory.py (CORRECT: namespaces as list with one item)
import boto3
import json

# Initialize control client
control_client = boto3.client('bedrock-agentcore-control', region_name='us-east-1')

print("Creating AgentCore Memory for DevAgent Swarm...")

try:
    # Create memory with semantic strategy
    # NOTE: namespaces MUST be a list, but can have ONE item
    memory_response = control_client.create_memory(
        name="DevAgentSwarmMemory",
        description="STM & LTM for PR code reviews (learns security patterns, coding practices)",
        eventExpiryDuration=90,  # 90 days for STM
        memoryStrategies=[
            {
                'semanticMemoryStrategy': {
                    'name': 'SecurityPatternExtractor',
                    'namespaces': ['/security/{actorId}']  # CORRECT: List with ONE namespace
                }
            }
        ]
    )
    
    memory_id = memory_response['memory']['id']
    memory_arn = memory_response['memory']['arn']
    memory_status = memory_response['memory']['status']
    
    print(f"\n✅ Memory Created Successfully!")
    print(f"Memory ID: {memory_id}")
    print(f"Memory ARN: {memory_arn}")
    print(f"Status: {memory_status}")
    print(f"\n📝 Add this to your .env file:")
    print(f"AGENTCORE_MEMORY_ID={memory_id}")
    print(f"\n⏳ Note: Status is '{memory_status}'. If 'CREATING', wait 2-3 minutes for ACTIVE.")
    
except Exception as e:
    print(f"❌ Error creating memory: {e}")
    print(f"\nTroubleshooting:")
    print("1. Verify AWS credentials: aws configure")
    print("2. Check IAM has: bedrock:*, bedrock-agentcore:*")
    print("3. Ensure region: us-east-1")
    print("4. Retry in 30 seconds")
