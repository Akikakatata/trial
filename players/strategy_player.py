import json
import os
import random
import socket
import sys

sys.path.append(os.getcwd())

from lib.player_base import Player, PlayerShip


class StrategicPlayer(Player):

    def __init__(self, seed=0):
        random.seed(seed)

        # Field size
        self.FIELD_SIZE = Player.FIELD_SIZE

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
        # Check if any two ships have overlapping positions or are diagonally adjacent
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


    def update_possible_positions(self, ship_name, new_positions):
        # Update the possible positions for the ship with the new information
        self.possible_positions[ship_name] = new_positions        # Update the possible positions for the ship based on the attack coordinates
        possible_positions = []
        for position in self.possible_positions[ship_name]:
            if self.is_within_attack_range(position, attack_coords):
                possible_positions.append(position)

        self.possible_positions[ship_name] = possible_positions


        # Retain only the positions that exist in both sets of information
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

    def get_random_valid_move(self, ship):
        # Get a random valid move for the ship
        possible_moves = []
        for x in range(self.FIELD_SIZE):
            for y in range(self.FIELD_SIZE):
                if ship.can_reach((x, y)) and self.overlap((x, y), ship.position) is None:
                    possible_moves.append((x, y))

        return random.choice(possible_moves)

    def action(self):
        if self.prev_attack_coords is not None:
            # Opponent moved, attack to scope out their position
            if self.prev_attack_coords[0] == "move":
                attack_coords = self.get_scope_attack_coords()
                attack_coord = random.choice(attack_coords)
                self.prev_attack_coords = ("attack", attack_coord)
                return json.dumps(self.attack(attack_coord))

            # Opponent attacked and hit one of my ships
            if self.prev_attack_coords[0] == "attack" and self.prev_attack_coords[1] == "hit":
                ship_hit = self.get_hit_ship()
                possible_positions = self.possible_positions[ship_hit]
                new_position = random.choice(possible_positions)

                self.ships[ship_hit].move(new_position)
                self.update_possible_positions(ship_hit, self.prev_attack_coords[2])

                move_command = self.move(ship_hit, new_position)
                self.prev_attack_coords = None
                return json.dumps(move_command)

            # Opponent attacked but missed or destroyed my ship
            if self.prev_attack_coords[0] == "attack":
                possible_positions = self.get_possible_opponent_positions()
                if len(possible_positions) > 0:
                    attack_coord = self.select_attack_coordinate(possible_positions)
                    self.prev_attack_coords = ("attack", attack_coord)

                    if self.attack(attack_coord):
                        ship_hit = self.get_hit_ship()
                        if ship_hit is not None and not self.ships[ship_hit].moved:
                            self.prev_attack_coords = ("attack", "hit", self.prev_attack_coords[2])

                    return json.dumps(self.attack(attack_coord))

        # Opponent's turn, no information
        return ""

    def get_scope_attack_coords(self):
        # Get attack coordinates to scope out opponent's position
        attack_coords = []

        for x in range(1, self.FIELD_SIZE - 1):
            for y in range(1, self.FIELD_SIZE - 1):
                attack_coords.append((x, y))

        return attack_coords

    def get_hit_ship(self):
        # Get the ship name that was hit by the opponent's attack
        for ship_name, ship in self.ships.items():
            if ship.health < ship.max_health:
                return ship_name

        return None

    def get_possible_opponent_positions(self):
        # Get a list of possible opponent positions
        possible_positions = []
        for ship_name, positions in self.possible_positions.items():
            if len(positions) > 0:
                possible_positions.extend([(ship_name, position) for position in positions])

        return possible_positions

    def select_attack_coordinate(self, possible_positions):
        # Select an attack coordinate from the list of possible positions
        random.shuffle(possible_positions)

        for ship_name, position in possible_positions:
            x, y = position
            attack_coords = []
            for i in range(x - 1, x + 2):
                for j in range(y - 1, y + 2):
                    if 0 <= i < self.FIELD_SIZE and 0 <= j < self.FIELD_SIZE:
                        attack_coords.append((i, j))

            random.shuffle(attack_coords)
            for attack_coord in attack_coords:
                if self.is_valid_attack_coordinate(attack_coord):
                    return attack_coord

        return random.choice(possible_positions)[1]

    def is_valid_attack_coordinate(self, attack_coord):
        # Check if the attack coordinate is valid (within the field and not attacked before)
        x, y = attack_coord
        return 0 <= x < self.FIELD_SIZE and 0 <= y < self.FIELD_SIZE and self.field[x][y] == " "

    def main(self, host, port, seed=0):
        assert isinstance(host, str) and isinstance(port, int)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((host, port))
            with sock.makefile(mode='rw', buffering=1) as sockfile:
                get_msg = sockfile.readline()
                print(get_msg)
                sockfile.write(self.initial_condition()+'\n')

                while True:
                    info = sockfile.readline().rstrip()
                    print(info)

                    if info.startswith("opponent move"):
                        self.prev_attack_coords = ("move",)
                    elif info.startswith("opponent attack"):
                        coords = info.split()[2:]
                        self.prev_attack_coords = ("attack", coords)

                    if info == "your turn":
                        sockfile.write(self.action()+'\n')
                        get_msg = sockfile.readline()
                        self.update(get_msg)
                    elif info == "waiting":
                        get_msg = sockfile.readline()
                        self.update(get_msg)
                    elif info == "you win":
                        break
                    elif info == "you lose":
                        break
                    elif info == "even":
                        break
                    else:
                        raise RuntimeError("unknown information")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="Strategic Player for Submarine Game")
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

    player = StrategicPlayer(seed=args.seed)
    player.main(args.host, args.port)
