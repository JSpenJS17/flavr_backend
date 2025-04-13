
You'll have to install Firebase CLI to run this. To install Firebase CLI, run:

`curl -sL https://firebase.tools | bash`

Then to run the Firebase Functions, run these (you might have to install some other stuff):
```
cd functions
firebase login
python3.11 -m pip install pandas
python3.11 -m venv venv
firebase emulators:start
```

You'll get a bunch of error messages telling you to run some commands and you might have to specifically install Python 3.11 (on my machine, `sudo apt install python3.11`)

I uploaded `working_correct.txt` which is what my machine outputs when it starts up. The link http://127.0.0.1:5001/test-35b4b/us-central1/cre is a part of that output and is what you'll need to use to test the function.

This was hastily written and I don't remember all of the steps so here's the link to the guide I followed: **https://firebase.google.com/docs/functions/get-started?gen=2nd#python**

**Final note**: I set up a test project for this (test-35b4b) so you might need access to it to actually run the code. If you do need access, it's worth it to set up your own test project or to just use flavr's project to set it up for production immediately.

Hit my line if you have questions :)

