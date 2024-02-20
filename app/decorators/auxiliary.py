from botocore.exceptions import ClientError
import ruamel.yaml
import boto3
import json
import time
import os


def get_secret():

    secret_name = "dev-hermesdaily-keys"
    region_name = "us-east-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    secret = get_secret_value_response['SecretString']

    return secret


def create_config_yaml():
    secrets = json.loads(get_secret())
    template_file_path = './data/config_template.yml'
    output_file_path = './data/ngrok_config.yml'

    # Check if YAML file exists
    if os.path.exists(template_file_path):
        # Load default YAML template
        with open(template_file_path, 'r') as template_file:
            yaml = ruamel.yaml.YAML()
            template_content = yaml.load(template_file)
    else:
        print(f"Error: Template file not found at {template_file_path}")
        return

    # Update values
    template_content['authtoken'] = secrets['ngrok_authtoken']
    template_content['tunnels']['similin_tunnel']['hostname'] = secrets['ngrok_hostname']
    template_content['tunnels']['similin_tunnel']['addr'] = secrets['ngrok_addr']

    # Save the modified content
    with open(output_file_path, 'w') as output_file:
        yaml = ruamel.yaml.YAML()
        yaml.dump(template_content, output_file)

    
    os.chmod(output_file_path, 0o755)

    # Set file permissions (e.g., read and write for the owner)
    print(f"Modified YAML saved to {output_file_path}")


def delete_config_yaml():
    file_path = './data/ngrok_config.yml'
    try:
        # Attempt to close the file if it's open
        with open(file_path, 'a'):
            os.utime(file_path, None)

        # Wait for a short duration to ensure the file is closed
        time.sleep(1)

        # Now, attempt to remove the file
        os.remove(file_path)
        print(f"YAML file at {file_path} deleted successfully.")
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}.")
    except Exception as e:
        print(f"Error: {e}")




"""
::      run.py        ::

# Imprimir la URL del túnel generado
print("URL del túnel HTTP:", http_tunnel)
print(ngrok.get_tunnels())

    
if len(sys.argv) < 2:
    logging.info("Please provide the phone number as a command-line argument.")
    pass
else:
    #---------------------------------------------
    # Initiate conversation with message template first if number is input
    #---------------------------------------------
    input_phonenumber = sys.argv[1]
    app.config["RECIPIENT_WAID"] = input_phonenumber
    send_template_message(app.config["RECIPIENT_WAID"], secrets)
"""
