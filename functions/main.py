from engine import cbe, ube, utv
import argparse
import pandas as pd

# The Cloud Functions for Firebase SDK to create Cloud Functions and set up triggers.
from firebase_functions import firestore_fn, https_fn

# The Firebase Admin SDK to access Cloud Firestore.
from firebase_admin import initialize_app, firestore
import google.cloud.firestore

app = initialize_app()

def history_from_csv(file_path):
    """Load the swipe history from a CSV file."""
    history = pd.read_csv(file_path)
    history = history.sort_values(by='timestamp', ascending=False)
    return history.to_dict(orient='records')

def UM_from_json(json_name, download=False):
    # support "file_name" and "file_name.json"
    if json_name[-5:] != ".json":
        json_name += ".json"

    # load data, survey_responses.json could be loaded dynamically from firestore
    with open(json_name) as f:
        json_data = json.load(f)
        
    df = pd.DataFrame(json_data)
    df.set_index('user_number', inplace=True)

    # do some pandas magic, convert "Looks good" to 1, "" to 0, and "Doesn't look good" to -1
    df.replace({"Looks good": 1, "": 0, "Doesn't look good": -1}, inplace=True)
    df.drop(columns=['timestamp'], inplace=True) # might need timestamp later

    return df

def UM_from_csv(csv_name):
    # support "file_name" and "file_name.csv"
    if csv_name[-4:] != ".csv":
        csv_name += ".csv"

    # load data, survey_responses.csv could be loaded dynamically from firestore
    df = pd.read_csv(csv_name)
    df.set_index('user_number', inplace=True)

    # do some pandas magic, convert "Looks good" to 1, "" to 0, and "Doesn't look good" to -1
    df.replace({"Looks good": 1, "": 0, "Doesn't look good": -1}, inplace=True)
    df.drop(columns=['timestamp'], inplace=True) # might need timestamp later

    return df # users_matrix -- user taste vectors stacked on each other

def DM_from_csv(csv_path):
    if csv_path[-4:] != ".csv":
        csv_path += ".csv"

    dish_matrix = pd.read_csv(csv_path)    
    dish_matrix.set_index('dish name', inplace=True)
    
    return dish_matrix

def cre_loc(DM, UM, history, num_recent=5):
    """Run the combined content recommendation engine.

    Args:
        DM (pd.DataFrame): Dish metadata (pre-baked by DM_prebaker.py).
        UM (pd.DataFrame): User matrix (stacked user taste vectors from Firestore).
        history (str): Path to the swipe history CSV file.
        num_recent (int, optional): Number of recent swipes to consider for the user taste vector. Defaults to 5.

    Returns:
        pd.Series: Recommended dishes and their scores, normalized to [-1, 1].
    """

    # Get the user taste vector
    UTV = utv.get_user_taste_vector(history, num_recent)

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
    
@https_fn.on_request()
def cre(req: https_fn.Request) -> https_fn.Response:
    ### MAIN API FUNCTION ##
    
    # way to test 
    # original = req.args.get("text")
    # if original is None:
    #     return https_fn.Response("No text parameter provided", status=400)

    # assume data directories
    data_dir = "data/"
    dish_metadata = data_dir + "dish_metadata.csv"
    user_matrix = data_dir + "survey_responses.csv"
    swipe_history = data_dir + "history.csv"

    # Load the dish matrix, user matrix, and swipe history
    DM = DM_from_csv(dish_metadata)
    UM = UM_from_csv(user_matrix)
    history = history_from_csv(swipe_history)

    # Run the collaborative recommendation engine
    recs = cre_loc(DM, UM, history, 5)
    
    print("Recommendations:")
    print(recs)

    firestore_client: google.cloud.firestore.Client = firestore.client()

    _, doc_ref_rec = firestore_client.collection("Recs").add(recs.to_dict())

    return https_fn.Response(f"Recs with ID {doc_ref_rec.id} added.")

if __name__ == "__main__":
    cre(None)

# if __name__ == "__main__":
#     # parse args if run from cmdline
#     parser = argparse.ArgumentParser(description="Run the collaborative recommendation engine.")
#     parser.add_argument("dish_metadata", help="Path to dish metadata CSV file")
#     parser.add_argument("user_matrix", help="Path to user matrix CSV file")
#     parser.add_argument("swipe_history", help="Path to swipe history CSV file")
#     parser.add_argument("-o", "--output", help="Output CSV file")
#     parser.add_argument("-n", "--num_recent", type=int, default=5, help="Number of recent swipes to consider")

#     args = parser.parse_args()

#     # Load the dish matrix, user matrix, and swipe history
#     DM = DM_from_csv(args.dish_metadata)
#     UM = UM_from_csv(args.user_matrix)
#     history = history_from_csv(args.swipe_history)

#     # Run the collaborative recommendation engine
#     recs = cre(DM, UM, history, args.num_recent)

#     if args.output:
#         recs.to_csv(args.output, index=True)
#         print(f"Recommendations saved to {args.output}")
#     else:
#         print("Recommendations:")
#         print(recs)

