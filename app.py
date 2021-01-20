import os
import time
from collections import OrderedDict
from threading import Thread

from flask import Flask, Response, request
from twilio.rest import Client
from twilio.twiml.voice_response import Dial, VoiceResponse


app = Flask(__name__)
client = Client()

# This should be set to the publicly reachable URL for your application.
# This could an ngrok URL, such as "https://17224f9e.ngrok.io".
# Do not include trailing slash when setting this variable.
BASE_URL = os.environ.get("BASE_URL", "http://XXXXXXXXXXXX.ngrok.io")

# There must be at least one phone number listed in order for the app to start.
# Be careful about committing real phone numbers to source control. Numbers in
# this list must be E.164 formatted.
AGENT_NUMBERS = ["+15555555555"]

# These two queues should be empty on application startup. For the sake of
# simplicitly, these variables are defined at the global scope. For a
# production call-center, a more sophisticated approach should be taken.
CUSTOMER_QUEUE = OrderedDict()
AGENT_QUEUE = OrderedDict()


class CustomerRedirect(Thread):
    """
    This thread class is used to delay the redirection of a customer call so that
    Twilio has enough time to create the agent's conference room before redirecting the customer to it.
    """
    def __init__(self, customer_num, customer_sid, agent_sid):
        Thread.__init__(self)
        self.customer_num = customer_num
        self.customer_sid = customer_sid
        self.agent_sid = agent_sid

    def run(self):
        time.sleep(4) # Hacks
        client.calls(self.customer_sid).update(
            twiml=f"<Response><Dial><Conference>{self.agent_sid}</Conference></Dial></Response>"
        )


@app.route("/incoming", methods=["POST"])
def incoming():
    """Handle incoming calls from any number, agent or otherwise."""
    from_number = request.form["From"]
    call_sid = request.form["CallSid"]

    if from_number in AGENT_NUMBERS:
        return handle_agent(from_number, call_sid)

    response = VoiceResponse()
    dial = Dial()

    try:
        # If an agent is available immediately, connect the customer to them.
        available_agent = AGENT_QUEUE.popitem(last=False)        
        dial.conference(available_agent[1])
    except KeyError:
        # Otherwise, place them in a conference called `Waiting Room` with the
        # other customers currently on hold.
        CUSTOMER_QUEUE[from_number] = call_sid
        dial.conference('Waiting Room')
        
    response.append(dial)
    return Response(str(response), 200, mimetype="application/xml")


def handle_agent(agent_number, agent_call_sid):
    """
    Agent will be placed in a solo conference until a caller is connected.
    Conferences are used because redirect will not work with a direct dial.
    """
    response = VoiceResponse()
    response.dial().conference(agent_call_sid)

    try:
        # If any callers are in the conference, redirect whoever has been
        # waiting the longest by popping the first caller off the queue.
        oldest_customer = CUSTOMER_QUEUE.popitem(last=False)
        redirect_thread = CustomerRedirect(oldest_customer[0], oldest_customer[1], agent_call_sid)
        redirect_thread.start()
    except KeyError:
        # If no callers are in the conference, add the agent to the agent queue
        # so that the next caller will immediately be connected to an agent.
        AGENT_QUEUE[agent_number] = agent_call_sid
    return Response(str(response), 200, mimetype="application/xml")


@app.route("/status", methods=["POST"])
def status():
    """
    Remove a caller (agent or customer) from the appropriate queue once their call is completed.
    This is needed in case a customer or an agent hangs up before being connected to someone.
    """
    if request.form["CallStatus"].lower() == "completed":
        incoming_caller = request.form["From"]
        try:
            if incoming_caller in AGENT_NUMBERS:
                AGENT_QUEUE.pop(incoming_caller)
            else:
                CUSTOMER_QUEUE.pop(incoming_caller)
        except KeyError:
            # We don't really care if this fails.
            pass

    return Response('', 200)


if __name__ == "__main__":
    if not AGENT_NUMBERS:
        raise Exception("At least one agent phone number must be provided.")
    app.run()
