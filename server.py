import os
from flask import Flask, request
from flask import jsonify
from twilio.util import TwilioCapability
from twilio.rest import TwilioRestClient
import twilio.twiml

# Account Sid and Auth Token can be found in your account dashboard
ACCOUNT_SID = 'ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
AUTH_TOKEN = 'YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY'

# TwiML app outgoing connections will use
APP_SID = 'APZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ'

CALLER_ID = '+12345678901'
CLIENT = 'jenny'
message_txt ="hello from Twilio"

app = Flask(__name__)

@app.route('/token')
def token():
  account_sid = os.environ.get("ACCOUNT_SID", ACCOUNT_SID)
  auth_token = os.environ.get("AUTH_TOKEN", AUTH_TOKEN)
  app_sid = os.environ.get("APP_SID", APP_SID)

  capability = TwilioCapability(account_sid, auth_token)

  # This allows outgoing connections to TwiML application
  if request.values.get('allowOutgoing') != 'false':
     capability.allow_client_outgoing(app_sid)

  # This allows incoming connections to client (if specified)
  client = request.values.get('client')
  if client != None:
    capability.allow_client_incoming(client)

  # This returns a token to use with Twilio based on the account and capabilities defined above
  return capability.generate()

@app.route('/call', methods=['GET', 'POST'])
def call():
  """ This method routes calls from/to client                  """
  """ Rules: 1. From can be either client:name or PSTN number  """
  """        2. To value specifies target. When call is coming """
  """           from PSTN, To value is ignored and call is     """
  """           routed to client named CLIENT                  """
  resp = twilio.twiml.Response()
  if request.method == 'POST':
    from_value = request.values.get('From')
    to = request.values.get('To')
    if not (from_value and to):
      return str(resp.say("Invalid request"))
    from_client = from_value.startswith('client')
    caller_id = os.environ.get("CALLER_ID", CALLER_ID)
    if not from_client:
      # PSTN -> client
      resp.dial(callerId=from_value).client(CLIENT)
    elif to.startswith("client:"):
      # client -> client
      resp.dial(callerId=from_value).client(to[7:])
    else:
      # client -> PSTN
      resp.dial(to, callerId=caller_id)
  elif request.method == 'GET':
    resp.say(message_txt, voice='alice')
    
  return str(resp)
  
@app.route('/voice', methods=['POST'])
def voice():
  resp = twilio.twiml.Response()
  resp.say(message_txt, voice='alice')
  resp.play("http://demo.twilio.com/hellomonkey/monkey.mp3")
  return str(resp)
  
@app.route("/message", methods=['GET', 'POST'])
def message():
  resp = twilio.twiml.Response()
  account_sid = os.environ.get("ACCOUNT_SID", ACCOUNT_SID)
  auth_token = os.environ.get("AUTH_TOKEN", AUTH_TOKEN)
  app_sid = os.environ.get("APP_SID", APP_SID)
  
  from_value = request.values.get('From')
  to_val = request.values.get('To')
  if not (from_value and to_val):
    return str(resp.say("Invalid request"))
    
  caller_id = os.environ.get("CALLER_ID", CALLER_ID)
  client = TwilioRestClient(account_sid, auth_token)
  #message = client.messages.create(to=to_val, from_=from_value, body=message_txt)
  if request.method == 'POST':
    global message_txt
    message_txt = request.values.get('Body')
    try:
      #resp.dial(to_val, callerId=caller_id)
      #resp.say(message_txt, voice='alice')
      client.calls.create(from_=from_value,to=to_val,url="https://still-taiga-4190.herokuapp.com/voice")
      #message = client.messages.create(to=to_val, from_=from_value, body=message_txt)
    except Exception as e:
      app.logger.error(e)
      return jsonify({'error': str(e)}) 
  elif request.method == 'GET':
      message_txt = request.values.get('Body')
      resp.dial(to_val, callerId=caller_id)
      resp.say(message_txt, voice='alice')

  #resp.message(body_txt)
  return str(resp)
  
@app.route("/receive_sms/", methods=['GET','POST'])
def receive_sms():
  # Sender's phone numer
  from_number = request.values.get('From')
  # Receiver's phone number - Plivo number
  to_number = request.values.get('To')
  # The text which was received
  text = request.values.get('Text')
  resp = twilio.twiml.Response()
  resp.say("from="+from_number+" to="+to_number+" text="+text)
  return str(resp)

@app.route("/hello", methods=['GET', 'POST'])
def hello():
  """Respond to incoming calls with a simple text message."""
  message = "Hello from Twilio!"
  resp = twilio.twiml.Response()
  resp.message(message)
  return str(resp)

@app.route('/', methods=['GET', 'POST'])
def welcome():
  resp = twilio.twiml.Response()
  resp.say("Welcome to Twilio")
  return str(resp)

if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host='0.0.0.0', port=port, debug=True)
