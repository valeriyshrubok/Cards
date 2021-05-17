from random import shuffle, choice, random, randint
from datetime import datetime
import os
import sys
import time
import json
import settings

class Support:

    class ReturnToGame(Exception):
        pass

    answers = {
        'n': False,
        'no': False,
        'net': False,
        chr(1090): False,
        'y': True,
        'yes': True,
        'da': True,
        chr(1085): True,
    }

    @staticmethod
    def answer_to_bool(answ):
        return Support.answers.get(answ.lower(), False)

    @staticmethod
    def probability(score):
        chance = (score - 11) * 10
        return chance if chance > 0 else 0

    @staticmethod
    def is_digit(some, dig_val=None):
        if isinstance(some, (int, float)) or some.count('.') <= 1 and some.replace(".", '').isdigit():
            if dig_val:
                if int(some) in dig_val:
                    return int(some)
                return
            else:
                return True

    @staticmethod
    def get_correct_time():
        n = datetime.now()
        return f"{n.day}.{n.hour}.{n.minute}.{n.second}"

    @staticmethod
    def passing():
        pass

class Deck:
    def __init__(self):
        self.deck = []
        for m in ["♠", "♣", "♦", "♥"]:
            for r in range(2, 15):
                v = r
                if r == 11:
                    r = "J"
                    v = 10
                if r == 12:
                    r = "Q"
                    v = 10
                if r == 13:
                    r = "K"
                    v = 10
                if r == 14:
                    r = "A"
                    v = 1
                self.deck.append(Card(r, v, m))

    def shuffle(self):
        return shuffle(self.deck)

    def dealCard(self):
        return self.deck.pop()

class Card:
    def __init__(self, rank, val, mast):
        self.rank = rank
        self.val = val
        self.mast = mast

    def getcardValue(self):
        return self.val

    def __repr__(self):
        return f"{self.mast}{self.rank}{self.mast}"

class Player:

    def __init__(self, name, deck_link, hand=None, bank=1000):
        self.hand = []
        self.bank = 1000
        self.current_bet = 0
        self.name = f"mr. {name}"
        self.is_dead = False
        self.passing = False
        self.current_deck = deck_link
        print(f'Player {self.name} created.')

    def move(self):
        try:
            self.current_interface()
            if Support.answer_to_bool(input('Взять карту? y/n')):
                self.take_card()
                self.checkin_score()
                return self.move()
        except AssertionError:
            self.is_dead = True
            self.return_cards()

    def return_cards(self):
        self.current_deck.deck += self.hand
        self.hand.clear()

    def current_interface(self):
        template = f"Your hand: {self.hand} " \
                   f"Score: {self.get_current_score()} " \
                   f"Chance burned: {Support.probability(self.get_current_score())} %"
        print(template)

    def checkin_score(self):
        assert self.get_current_score() <= 21

    def get_current_score(self):
        return sum([card.val for card in self.hand])

    def take_card(self):
        new_card = self.current_deck.dealCard()
        print(f"{self.name} take {new_card};")
        if new_card.rank == 'A':
            if isinstance(self, AutoPlayer):
                new_card.val = 11 if self.get_current_score() <= 10 else 1
            else:
                new_card.val = self.tuz()
        self.hand.append(new_card)

    def tuz(self):
        inp = Support.is_digit(input('TUZ 11 or 1: '), (1, 11))
        if inp:
            return inp
        self.tuz()

    def heal(self):
        self.is_dead = False
        self.passing = False

    def take_bet(self, supp=''):
        inp = input(f"{supp} Take your bet {self.name}. \nYou bank: {self.bank} BYN: ")
        if Support.is_digit(inp):
            bet = float(inp)
            if bet <= self.bank:
                self.current_bet = bet
                self.bank -= bet
                return
        self.take_bet("шутник?")

    def get_player_temp(self):
        player_template = {
            'hand': self.get_dict_hand(),
            'bank': self.bank,
            'name': self.name,
            'is_bot': isinstance(self, AutoPlayer)
        }
        return player_template

    def get_dict_hand(self):
        card_list = []
        for card in self.hand:
            card_dict = dict()
            card_dict["rank"] = card.rank
            card_dict["val"] = card.val
            card_dict["mast"] = card.mast
            card_list.append(card_dict)
        return card_list

    def __repr__(self):
        return f'{self.name} {self.hand}; score: {self.get_current_score()} chance burned {Support.probability(self.get_current_score())} % '

class AutoPlayer(Player):

    def __init__(self, name, deck_link, hand=None, bank=0):
        super(AutoPlayer, self).__init__(name, deck_link)
        self.bank = bank or self.random_money()
        self.is_bot = True

    def random_money(self):
        return int(random() * 1000)

    def move(self):
        if not self.is_dead or not self.passing:
            try:
                while self.worth_taking():
                    self.hmmmm()
                    self.take_card()
                    self.checkin_score()
                self.passing = True
                print(f"{self.name} - Decided he'd had enough.")
            except AssertionError:
                print(f"{self.name} burned with score {self.get_current_score()}")
                self.is_dead = True
                self.return_cards()
        else:
            pass

    def hmmmm(self):
        time.sleep(random() * len(self.hand))

    def worth_taking(self):
        current_score = self.get_current_score()
        probability = Support.probability(current_score)
        return self.take_it_anyway(probability)

    @staticmethod
    def take_it_anyway(probability):
        probability_pull = [True for _ in range(100 - probability)] + [False for _ in range(probability)]
        shuffle(probability_pull)
        return choice(probability_pull)

    def take_bet(self, supp=''):
        bet = randint(0, int(self.bank))
        self.current_bet = bet
        self.bank -= bet
        print(f"Bot {self.name} take {bet} BYN bet.")

class Gameplay:

    def __init__(self):
        self.deck = self.generate_deck()
        self.player_num = 0
        self.players = []
        self.alive_players = []
        self.save_path = 'saves/'
        self.actions = {
            "save": self.quick_save,
            "load": self.load_game,
            "exit": self.end_game,
            "pass": self.return_to_game,
        }

    def generate_deck(self):
        return Deck()

    def run(self):
        self.get_player_num()
        self.generate_players()
        self.create_diller()

        # gameplay
        r = 0

        while self.players:
            print(f"====================================== ROUND {r} ======================================")
            self.interface()
            self.heal_players()
            self.deck.shuffle()

            for current_player in self.players:
                current_player.take_bet()
                current_player.move()

            self.diller.move()

            self.check_win()
            self.return_cards()
            r += 1
        return self.run()

    def quick_save(self):
        file_name = input("Named current save:") or f"game_{Support.get_correct_time()}"
        with open(f"{self.save_path}{file_name}.json", 'w') as save_file:
            json.dump(self.prepare_players(), save_file)

    def prepare_players(self):
        players_list = list()
        for player in self.players:
            players_list.append(player.get_player_temp())
        return players_list

    def create_diller(self):
        self.diller = AutoPlayer('*Diller*', self.deck, bank=10000)

    def get_player_num(self):
        user_inp = input("Enter number of players:")
        if self.check_valid_num(user_inp):
            self.player_num = int(user_inp)
        else:
            self.get_player_num()

    def interface(self):
        for pl in self.players:
            print(f"{pl.name} | {pl.bank} BYN")
        print(f"KAZINO BANK: {self.diller.bank} BYN")
        inp = input("Open menu?:")
        self.menu(inp)

    def menu(self, inp):
        try:
            if Support.answer_to_bool(inp):
                self.print_menu()
                user_act = input("Change your action:")
                self.actions.get(user_act, Support.passing)()
                return self.menu(inp)
        except Support.ReturnToGame:
            return

    def load_game(self):
        print("Loads Games: ")
        saves = dict()
        for _, _, filenames in os.walk(self.save_path):
            for ind, save_name in enumerate(filenames):
                saves[str(ind)] = save_name
                print(f"{ind} : {save_name}")

        inp = input('Change save game:')
        name_for_load = saves.get(inp, "unknown")
        with open(f"{self.save_path}{name_for_load}", "r") as read_file:
            data = json.load(read_file)
            self.update_players(data)

    def update_players(self, last_players_state):
        self.players = []
        for ps in last_players_state:
            if ps['is_bot']:
                self.players.append(AutoPlayer(ps['name'], self.deck, ps['bank'], self.create_hand(ps['hand'])))
            else:
                self.players.append(Player(ps['name'], self.deck, ps['bank'], self.create_hand(ps['hand'])))

    def create_hand(self, json_cards):
        return self.return_hand(json_cards)

    def return_hand(self, json_cards):
        hand = []
        for c in json_cards:
            hand.append(Card(c['rank'], c['val'], c['mast']))
        return hand

    def end_game(self):
        sys.exit()

    def print_menu(self):
        for k, v in self.actions.items():
            print(f"{k}: {v.__name__}")

    def return_to_game(self):
        raise Support.ReturnToGame

    @staticmethod
    def check_valid_num(inp, max_count=settings.MAX_PLAYERS):
        if inp.isdigit() and int(inp) <= max_count:
            return True       

    def generate_players(self):
        for num in range(self.player_num):
            current_player = self.create_player(num)
            self.players.append(current_player)
            self.alive_players.append(current_player)

    def is_bot_realy(self, name, supp=''):
        inp = input(f"{supp}{name} is bot? y/n")
        if inp in Support.answers.keys():
            return Support.answer_to_bool(inp)
        else:
             self.is_bot_realy(name, 'Я тебя ещё раз спрашиваю, ')

    def create_player(self, num):
        name = input(f"Enter {num} player name.")
        is_bot = self.is_bot_realy(name) if name else True
        return self.change_mode(name or str(num), is_bot)

    def change_mode(self, name, is_bot):
        if is_bot:
            return AutoPlayer(name, self.deck)
        return Player(name, self.deck)

    def heal_players(self):
        for current_player in self.players:
            current_player.heal()
                 
    def check_win(self):
        players = sorted(self.players, key=lambda x: x.get_current_score() if x.get_current_score() <= 21 else 0)[::-1]
        print([i.get_current_score() for i in players])
        bonus = sum([p.current_bet for p in players]) * 2
        for i, p in enumerate(players):
            if p.get_current_score() != 0 and (p.get_current_score() >= self.diller.get_current_score()
                                               or p.get_current_score() == 21 or i == 0
                                               or p.get_current_score() == players[0].get_current_score()):
                p.bank += int(bonus / len(players))
                self.diller.bank -= p.current_bet
                print(f'{p.name} +{bonus / len(players)} BYN BANK {p.bank} BYN')
            else:
                print(f'{p.name} -{p.current_bet} BANK {p.bank} BYN')
                self.diller.bank += p.current_bet
                if p.bank <= 0:
                    print(f'{p.name} won.')
                    del self.players[self.players.index(p)]

    def return_cards(self):
        for p in self.players:
            p.return_cards()     
