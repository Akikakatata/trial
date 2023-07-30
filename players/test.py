import random
import json
import os
import random
import socket
import sys

sys.path.append(os.getcwd())
from lib.player_base import Player



# Example usage:
valid_positions = generate_valid_positions(Player.FIELD_SIZE)
print(valid_positions)
