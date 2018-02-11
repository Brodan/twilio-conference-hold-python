# twilio-conference-hold-python
This [Twilio](https://www.twilio.com/) app demonstrates a call center that places incoming callers into a conference with one another until connected with an agent.

## Install Instructions
```
$ git clone https://github.com/Brodan/twilio-conference-hold-python.git
$ cd twilio-conference-hold-python
$ virtualenv venv
$ . venv/bin/activate
$ pip install -r requirements.txt
$ export TWILIO_ACCOUNT_SID="XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
$ export TWILIO_AUTH_TOKEN="YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY"
```

## Run Instructions
Note: To run this app locally you'll need to have [ngrok](https://ngrok.com/) installed.

```
$ ngrok http 5000
$ export BASE_URL="YOUR_NGROK_URL_HERE"
$ python app.py
```

## License
MIT
