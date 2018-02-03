import os
from flask import Flask, request, Response
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client


app = Flask(__name__)
client = Client()

# This should be set to the publicly reachable URL for your application.
# This could an ngrok URL, such as "https://17224f9e.ngrok.io".
# Do not include trailing slash when setting this variable.
BASE_URL = os.environ["BASE_URL"]

# There must be at least one phone number listed in order for the app to start.
# Be careful about committing real phone numbers to source control. Numbers in
# this list must be E.164 formatted.
AGENT_NUMBERS = ["+15555555555"]

# These two queues should be empty on application startup. For the sake of
# simplicitly, these variables are defined at the global scope. For a
# production call-center, a more sophisticated approach should be taken.
CUSTOMER_QUEUE = []
AGENT_QUEUE = []


@app.route("/incoming_call", methods=["POST"])
def incoming_call():
    """Handle incoming calls from any number, agent or otherwise.

    :return: The appropriate TwiML to handle the call, i.e. a
        twilio.twiml.voice_responce.VoiceResponse object, casted to a string.

        The contents of the TwiML will vary depending on if an agent or a
        customer is calling.
    :rtype: str
    """

    from_number = request.form["From"]
    call_sid = request.form["CallSid"]

    if from_number in AGENT_NUMBERS:
        return handle_agent(from_number, call_sid)

    response = VoiceResponse()
    try:
        # If an agent is available immediately, connect the customer with them.
        available_agent = AGENT_QUEUE.pop(0)
        response.enqueue(available_agent["call_sid"])
    except IndexError:
        # Otherwise, place them in a conference called `call_center` with all
        # other customers currently on hold.
        CUSTOMER_QUEUE.append({
            "number": from_number,
            "call_sid": call_sid,
        })
        response.enqueue('call_center')

    return Response(str(response), 200, mimetype="application/xml")


@app.route('/conference/<conference_name>', methods=['POST'])
def conference(conference_name):
    """Connect an in-progress call to an existing conference.

    :param conference_name: The name of the Twilio <Conference> to connect the
        caller to. This name will be a unique call sid from an incoming caller.

    :return: The appropriate TwiML to handle the call, i.e. a
        twilio.twiml.voice_responce.VoiceResponse object, casted to a string.
    :rtype: str
    """

    response = VoiceResponse().dial().conference(conference_name)
    return Response(str(response), 200, mimetype="application/xml")


def handle_agent(agent_number, agent_call_sid):
    """Agent will be placed in a conference until a caller is connected.

    :param agent_number: The phone number of the incoming agent.
    :param agent_call_sid: The unique call sid of the incoming agent.
    :return: The appropriate TwiML to handle the call, i.e. a
        twilio.twiml.voice_responce.VoiceResponse object, casted to a string.
    :rtype: str
    """

    response = VoiceResponse()
    response.dial().conference(agent_call_sid)

    try:
        # If any callers are in the conference, redirect whoever has been
        # waiting the longest by popping the first caller off the queue.
        oldest_call = CUSTOMER_QUEUE.pop(0)
        client.calls(oldest_call["call_sid"]).update(
            url=BASE_URL + '/conference/' + agent_call_sid,
            method="POST")
    except IndexError:
        # If no callers are in the conference, add the agent to the agent queue
        # so that the next caller will automatically be connected to an agent.
        AGENT_QUEUE.append({
            "number": agent_number,
            "call_sid": agent_call_sid,
        })

    return Response(str(response), 200, mimetype="application/xml")


if __name__ == "__main__":
    if not AGENT_NUMBERS:
        raise Exception("At least one agent phone number must be provided.")

    app.run()
