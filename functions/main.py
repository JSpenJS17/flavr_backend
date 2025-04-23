from engine import cbe, ube, utv
import pandas as pd
import json

# The Cloud Functions for Firebase SDK to create Cloud Functions and set up triggers.
from firebase_functions import firestore_fn, https_fn

# The Firebase Admin SDK to access Cloud Firestore and Firebase Authentication.
from firebase_admin import initialize_app, firestore
from firebase_admin import auth as firebase_auth

app = initialize_app()

# Firestore client
db = firestore.client()

# def UM_from_json(json_name, download=False):
    # support "file_name" and "file_name.json"
    # if json_name[-5:] != ".json":
    #     json_name += ".json"

    # # load data, survey_responses.json could be loaded dynamically from firestore
    # with open(json_name) as f:
    #     json_data = json.load(f)
        
    # df = pd.DataFrame(json_data)
    # df.set_index('user_number', inplace=True)

    # # do some pandas magic, convert "Looks good" to 1, "" to 0, and "Doesn't look good" to -1
    # df.replace({"Looks good": 1, "": 0, "Doesn't look good": -1}, inplace=True)
    # df.drop(columns=['timestamp'], inplace=True) # might need timestamp later

    # return df

def UM_from_csv(csv_name):
    # support "file_name" and "file_name.csv"
    if csv_name[-4:] != ".csv":
        csv_name += ".csv"

    # load data, survey_responses.csv could be loaded dynamically from firestore
    df = pd.read_csv(csv_name)
    df.set_index('user_number', inplace=True)

    return df # users_matrix -- user taste vectors stacked on each other

def UTV_from_csv(csv_name):
    # support "file_name" and "file_name.csv"
    if csv_name[-4:] != ".csv":
        csv_name += ".csv"

    df = pd.read_csv(csv_name)
    df.set_index('dish', inplace=True)
    return df # user taste vector for the current user

def DM_from_csv(csv_path):
    if csv_path[-4:] != ".csv":
        csv_path += ".csv"

    dish_matrix = pd.read_csv(csv_path)    
    dish_matrix.set_index('dish name', inplace=True)
    
    return dish_matrix


def cre_loc(DM, UM, UTV, swipes):
    """Run the combined content recommendation engine.

    Args:
        DM (pd.DataFrame): Dish metadata (pre-baked by DM_prebaker.py).
        UM (pd.DataFrame): User matrix (stacked user taste vectors from Firestore).
        UTV (pd.DataFrame): User Taste Vector for the current user
        swipes (list of tuples): Swipe history for the current user.

    Returns:
        pd.Series: Recommended dishes and their scores, normalized to [-1, 1].
    """

    # Get the user taste vector
    UTV = utv.update_UTV_swipes(UTV, swipes)

    # Get recommendations
    cbe_recs = cbe.cbe(DM, UTV)
    ube_recs = ube.ube(UM, UTV)

    # Combine recommendations from CBE and UBE
    combined_recs = pd.concat([cbe_recs, ube_recs], axis=1)
    combined_recs.columns = ['CBE', 'UBE']
    combined_recs = combined_recs.mean(axis=1)
    combined_recs = combined_recs.sort_values(ascending=False)
    
    # Save to output file if specified
    return combined_recs
    
def make_utv(user_id):
    # upload a blank UTV to users/user_id/UTV
    UTV = UTV_from_csv("data/empty_utv.csv")
    utv_dict = UTV.to_dict()["taste"]
    utv_ref = db.collection("users").document(user_id).collection("UTV")
    batch = db.batch()
    for key, value in utv_dict.items():
        doc_ref = utv_ref.document(key)
        batch.set(doc_ref, {"value": value})
    batch.commit()

    return UTV
        

@https_fn.on_request()
def cre(req: https_fn.Request) -> https_fn.Response:
    ### MAIN API FUNCTION ###

    # Make sure it's a POST request
    if req.method != "POST":
        return https_fn.Response("Method Not Allowed", status=405)

    # Parse incoming JSON
    try:
        body = req.get_json(silent=True)
        if not body:
            return https_fn.Response("Invalid or missing JSON body", status=400)

        # Extract user ID and swipes
        user_id = body.get("user-id") # string
        swipes = body.get("swipes")   # dict

        if not user_id or not isinstance(swipes, dict):
            return https_fn.Response("Invalid format: 'user-id' or 'swipes' missing/invalid", status=400)

    except Exception as e:
        return https_fn.Response(f"Error parsing JSON: {str(e)}", status=400)
        

    # Load the dish matrix, and user matrix
    DM = DM_from_csv("data/dish_metadata.csv")
    UM = UM_from_csv("data/survey_responses.csv")


    # Download UTV for this user from Firestore
    try:
        # check if the UTV exists
        utv_ref = db.collection("users").document(user_id).collection("UTV")
        docs = utv_ref.stream()
        if not any(doc.exists for doc in docs): # not sure how slow this is
            # UTV doesn't exist, create a new (blank) one
            UTV = make_utv(user_id)

        else:
            # Load UTV from Firestore, much faster
            utv_dict = {}
            for doc in docs:
                dish = doc.id
                value = doc.to_dict().get("value")
                utv_dict[dish] = value

            utv_dict = {"taste": utv_dict}

            UTV = pd.DataFrame(utv_dict)
            UTV.index.name = "dish"
        
    except Exception as e:
        return https_fn.Response(f"Error loading UTV from Firestore: {str(e)}", status=500)

    # Update UTV using swipe data
    try:
        UTV = utv.update_UTV_swipes(UTV, swipes)
    except Exception as e:
        return https_fn.Response(f"Error updating UTV: {str(e)}", status=500)


    # Save updated UTV back to Firestore
    try:
        # utv_ref = db.collection("users").document(user_id).collection("UTV")
        utv_dict = UTV.to_dict()["taste"]
        batch = db.batch()
        for key, value in utv_dict.items():
            doc_ref = utv_ref.document(key)
            batch.set(doc_ref, {"value": value})
        batch.commit()

    except Exception as e:
        return https_fn.Response(f"Error writing UTV to Firestore: {str(e)}", status=500)


    # Run the recommendation engine
    try:
        recs = cre_loc(DM, UM, UTV, swipes).head(10)
        return https_fn.Response(json.dumps(recs.to_dict()), content_type="application/json")
    except Exception as e:
        return https_fn.Response(f"Error generating recommendations: {str(e)}", status=500)

def cre_test(swipes, user_id):
    # Load the dish matrix, and user matrix
    DM = DM_from_csv("data/dish_metadata.csv")
    UM = UM_from_csv("data/survey_responses.csv")


    # Download UTV for this user from Firestore
    try:
        # check if the UTV exists
        utv_ref = db.collection("users").document(user_id).collection("UTV")
        docs = utv_ref.stream()
        if not any(doc.exists for doc in docs): # not sure how slow this is
            # UTV doesn't exist, create a new (blank) one
            UTV = make_utv(user_id)

        else:
            # Load UTV from Firestore, much faster
            utv_dict = {}
            for doc in docs:
                dish = doc.id
                value = doc.to_dict().get("value")
                utv_dict[dish] = value

            utv_dict = {"taste": utv_dict}

            UTV = pd.DataFrame(utv_dict)
            UTV.index.name = "dish"
        
    except Exception as e:
        return https_fn.Response(f"Error loading UTV from Firestore: {str(e)}", status=500)

    # Update UTV using swipe data
    try:
        UTV = utv.update_UTV_swipes(UTV, swipes)
    except Exception as e:
        return https_fn.Response(f"Error updating UTV: {str(e)}", status=500)


    # Save updated UTV back to Firestore
    try:
        # utv_ref = db.collection("users").document(user_id).collection("UTV")
        utv_dict = UTV.to_dict()["taste"]
        batch = db.batch()
        for key, value in utv_dict.items():
            doc_ref = utv_ref.document(key)
            batch.set(doc_ref, {"value": value})
        batch.commit()

    except Exception as e:
        return https_fn.Response(f"Error writing UTV to Firestore: {str(e)}", status=500)

    UTV.to_csv("data/utv.csv") # for testing

    # Run the recommendation engine
    try:
        recs = cre_loc(DM, UM, UTV, swipes).head(10)
        return https_fn.Response(json.dumps(recs.to_dict()), content_type="application/json")
    except Exception as e:
        return https_fn.Response(f"Error generating recommendations: {str(e)}", status=500)

if __name__ == "__main__":
    # Load the dish matrix, user matrix, and swipe history
    DM = DM_from_csv("data/dish_metadata.csv")
    UM = UM_from_csv("data/survey_responses.csv")

    # Example swipe history
    swipes = {
        "pizza": 1,
        "huli huli": -1,
        "steak": 1,
        "larb": -1
    }

    user_id = "FohydHkTpxPWf3SY70b2iyMiVT02" 
    response = cre_test(swipes, user_id)
    print(response.get_data(as_text=True)) # should be a json string of the top 10 recommendations