import json
import os
import random
import socket
import sys
from lib.player_base import Player, PlayerShip


sys.path.append(os.getcwd())


class StrategicPlayer(Player):

    def __init__(self, seed=0):
        random.seed(seed)

        # フィールドを2x2の配列として持っている．
        self.field = [[i, j] for i in range(Player.FIELD_SIZE)
                      for j in range(Player.FIELD_SIZE)]

        # List of possible ship positions for each ship
        
        self.possible_positions = {'w': [], 'c': [], 's': []}

        # Initialize ships and their positions
        self.initialize_ships()

        # Initialize previous attack coordinates
        self.prev_attack_coords = None

    def initialize_ships(self):
        # Randomly position the ships
        while True:
            self.possible_positions = {'w': [], 'c': [], 's': []}
            self.ships = {}

            # Generate possible positions for each ship
            for ship_name in self.possible_positions:
                self.possible_positions[ship_name] = random.sample(
                    self.field, 3)

            # Validate ship positions
            if self.validate_ship_positions():
                break

        # Create ship objects
        for ship_name, position in self.possible_positions.items():
            self.ships[ship_name] = PlayerShip(ship_name, position)

    def validate_ship_positions(self):
        # Check if any two ships have overlapping positions
        # or are diagonally adjacent
        for i in range(len(self.possible_positions)):
            for j in range(i + 1, len(self.possible_positions)):
                pos1 = self.possible_positions[i]
                pos2 = self.possible_positions[j]

                if self.overlap(pos1, pos2) or self.diagonal_adjacency(pos1, pos2):
                    return False

        return True

    def overlap(self, pos1, pos2):
        # Check if two positions overlap
        return pos1 == pos2

    def diagonal_adjacency(self, pos1, pos2):
        # Check if two positions are diagonally adjacent
        x1, y1 = pos1
        x2, y2 = pos2

        return abs(x1 - x2) == 1 and abs(y1 - y2) == 1

    def update(self, message):
        msg = json.loads(message)

        if 'move' in msg:
            ship_name = msg['move']['ship']
            new_position = tuple(msg['move']['to'])
            self.update_possible_positions(ship_name, new_position)

    def update_possible_positions_after_hit(self, ship_name, attack_coords):
        # Update the possible positions for the ship based
        # on the attack coordinates
        possible_positions = []
        for position in self.possible_positions[ship_name]:
            if self.is_within_attack_range(position, attack_coords):
                possible_positions.append(position)

        self.possible_positions[ship_name] = possible_positions

    def update_possible_positions(self, ship_name, new_positions):
        # Update the possible positions for the ship with the new information
        self.possible_positions[ship_name] = new_positions
        self.intersect_possible_positions(ship_name)
        if ship_name in self.possible_positions:
            self.possible_positions[ship_name] = list(set(self.possible_positions[ship_name]) & set(new_positions))

    def is_within_attack_range(self, position, attack_coords):
        # Check if a position is within the attack range of the given attack coordinates
        x, y = position
        for attack_coord in attack_coords:
            attack_x, attack_y = attack_coord
            if (
                abs(x - attack_x) <= 1 and
                abs(y - attack_y) <= 1 and
                (x, y) != attack_coord
            ):
                return True

        return False

    def attack(self):
        if self.prev_attack_coords is not None:
            # Update possible opponent positions based on the previous attack
            for ship_name in self.possible_positions:
                self.update_possible_positions_after_hit(ship_name, self.prev_attack_coords)

        # Select a random position for attack
        attack_coords = random.choice(self.field)

        self.prev_attack_coords = attack_coords
        return attack_coords


def main(host, port, seed=0):
    assert isinstance(host, str) and isinstance(port, int)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((host, port))
        with sock.makefile(mode='rw', buffering=1) as sockfile:
            get_msg = sockfile.readline()
            print(get_msg)
            player = StrategicPlayer()
            sockfile.write(player.initial_condition()+'\n')

            while True:
                info = sockfile.readline().rstrip()
                print(info)
                if info == "your turn":
                    sockfile.write(player.action()+'\n')
                    get_msg = sockfile.readline()
                    player.update(get_msg)
                elif info == "waiting":
                    get_msg = sockfile.readline()
                    player.update(get_msg)
                elif info == "you win":
                    break
                elif info == "you lose":
                    break
                elif info == "even":
                    break
                elif not info:
                    continue
                else:
                    print(info)
                    raise RuntimeError("unknown information "+info)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="Sample Player for Submaline Game")
    parser.add_argument(
        "host",
        metavar="H",
        type=str,
        help="Hostname of the server. E.g., localhost",
    )
    parser.add_argument(
        "port",
        metavar="P",
        type=int,
        help="Port of the server. E.g., 2000",
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="Random seed of the player",
        required=False,
        default=0,
    )
    args = parser.parse_args()

    main(args.host, args.port, seed=args.seed)
