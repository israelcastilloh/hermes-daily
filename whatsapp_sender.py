# Importing the Required Library
from twilio.rest import Client
import sys

def main(input_phonenumber):

    account_sid = 'AC6841ab57e3cdc40ba9c031d5476f2fef'
    auth_token = '2328f1f021984ccc52c41872ce02311c'
    client = Client(account_sid, auth_token)

    message = client.messages.create(
      from_='whatsapp:+14155238886',
      body='Hello, world!',
      to=f'whatsapp:{input_phonenumber}'
    )

    print(message.sid)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide the phone number as a command-line argument.")
    else:
        input_phonenumber = sys.argv[1]
        main(input_phonenumber)