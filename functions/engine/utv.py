import numpy as np
from datetime import datetime
import pandas as pd

# this needs to be updated if we ever add a dish
dishes = ['pizza', 'flatbread pizza', 'burrito', 'steak', 'mac and cheese', 'chicken tikka masala', "general tso's chicken", 'chili', 'lasagna', 'pasta carbonara', 'fettuccine alfredo', 'calzone', 'gnocchi', 'saltimbocca', 'coq au vin', 'bouillabaisse', 'duck confit', 'cassoulet', 'quiche lorraine', 'sole meunière', 'tartiflette', 'street tacos', 'mole poblano', 'enchiladas', 'pozole', 'tamales', 'cochinita pibil', 'birria', 'carne asada', 'sushi', 'ramen', 'shrimp tempura', 'tonkatsu', 'yakitori', 'udon', 'okonomiyaki', 'shabu-shabu', 'donburi', 'shawarma', 'kofta', 'tabbouleh', 'shakshuka', 'falafel', 'mansaf', 'kibbeh', 'moussaka', 'souvlaki', 'dolma (stuffed grapeleaves)', 'spanakopita', 'gyros', 'stifado', 'fasolada', 'kleftiko', 'peking duck', 'kung pao chicken', 'mapo tofu', 'sweet and sour pork', 'hot pot', 'chow mein', 'zongzi', 'beef and broccoli', 'char siu', 'butter chicken', 'biryani', 'rogan josh', 'paneer tikka', 'chana masala', 'tandoori chicken', 'vindaloo', 'pad thai', 'green curry', 'massaman curry', 'khao soi', 'larb', 'tom kha gai', 'paella', 'tortilla española', 'fabada', 'cochinillo', 'bacalao a la vizcaína', 'bibimbap', 'kimchi jjigae', 'bulgogi', 'samgyeopsal', 'sundubu jjigae', 'galbi', 'naengmyeon', 'dakgalbi', "shepard's pie", 'fish and chips', 'poke', 'huli huli', 'fajita', 'quesadilla', 'bbq ribs', 'buffalo wings', 'pot roast', 'jambalaya', 'alaskan salmon', 'fried chicken', 'chicken pot pie', 'chicken nuggets or tenders', 'po boy', 'cobb salad', 'caesar salad', 'italian salad', 'taco salad', 'greek salad', 'fattoush', 'wedge salad', 'pasta salad', 'reuben sandwich', 'club sandwich', 'philly cheese steak', 'fried chicken sandwich', 'pulled pork sandwich', 'panini/grilled cheese w/ tomato soup', 'blt', 'french dip', 'italian sandwich', 'sloppy joe', 'meatball sub', 'chicken noodle soup', 'pho', 'minestrone', 'french onion soup', 'clam chowder', 'cream of mushroom soup', 'lentil soup', 'broccoli and cheddar soup', 'tortilla soup']

def get_user_taste_vector(history, swipe_count=5):
    """Creates a user taste vector from the swipes and history data.

    Args:
        history: list of swipes, each swipe is a dict with keys 'dish name', 'swiped', 'was_recommended', and 'timestamp'
        swipe_count: number of recent swipes to consider as current swipes
    
    Returns:
        a pandas dataframe with dish names as index and a single column 'wave_rating' with the taste vector
    """

    df = pd.DataFrame(index=dishes, columns=['rating', 'count'])
    df.index.name = 'dish'
    df['rating'] = float(0)
    df['count'] = 0

    swipes = history[-swipe_count:]
    history = history[:-swipe_count]

    for swipe in history:
        rating =  swipe['swiped']
        rating *= 2 if swipe['was_recommended'] else 1
        
        if type(swipe['timestamp']) == str:
            swipe['timestamp'] = datetime.strptime(swipe['timestamp'], '%Y-%m-%d %H:%M:%S.%f')
        
        months_ago = (datetime.now() - swipe['timestamp']).days // 30

        #inverse logistic time decay function
        rating *= 1 - (.75)/(1 + np.exp(-4 * (months_ago-1.5)))
        df.at[swipe['dish name'], 'rating'] += rating
        df.at[swipe['dish name'], 'count'] += 1

    df['wave_rating'] = df.apply(lambda row: row['rating'] / row['count'] / 3 if row['count'] > 0 else 0, axis=1)

    #add in swipes
    for swipe in swipes:
        df.at[swipe['dish name'], 'wave_rating'] += swipe['swiped']
    
    np.arctan(df['wave_rating'])

    return df['wave_rating']
