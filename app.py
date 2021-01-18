import os
import time
from collections import OrderedDict
from threading import Thread

from flask import Flask, Response, request
from twilio.rest import Client
from twilio.twiml.voice_response import Dial, VoiceResponse

app = Flask(__name__)
client = Client()
BASE_URL = os.environ.get("BASE_URL", "http://XXXXXXXXXXXX.ngrok.io") # Replace this value.

AGENT_NUMBERS = ["+15555555555"] # Replace this value.

CUSTOMER_QUEUE = OrderedDict()
AGENT_QUEUE = OrderedDict()


class CustomerRedirect(Thread):
    def __init__(self, customer_sid, agent_sid):
        Thread.__init__(self)
        self.customer_sid = customer_sid
        self.agent_sid = agent_sid

    def run(self):
        time.sleep(5) # HACKS
        client.calls(self.customer_sid).update(
            twiml=f"<Response><Dial><Conference>{self.agent_sid}</Conference></Dial></Response>"
        )


@app.route("/incoming", methods=["POST"])
def incoming():
    from_number = request.form["From"]
    call_sid = request.form["CallSid"]

    if from_number in AGENT_NUMBERS:
        return handle_agent(from_number, call_sid)

    response = VoiceResponse()
    dial = Dial()

    try:
        available_agent = AGENT_QUEUE.popitem(last=False)        
        dial.conference(available_agent[1])
    except KeyError:
        CUSTOMER_QUEUE[from_number] = call_sid
        dial.conference('Waiting Room')
        
    response.append(dial)
    return Response(str(response), 200, mimetype="application/xml")


def handle_agent(agent_number, agent_call_sid):
    response = VoiceResponse()
    response.dial().conference(agent_call_sid)

    try:
        oldest_call = CUSTOMER_QUEUE.popitem(last=False)
        redirect_thread = CustomerRedirect(oldest_call[1], agent_call_sid)
        redirect_thread.start()
    except KeyError:
        AGENT_QUEUE[agent_number] = agent_call_sid
    return Response(str(response), 200, mimetype="application/xml")


@app.route("/status", methods=["POST"])
def status():
    if request.form["CallStatus"].lower() == "completed":
        try:
            CUSTOMER_QUEUE.pop(request.form["From"])
        except KeyError:
            # We don't really care if this fails.
            pass

    return Response('', 200)


if __name__ == "__main__":
    if not AGENT_NUMBERS:
        raise Exception("At least one agent phone number must be provided.")
    app.run()
