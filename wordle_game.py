
from enum import Enum
import random
import sys
import os
import json
import string
from datetime import datetime
from collections import Counter
from dataclasses import dataclass   
from colorama import init, Fore, Back, Style


WORD_LENGTH = 5
ALPHABET_DICT = {char: idx for idx, char in enumerate(string.ascii_lowercase)}
COLOR_PRIORITY = {"gray": 0, "white": 0, "yellow": 1, "green": 2}

class Status(Enum):
    ONGOING = "ongoing"
    WON = "won"
    LOST = "lost"

# Word class wrapper for a persistent state including the colors
@dataclass
class Letter:
    char: str
    color: str

class Alphabet:
    def __init__(self):
        self.alphabet_words = [Letter(c, 'gray') for c in (ALPHABET_DICT.keys())]
    def __getitem__(self, key):
        return self.alphabet_words[key]

class Word:
    def __init__(self, guessed_word):
        temp = []
        if not guessed_word:
            temp = [Letter('_', 'gray') for _ in range(WORD_LENGTH)]
        else:
            temp = [Letter(c, 'gray') for c in guessed_word]
        self.actual_word = temp      

    def __getitem__(self, key):
        return self.actual_word[key]
    
    def __setcolor__(self, key, col):
        self.actual_word[key].color = col
    
    def __str__(self):
        obj = ''.join([el.char for el in self.actual_word])
        return f"{obj}"    

class Board:
    def __init__(self):
        """
        'board_arr' will keep all of the guessed words, a list of list of chars.
        Hence, it will contain a list of list of Word objects, formed by letter objects
        """
        self.all_words = []
        self.num_attempts = 0
        self.max_attempts = 6
        self.sol_lenght = WORD_LENGTH
        self.boar_arr = [Word('') for _ in range(self.max_attempts)]        
        self.status = Status.ONGOING
        self.wordfile = "wordlist.txt"
        self.outputFile = "data/attempts.json"
        self.solution = self.load_word()
        self.alphabet = Alphabet()
        # Colorama
        init(autoreset=True)
        
    def load_word(self):
        """
        Loads the word to guess from a text file, checking that if the word was already guessed.
        The structure of the attempts.json file will be:
        {
            "actual_word": ...,
            "last_word_guessed": ...,
            "num_attempts": ...,
            "result": ...,
            "date": ...,        
        }
        """
        dir_path = os.path.dirname(os.path.realpath(__file__))
        os.makedirs(os.path.join(dir_path, "data"), exist_ok=True)
        if not os.path.isfile("data/attempts.json"):
            with open("data/attempts.json", 'w') as af:
                json.dump([], af)

        with open(self.wordfile, "r") as word_file, open(self.outputFile, "r") as json_out:
            # Will need to be modified if the file containing the valid words changes
            word_selection = word_file.readline().split(',')
            json_data = json.load(json_out)

            # Get all valid words
            self.all_words = word_selection

            guessed_words = set()
                     
            if json_data:
                for entry in json_data:
                    guessed_words.add(entry.get("word_guessed"))   
                # Get unique words from set intersection
                possible_words = set(word_selection) - guessed_words 
            else:   
                possible_words = set(word_selection)
            
            chosen_word = random.choice(list(possible_words)) 
            # print(f"Solution is {chosen_word}")
            return chosen_word  
            
    def guessWord(self, guessedWord):
        """
        Given a word from the user, iterate over the real word and check every letter, then assign colors based on it.
        """
        # Check the board status to see if we need to stop the game
        self.checkBoardStatus()

        # Initialize the word that will be checked for correctness, by casting it to a Word object
        # Cast the solution word to a list of characters
        display_word = Word(guessedWord)
        solution = list(self.solution)

        # --- Wordle logic ---  
        # Green if the letter is correct, yellow if the letter is present in the word, and gray if it's not
        # Initialize a counter of frequencies of the letters
        # If a letter is correct (green), remove 1 from the frequencies
        # If another letter is then present, it means it will be yellow
        pool = Counter(solution)
        # print(f"Pool: {pool}")
        for idx, char in enumerate(solution):
            if display_word[idx].char == char:
                display_word.__setcolor__(idx, "green") 
                pool.subtract(display_word[idx].char)                    
        for idx, char in enumerate(solution):
            if display_word[idx].color != "green":
                if pool[display_word[idx].char] > 0:
                    display_word.__setcolor__(idx, "yellow")
                    pool.subtract(display_word[idx].char) 
                else:
                    display_word.__setcolor__(idx, "gray")      

        # Append the word that will need to be displayed, increase the number of attempts
        self.boar_arr[self.num_attempts] = display_word
        self.num_attempts += 1
        self.displayBoard()
        if guessedWord == self.solution:            
            # Game has been won
            self.status = Status.WON
        self.checkBoardStatus()    

    def checkBoardStatus(self):
        if self.status == Status.WON or self.status == Status.LOST:
            self.endGame()
        elif self.status == Status.ONGOING and self.num_attempts >=  self.max_attempts:
            self.status = Status.LOST
            self.endGame()

    def displayBoard(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        color_assign = {
            "green": Fore.GREEN,
            "yellow": Fore.YELLOW,
            "gray": Fore.WHITE,
        }       
        for word_obj in self.boar_arr:
            letters = [char for char in word_obj]
            for lt in letters:
                print(f"{Style.BRIGHT} {Back.BLACK} {color_assign.get(lt.color)} {lt.char.upper()}", end='', sep='')
            print('\n')
            Style.RESET_ALL

    def saveResults(self):
        with open(self.outputFile, 'r') as json_read:
            existing_guesses = json.load(json_read)

        result_dict = {
            "actual_word": self.solution,
            "last_word_guessed": self.boar_arr[self.num_attempts - 1].__str__(),
            "result": str(self.status.value),
            "num_attempts": self.num_attempts,
            "date": datetime.today().strftime('%Y-%m-%d')
        }        
        existing_guesses.append(result_dict)

        try: 
            with open(self.outputFile, 'w') as json_out:
                json.dump(existing_guesses, json_out)
        except Exception as e:
            print(f"Encountered an error when saving the JSON result file: {e}")
        
    def endGame(self):
        if self.status == Status.LOST:
            print(f"You have lost! The correct word was {self.solution.upper()}.")
        elif self.status == Status.WON:    
            endstr = '' if self.num_attempts == 1 else 's'        
            print(f"Well done! You correctly guessed the words in {self.num_attempts} attempt{endstr}.")        
        self.saveResults()
        sys.exit(0)        

    def startGame(self):
        while self.status == Status.ONGOING:
            cond = False
            while(not cond):                
                guessed_word = input(f"Enter your guess (Num attempts: {self.num_attempts}): ").lower()
                if len(guessed_word) != self.sol_lenght or not guessed_word.isalpha() or not guessed_word in self.all_words:
                    print(f"The word has to be valid, alphanumeric and of lenght {self.sol_lenght}!")
                else:
                    cond = True     
            self.guessWord(guessed_word)

# While the lenght of the input word that is entered by the user is different than 5, keep looping