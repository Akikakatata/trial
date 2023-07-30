import random
import json
import os
import random
import socket
import sys

sys.path.append(os.getcwd())
from lib.player_base import Player

def generate_valid_positions(field_size):
    field = [[i, j] for i in range(field_size) for j in range(field_size)]
    
    while True:
        ps = random.sample(field, 3)
        possible_positions = {'w': ps[0], 'c': ps[1], 's': ps[2]}
        
        validation = "fit"
        
        for i in range(len(possible_positions)):
            for j in range(i + 1, len(possible_positions)):
                pos1 = possible_positions[list(possible_positions.keys())[i]]
                pos2 = possible_positions[list(possible_positions.keys())[j]]
                x1, y1 = pos1
                x2, y2 = pos2
                
                if ((x1 == x2) or (y1 == y2)) or ((abs(x1 - x2) == 1 and abs(y1 - y2) == 1)):
                    validation = "unfit"
                    break  # No need to continue checking if one pair is unfit
            
            if validation == "unfit":
                break
        
        if validation == "fit":
            return possible_positions

# Example usage:
valid_positions = generate_valid_positions(Player.FIELD_SIZE)
print(valid_positions)
