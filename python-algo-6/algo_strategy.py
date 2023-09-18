import gamelib
import random
import math
import warnings
from sys import maxsize
import json


"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips: 

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical 
  board states. Though, we recommended making a copy of the map to preserve 
  the actual current map state.
"""

class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        """ 
        Read in config and perform any initial setup here 
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0
        # This is a good place to do initial setup
        self.scored_on_locations = [[8, 5]]

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.

        self.starter_strategy(game_state)

        game_state.submit_turn()


    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """

    def starter_strategy(self, game_state):
        """
        For defense we will use a spread out layout and some interceptors early on.
        We will place turrets near locations the opponent managed to score on.
        For offense we will use long range demolishers if they place stationary units near the enemy's front.
        If there are no stationary units to attack in the front, we will send Scouts to try and score quickly.
        """
        #self.build_reactive_defense(game_state)
        self.build_initial_defences(game_state)
        # Now build reactive defenses based on where the enemy scored
        

        if game_state.turn_number % 2 == 0:
            if len(game_state.game_map[20, 8]) > 0:
                game_state.attempt_spawn(SCOUT, [21, 7], 1000)
            
        else:
            last_scored_location = self.scored_on_locations[-1]
            #game_state.attempt_spawn(INTERCEPTOR, last_scored_location)

    def build_initial_defences(self, game_state):
        """
        Initial setup. We will use turrets as the primary defense as they are cheapest, and build an additional
        long-range support to defend our atackers.
        """
        tier1_destructors_points = [[0, 13], [1, 13], [2, 13], [3, 13], [24, 13], [25, 13], [26, 13], [27, 13], [4, 12], [23, 12], [5, 11], [22, 11], [6, 10], [21, 10], [7, 9], [13, 9], [20, 9], [8, 8], [13, 8], [15, 8], [19, 8], [9, 7], [13, 7], [15, 7], [18, 7], [10, 6], [13, 6], [15, 6], [17, 6], [11, 5], [13, 5], [15, 5], [16, 5], [12, 4], [13, 4], [15, 4], [3, 12], [24, 12], [12, 5], [13, 12], [13, 11], [15, 11], [13, 10], [15, 10], [13, 9], [15, 9], [13, 8], [15, 8], [13, 7], [15, 7], [13, 6], [15, 6]]
        tier2_destructors_points = [[3, 12], [24, 12], [12, 5]]

        tier1_upgrades_points = [[13, 12], [13, 11], [15, 11], [13, 10], [15, 10], [13, 9], [15, 9], [13, 8], [15, 8], [13, 7], [15, 7], [13, 6], [15, 6]]

        support_points = [[20, 8], [19, 7], [18, 6], [17, 5], [16, 4]]
        #secondary_support_points = [[12, 5], [13, 4], [14, 4], [15, 5]]

        if game_state.turn_number % 2 == 1:
            game_state.attempt_upgrade(support_points)
            game_state.attempt_spawn(SUPPORT, support_points)
            game_state.attempt_upgrade(support_points)
        game_state.attempt_spawn(TURRET, tier1_destructors_points)
        #game_state.attempt_upgrade(secondary_support_points)
        #game_state.attempt_spawn(SUPPORT, secondary_support_points)
        #game_state.attempt_upgrade(secondary_support_points)
        game_state.attempt_upgrade(tier1_upgrades_points)
        game_state.attempt_spawn(TURRET, tier1_upgrades_points)
        game_state.attempt_upgrade(support_points)
        game_state.attempt_spawn(SUPPORT, support_points)
        game_state.attempt_upgrade(support_points)
        game_state.attempt_spawn(TURRET, tier2_destructors_points)

    def is_left_heavy(self, game_state):
        """Detects enemy defense units, Returns true for left, 1 for right"""
        left_unit_count = self.detect_enemy_unit(game_state, valid_x=[0, 1, 2, 3], valid_y=[14, 15, 16, 17])
        right_unit_count = self.detect_enemy_unit(game_state, valid_x=[24, 25, 26, 27], valid_y=[14, 15, 16, 17])
        return left_unit_count > right_unit_count

    def detect_enemy_unit(self, game_state, unit_type=None, valid_x = None, valid_y = None):
        total_units = 0
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        total_units += 1
        return total_units

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called 
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at in json-docs.html in the root of the Starterkit.
        """
        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        events = state["events"]
        breaches = events["breach"]
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly, 
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.append(location)
                gamelib.debug_write("All locations: {}".format(self.scored_on_locations))


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
