"""
Azure Resource Setup Script for AI Travel Concierge Agent

This script sets up Azure resources programmatically where possible.
Some resources require portal creation - instructions provided.

Run this script to configure your environment.

USAGE:
    python app/scripts/setup_azure.py

DELETE THIS SCRIPT after successful setup and integration.
"""

import os
import sys
import subprocess
import json

# Configuration
SUBSCRIPTION_ID = "05e7b074-305c-48d8-9bd0-ce5305cd027c"
RESOURCE_GROUP = "rg-udacity-project-agentic-ai"
LOCATION = "eastus"

# Resource names
AOAI_RESOURCE = "udacity-agentic-ai-eastus-resour"
COSMOS_ACCOUNT = "udacity-travel-cosmos"
COSMOS_DB = "ragdb"
COSMOS_CONTAINER = "snippets"


def run_az_command(cmd: str, capture_output: bool = True) -> dict:
    """Run an Azure CLI command and return the result."""
    try:
        result = subprocess.run(
            f"az {cmd}",
            shell=True,
            capture_output=capture_output,
            text=True
        )
        if result.returncode != 0:
            return {"success": False, "error": result.stderr}
        if capture_output and result.stdout:
            try:
                return {"success": True, "data": json.loads(result.stdout)}
            except json.JSONDecodeError:
                return {"success": True, "data": result.stdout.strip()}
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def check_azure_login():
    """Verify Azure CLI is logged in."""
    print("Checking Azure CLI login...")
    result = run_az_command('account show --query "{name:name, id:id}" -o json')
    if result["success"]:
        print(f"  Logged in to: {result['data']['name']}")
        return True
    print("  ERROR: Not logged in. Run 'az login' first.")
    return False


def get_aoai_details():
    """Get Azure OpenAI endpoint and key."""
    print("\nGetting Azure OpenAI details...")
    
    # Get endpoint
    endpoint_result = run_az_command(
        f'cognitiveservices account show --name {AOAI_RESOURCE} '
        f'--resource-group {RESOURCE_GROUP} --query "properties.endpoint" -o tsv'
    )
    
    # Get key
    key_result = run_az_command(
        f'cognitiveservices account keys list --name {AOAI_RESOURCE} '
        f'--resource-group {RESOURCE_GROUP} --query "key1" -o tsv'
    )
    
    if endpoint_result["success"] and key_result["success"]:
        print(f"  Endpoint: {endpoint_result['data']}")
        print(f"  Key: {key_result['data'][:20]}...")
        return {
            "endpoint": endpoint_result["data"],
            "key": key_result["data"]
        }
    
    print("  ERROR: Could not retrieve Azure OpenAI details")
    return None


def get_cosmos_details():
    """Get Cosmos DB endpoint and key."""
    print("\nGetting Cosmos DB details...")
    
    # Get endpoint
    endpoint_result = run_az_command(
        f'cosmosdb show --name {COSMOS_ACCOUNT} '
        f'--resource-group {RESOURCE_GROUP} --query "documentEndpoint" -o tsv'
    )
    
    # Get key
    key_result = run_az_command(
        f'cosmosdb keys list --name {COSMOS_ACCOUNT} '
        f'--resource-group {RESOURCE_GROUP} --query "primaryMasterKey" -o tsv'
    )
    
    if endpoint_result["success"] and key_result["success"]:
        print(f"  Endpoint: {endpoint_result['data']}")
        print(f"  Key: {key_result['data'][:20]}...")
        return {
            "endpoint": endpoint_result["data"],
            "key": key_result["data"]
        }
    
    print("  ERROR: Could not retrieve Cosmos DB details")
    return None


def list_aoai_deployments():
    """List Azure OpenAI deployments."""
    print("\nListing Azure OpenAI deployments...")
    result = run_az_command(
        f'cognitiveservices account deployment list --name {AOAI_RESOURCE} '
        f'--resource-group {RESOURCE_GROUP} '
        f'--query "[].{{name:name, model:properties.model.name}}" -o json'
    )
    
    if result["success"]:
        for deployment in result["data"]:
            print(f"  - {deployment['name']}: {deployment['model']}")
        return result["data"]
    return []


def generate_env_file(aoai: dict, cosmos: dict):
    """Generate .env file content."""
    print("\n" + "="*60)
    print("GENERATED .env FILE CONTENT")
    print("="*60)
    
    env_content = f"""# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT={aoai['endpoint']}
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4.1-mini
AZURE_OPENAI_EMBED_DEPLOYMENT=text-embedding-3-small
AZURE_OPENAI_KEY={aoai['key']}

# Cosmos DB Configuration
COSMOS_ENDPOINT={cosmos['endpoint']}
COSMOS_KEY={cosmos['key']}
COSMOS_DB={COSMOS_DB}
COSMOS_CONTAINER={COSMOS_CONTAINER}
COSMOS_PARTITION_KEY=/pk

# Azure AI Foundry Agent Configuration (MANUAL SETUP REQUIRED)
# See instructions below to get these values from Azure AI Foundry portal
PROJECT_ENDPOINT=
AGENT_ID=
BING_CONNECTION_ID=

# Optional: Direct Bing Search API (fallback)
BING_KEY=

# Python path
PYTHONPATH=.
"""
    print(env_content)
    return env_content


def print_manual_setup_instructions():
    """Print instructions for manual Azure portal setup."""
    print("\n" + "="*60)
    print("MANUAL SETUP REQUIRED - Azure AI Foundry Portal")
    print("="*60)
    print("""
The following steps must be done in the Azure AI Foundry portal:

1. CREATE FOUNDRY PROJECT
   - Go to: https://ai.azure.com
   - Click "Create an agent" on the home page
   - Enter project name: "udacity-travel-agent"
   - Select your subscription and resource group: rg-udacity-project-agentic-ai
   - Click "Create"
   
   SCREENSHOT: Take a screenshot of the created project overview page

2. CREATE GROUNDING WITH BING SEARCH RESOURCE
   - Go to: https://portal.azure.com/#create/Microsoft.BingGroundingSearch
   - Subscription: Your subscription
   - Resource group: rg-udacity-project-agentic-ai
   - Name: udacity-travel-bing-grounding
   - Region: Global
   - Pricing tier: Select available tier
   - Click "Review + create" then "Create"
   
   SCREENSHOT: Take a screenshot of the Bing Grounding resource overview

3. CONNECT BING GROUNDING TO YOUR AGENT
   - In AI Foundry portal, go to your agent
   - In the Setup pane, scroll to "Knowledge"
   - Click "Add" and select "Grounding with Bing Search"
   - Select your Bing Grounding resource and add connection
   
   SCREENSHOT: Take a screenshot showing Bing Grounding connected

4. GET CONNECTION DETAILS
   After setup, retrieve:
   - PROJECT_ENDPOINT: From project overview in AI Foundry portal
   - AGENT_ID: From the agent details page
   - BING_CONNECTION_ID: Format is:
     /subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.CognitiveServices/accounts/{account}/projects/{project}/connections/{connection}

5. UPDATE YOUR .env FILE
   Add the values from step 4 to your .env file

6. OPTIONAL: File Search for RAG
   - In AI Foundry portal, you can also add File Search tool
   - Upload your knowledge base documents
   - This provides built-in RAG functionality
   
   SCREENSHOT: Take a screenshot if you configure File Search
""")


def main():
    print("="*60)
    print("Azure Resource Setup for AI Travel Concierge Agent")
    print("="*60)
    
    # Check login
    if not check_azure_login():
        sys.exit(1)
    
    # Get resource details
    aoai = get_aoai_details()
    cosmos = get_cosmos_details()
    
    if not aoai or not cosmos:
        print("\nERROR: Could not retrieve all resource details")
        sys.exit(1)
    
    # List deployments
    list_aoai_deployments()
    
    # Generate .env content
    env_content = generate_env_file(aoai, cosmos)
    
    # Save to .env file
    env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
    env_path = os.path.abspath(env_path)
    
    print(f"\nSaving to: {env_path}")
    with open(env_path, "w") as f:
        f.write(env_content)
    print("  .env file saved successfully!")
    
    # Print manual instructions
    print_manual_setup_instructions()
    
    print("\n" + "="*60)
    print("NEXT STEPS")
    print("="*60)
    print("""
1. Complete the manual setup steps in Azure portal
2. Update .env with PROJECT_ENDPOINT, AGENT_ID, BING_CONNECTION_ID
3. Run: python chat.py
4. Take required screenshots for Udacity submission
""")


if __name__ == "__main__":
    main()
