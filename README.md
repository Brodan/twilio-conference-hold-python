# twilio-conference-hold-python
This [Twilio](https://www.twilio.com/) app demonstrates a call center that places incoming callers into a conference with one another until connected with an agent.

Interested in getting started with Twilio? [Sign up with my referral and get $10 in credit](https://www.twilio.com/referral/u9A86w)!

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
Note: The easiest solution to running this app locally is using [ngrok](https://ngrok.com/).

```
$ ngrok http 5000
$ export BASE_URL="YOUR_NGROK_URL_HERE"
$ python app.py
```

## License
MIT
