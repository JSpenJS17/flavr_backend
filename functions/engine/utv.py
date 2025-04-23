import numpy as np
from datetime import datetime
import pandas as pd

def update_UTV_swipes(UTV, swipes):
    """Updates the user taste vector based on incoming swipes.

    Args:
        UTV (pd.DataFrame): User Taste Vector for the current user
        swipes (list of dictionaries): Incoming swipes for recommendation engine
    
    Returns:
        a pandas dataframe with dish names as index and a single column 'taste' with the taste vector
    """

    #scale down current UTV
    UTV['taste'] = UTV['taste'] * .5

    #add in swipes
    for dish_name, swipe in swipes.items():
        UTV.at[dish_name, 'taste'] += swipe
    
    #normalize the UTV
    np.arctan(UTV['taste'])

    return UTV

def update_UTV_recs(UTV, recs):
    """Updates the user taste vector based on reactions to recommendations.
    Args:
        UTV (pd.DataFrame): User Taste Vector for the current user
        rec (list of dictionaries): Reactions to recommendations
    
    Returns:
        a pandas dataframe with dish names as index and a single column 'taste' with the taste vector
    """

    #update current UTV based on reactions
    for rec in recs:
        UTV.at[rec['dish name'], 'taste'] += rec['swiped']
    
    #normalize the UTV
    np.arctan(UTV['taste'])

    return UTV
