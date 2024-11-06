Azure Key Vault Secrets Manager

# Python 

This script provides functionality to push or pull secrets to and from Azure Key Vault using the Azure CLI. It supports filtering secrets by tags, wildcard patterns, and managing Azure subscriptions.

Prerequisites

- Azure Subscription
- Azure CLI installed on your machine
- Access to a Key Vault within your Azure subscription
- Python 3.11 or earlier
    
Usage

Pulling Secrets from Azure Key Vault

To pull secrets from a specified Azure Key Vault, use the following command:

    python script.py --direction pull --vaultname 'vaultnamegoeshere' --tags "Environment=='taggoeshere'" --filename "output.json"
    
- --vaultname: Specify the vault name. You can use wildcards (*) for pattern matching.
- --tags: Filter secrets by tags. Multiple tags can be added (e.g., "environment=prod" "team=devops").
- --filename: The file where secrets will be saved in JSON format.
 
Pushing Secrets to Azure Key Vault

To push secrets to a specified Azure Key Vault from a JSON file, use the following command:

    python script.py --direction push --vaultname 'vaultnamegoeshere' --filename "secrets.json"
    
- --vaultname: The name of the Azure Key Vault where secrets will be pushed.
- --filename: The JSON file that contains the secrets.

To switch between Azure subscriptions, you can provide the subscription ID using the --subscription flag or set the environment variable AZURE_SUBSCRIPTION_ID: 

    export AZURE_SUBSCRIPTION_ID="your_subscription_id"
    export AZURE_KEYVAULT_NAME="your-keyvault-name"

You can also specify the subscription directly in the command:

    python script.py --subscription 'your_subscription_id'

Verbose Mode

When pulling secrets, use the --verbose flag to display the secret values in the terminal:

    python script.py --direction pull --vaultname 'vaultnamegoeshere' --filename "output.json" --verbose
    
By default, secrets are hidden during retrieval for security purposes.

Error Handling and Debugging

If the script encounters an issue (e.g., cannot fetch secrets or log in to Azure), it will print an error message. For more details, you can run the script in verbose mode by adding the --verbose flag. Additionally, ensure you have the correct permissions to access the Key Vault and have logged into Azure using the Azure CLI.

Key Features:

- Azure Login Check: Automatically checks and logs in to Azure.
- Subscription Management: Supports switching between Azure subscriptions.
- Push/Pull Secrets: Allows pushing secrets to and pulling secrets from Azure Key Vault.
- Filtering: Secrets can be filtered by tags or name patterns.
- Wildcard Pattern Matching: Use wildcards to match Key Vault names.
- Verbose Mode: Option to display secret values during the pull operation.
