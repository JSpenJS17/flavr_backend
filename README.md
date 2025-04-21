
You'll have to install Firebase CLI to run this. To install Firebase CLI, run:

`curl -sL https://firebase.tools | bash`

Then to run the Firebase Functions, run these (you might have to install some other stuff):
```
cd functions
firebase login
python3.11 -m pip install pandas
firebase emulators:start
```

This will set up an EMULATOR for testing. It's all local -- no damage to our wallets.
**To test this, it will give you a URL on startup for each Firebase Function that it fires up.**
Use the command below with that URL and you'll get a response.


## Important Part:

To test, I've been using this curl command (replace the URL with either the test one or the real one):
**`curl -X POST <FUNCTION_URL> -H "Content-Type: application/json" -d '{"user-id": "FohydHkTpxPWf3SY70b2iyMiVT02", "swipes": {"sushi": 1, "pizza": -1, "steak": 1, "huli huli": -1}}'`**

**https://us-central1-flavr-4e17f.cloudfunctions.net/cre <-- THIS IS THE REAL PRODUCTION URL**

We need to figure out authentication, I have no clue how that will work. When authentication is bypassed, the functions work as intended.

From the frontend's perspective, it should be as simple as an HTTP post request. i.e. the frontend should NOT NEED TO KNOW about firebase. It's all a magic black box in the sky.

If you have questions feel free to hit my line :)


Input JSON format:
{
  "user-id": "FohydHkTpxPWf3SY70b2iyMiVT02", 
  "swipes": {
    "sushi": 1, 
    "pizza": -1, 
    "steak": 1, 
    "huli huli": -1
  }
}