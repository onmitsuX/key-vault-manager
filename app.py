import json
import subprocess
import argparse
import click
import fnmatch
import os

def azure_login_check():
    """Check if the user is logged in to Azure, and use az login if not."""
    try:
        result = subprocess.run(["az", "account", "show"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        click.echo("You are not logged in to Azure. Initiating 'az login'...")
        try:
            subprocess.run(["az", "login"], check=True)
            click.echo("Login successful!")
        except subprocess.CalledProcessError:
            click.echo("Error: Azure login failed. Please try logging in manually.")
            exit(1)

def switch_subscription(subscription_id=None):
    """Switch to the specified subscription using the given ID."""
    if subscription_id:
        click.echo(f"Switching to subscription: {subscription_id}")
        try:
            result = subprocess.run(
                ['az', 'account', 'set', '--subscription', subscription_id],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            click.echo("Subscription switched successfully.")
        except subprocess.CalledProcessError as e:
            click.echo(f"Error switching to subscription {subscription_id}.")
            click.echo(e.stderr.decode())  # Print the detailed error message from stderr
            exit(1)


def push_secrets(vaultname, filename):
    """Push secrets to Azure Key Vault."""
    click.echo(f"Pushing secrets to vault: {vaultname}")

    with open(filename, 'r') as f:
        secrets = json.load(f)

    for secret in secrets:
        if not isinstance(secret, dict) or "name" not in secret or "value" not in secret:
            click.echo("Error: Each secret must have 'name' and 'value' fields.")
            exit(1)

        tags = secret.get("tags", {})
        name = secret["name"]
        value = secret["value"]

        tag_args = [f"{key}={value}" for key, value in tags.items()]

        result = subprocess.run(
            ['az', 'keyvault', 'secret', 'set', '--vault-name', vaultname, '--name', name, '--value', value, '--tags'] + tag_args,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        if result.returncode != 0:
            click.echo(f"Error pushing secret {name}")
            exit(1)
        else:
            click.echo(f"Secret {name} pushed successfully")

def pull_secrets(vaultname, tags, filename, secret_name_pattern=None, verbose=False):
    """Pull secrets from Azure Key Vault with optional filtering by name pattern and tags."""
    click.echo(f"Pulling secrets from vault: {vaultname}")

    if tags:
        tags_qry = " && ".join([f"tags.{key} == '{value}'" for key, value in tags.items()])
        cmd = ['az', 'keyvault', 'secret', 'list', '--vault-name', vaultname, '--query', f"[?{tags_qry}].id", '-o', 'json']
    else:
        cmd = ['az', 'keyvault', 'secret', 'list', '--vault-name', vaultname, '--query', "[].id", '-o', 'json']

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if result.returncode != 0:
        click.echo("Error fetching secrets")
        click.echo(result.stderr.decode())
        exit(1)

    secrets_ids = json.loads(result.stdout)
    secrets = []

    for secret_id in secrets_ids:
        result = subprocess.run(
            ['az', 'keyvault', 'secret', 'show', '--id', secret_id, '--query', '{name: name, value: value, tags: tags}', '-o', 'json'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        if result.returncode == 0:
            secret = json.loads(result.stdout)

            if secret_name_pattern:
                if fnmatch.fnmatch(secret['name'], secret_name_pattern):
                    secrets.append(secret)
                    if verbose:
                        click.echo(f"Secret pulled: {secret}")
                    else:
                        click.echo(f"Secret {secret['name']} pulled successfully (value hidden)")
            else:
                secrets.append(secret)
                if verbose:
                    click.echo(f"Secret pulled: {secret}")
                else:
                    click.echo(f"Secret {secret['name']} pulled successfully (value hidden)")
        else:
            click.echo(f"Error pulling secret {secret_id}")

    with open(filename, 'w') as f:
        json.dump(secrets, f, indent=4)

    click.echo(f"Secrets saved to {filename}")

def confirm_action(action, vaultname):
    """Custom confirmation prompt showing 'y/n' and handling both cases."""
    response = input(f"Are you sure you want to {action} secrets in the vault '{vaultname}'? [y/n]: ").strip().lower()
    return response == 'y'

def main():
    parser = argparse.ArgumentParser(description="Azure Key Vault Secrets Manager")
    parser.add_argument('--direction', type=str, required=True, choices=['push', 'pull'], help='Push or Pull secrets to/from Azure Key Vault')
    parser.add_argument('--vaultname', type=str, help='Name or wildcard pattern of the Key Vault')
    parser.add_argument('--filename', type=str, required=True, help='Filename for secrets (JSON format)')
    parser.add_argument('--tags', nargs='+', type=str, help='Tags to filter secrets when pulling (key=value format)')
    parser.add_argument('--name', type=str, help='Name or name pattern of the secret to pull')
    parser.add_argument('--verbose', action='store_true', help='Show secrets in terminal when pulling')
    parser.add_argument('--subscription', type=str, help='Azure Subscription ID')

    args = parser.parse_args()

    subscription_id = args.subscription or os.getenv('AZURE_SUBSCRIPTION_ID')
    vaultname = args.vaultname or os.getenv('AZURE_KEYVAULT_NAME')

    if not subscription_id:
        click.echo("Error: No subscription ID provided. Set the AZURE_SUBSCRIPTION_ID environment variable or use the --subscription flag.")
        exit(1)

    if not vaultname:
        click.echo("Error: No vault name provided. Set the AZURE_KEYVAULT_NAME environment variable or use the --vaultname flag.")
        exit(1)

    azure_login_check()
    switch_subscription(subscription_id)

    # Custom confirmation prompt
    action = "push" if args.direction == 'push' else "pull"
    if not confirm_action(action, vaultname):
        click.echo("Operation cancelled.")
        exit(0)

    if args.direction == 'push':
        push_secrets(vaultname, args.filename)
    elif args.direction == 'pull':
        tag_dict = dict(tag.split('=') for tag in args.tags) if args.tags else {}
        pull_secrets(vaultname, tag_dict, args.filename, args.name, args.verbose)

if __name__ == '__main__':
    main()
