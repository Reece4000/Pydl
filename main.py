import tkinter as tk
from tkinter import ttk
import random
import sqlite3 as sq
from datetime import date, datetime
import time

# ------------------------------------------------------------
# CONSTANTS
with open('words.txt') as f:
    words = f.read()
LEGAL_WORDS = words.split('\n', 1)[0]
GOAL_WORDS = words.split('\n', 1)[1]
GOAL_WORDS_ARRAY = GOAL_WORDS.split()
FULL_WORD_ARRAY = (LEGAL_WORDS + GOAL_WORDS).split()
EVAL_LTRS = {
    None: "#ffdd7d",  # init colour for qwerty keyboard
    0: "#d44c4c",  # letter not found in word
    1: "#4ed433",  # letter found at correct pos
    2: "#ffe505",  # letter found at incorrect pos
    3: "#988e67",  # dark grey
    4: "#d9cc96"   # light grey
}
QWERTY = "QWERTYUIOPASDFGHJKLZXCVBNM⏎␡"
FNT = 'consolas'
BLD = 'bold'
MAIN_BG = "#fcba03"
BTN_COL = "#ffdd7d"
BTN_FG = "#4d4b46"
HILITE = "#ffc930"
TXT_COL = "#2e2201"
MSG = {  # added numbers represent pauses when the text is drawn
    0: "2unlucky.",
    1: "3OK, not bad.",
    2: "4great.",
    3: "3brilliant.",
    4: "3impressive, 2very nice.",
    5: "4wow - nice work.",
    6: "6:O !!!"
}
GREETINGS = [  # added numbers represent pauses when the text is drawn
    "hey!",
    "how's it going?",
    "welcome to pydl!",
    "hi1.1.1.1 1literacy is important!",
    "oh1.1.1.1 2hey1.1.1.1",
    "good day!",
    "well hello!",
    "hi there!",
    "oh, hi1.1.1.1 2didn't see you there!",
    "what's up?",
    "the name's1.1.1.1 2pydl."
]


def format_time(time):
    if len(str(int(time) % 60)) < 2:
        secs = '0' + str(int(time) % 60) + 's'
    else:
        secs = str(int(time) % 60) + 's'
    return str(int(time / 60)) + 'm ' + secs


class PydlDatabase:
    def __init__(self, db_name):
        self.db_name = db_name
        self.CREATE_QUERY = ("CREATE TABLE IF NOT EXISTS Leaderboard "
                             "(initials TEXT, "
                             "date TEXT, "
                             "guessnum INTEGER, "
                             "timetaken INTEGER, "
                             "word TEXT)")

    def sql_query(self, query, return_records=False):
        """ Run SQL query, with the option to return the results to the calling code as a list. """
        connection = sq.connect(self.db_name)  # create/connect to db
        cursor = connection.cursor()  # create a cursor object
        cursor.execute(query)
        records = cursor.fetchall()
        connection.commit()  # commit to database
        connection.close()  # close connection to database
        if return_records:
            return records


class GameState:
    def __init__(self, db):
        self.db = db
        self.found = [None for _ in range(28)]
        self.guesses = [[' ' for col in range(5)] for row in range(6)]
        self.guess_num = 0
        self.goal_word = random.choice(GOAL_WORDS_ARRAY).upper()
        self.won = False
        self.time_start = 0
        self.time_taken = 0
        self.eval_grid = [[None for x in range(5)] for y in range(6)]
        self.resigned = False
        print(self.goal_word)

    def logic(self, app):
        if self.won:
            # data = ["name", "date", "time", "time taken"]
            data = [app.entry.get().upper(),
                    str(date.today().strftime("%d/%m/%y")),
                    self.guess_num,
                    int(self.time_taken)]
            self.db.sql_query("INSERT INTO Leaderboard (initials, date, guessnum, timetaken, word) "
                              "VALUES("
                              "'" + data[0] + "', " +  # initials
                              "'" + data[1] + "', " +  # date
                              str(data[2]) + ", " +  # guesses
                              str(data[3]) + ", " +  # time taken
                              "'" + self.goal_word + "');")  # word
            time_str = format_time(data[3])
            app.entry.delete(0, tk.END)
            app.new_game(greet=False)
            guess_str = str(data[2]) + " guesses!" if self.guess_num > 1 else str(data[2]) + " guess!"
            app.update_tip(str(data[0]) + " got it in " + time_str + " with " + guess_str, pauses=False)
            app.timelabel.reset()
            self.won = False
        elif self.guess_num == 6 and not self.won:
            app.entry.delete(0, tk.END)
            app.update_tip("Press NEW to start a new game.")
        else:
            guess = app.get_guess()
            if not guess:
                return
            self.eval_guess()
            evaluated_array = self.eval_grid[self.guess_num]
            points = (evaluated_array.count(1) * 2) + evaluated_array.count(2)
            msg = MSG[6] if points > 6 else MSG[points]
            app.redraw()
            if evaluated_array.count(1) == 5:
                self.won = True
                if not self.guess_num == 0:
                    self.time_taken = app.timelabel.counter
                app.update_tip("you did it!2 enter your initials:")
                app.timelabel.running = False
            elif self.guess_num == 5:
                app.update_tip("you failed1.1.1.2 '" + self.goal_word + "' was the word.")
                app.timelabel.running = False
            else:
                app.update_tip(guess + "... " + msg)
                if self.guess_num == 0:
                    self.time_start = time.perf_counter()
                    app.timelabel.start()
            self.guess_num += 1

    def eval_guess(self):
        word_arr = [*(self.goal_word.upper())]
        match_array = [0, 0, 0, 0, 0]
        guess = self.guesses[self.guess_num]
        for i in range(len(guess)):  # check for full matches
            qwerty_index = QWERTY.find(guess[i].upper())
            if guess[i] == word_arr[i]:
                match_array[i] = 1
                self.found[qwerty_index] = 1
                word_arr[i] = '#'
        for i in range(len(guess)):  # check for positionally incorrect matches
            qwerty_index = QWERTY.find(guess[i].upper())
            if guess[i] in word_arr:
                if match_array[i] != 1:
                    index = word_arr.index(guess[i])
                    match_array[i] = 2
                    word_arr[index] = '#'
                    if self.found[qwerty_index] != 1:
                        self.found[qwerty_index] = 2
            else:
                if self.found[qwerty_index] != 1 and self.found[qwerty_index] != 2:
                    self.found[qwerty_index] = 0
        self.eval_grid[self.guess_num] = match_array

    def give_up(self, app):
        app.update_tip(".1.1.1 8better luck next time.")
        app.timelabel.running = False
        for row in range(6):
            if row < self.guess_num:
                self.eval_grid[row] = [3 for col in range(5)]
            if row >= self.guess_num:
                self.guesses[row] = ["😔" for col in range(5)] # 😔
                self.eval_grid[row] = [3 for col in range(5)]
            if row == 5:
                self.guesses[row] = [self.goal_word[col] for col in range(5)]  # 😔
                self.eval_grid[row] = [4 for col in range(5)]
        for letter in range(28):
            if QWERTY[letter] in self.goal_word:
                self.found[letter] = 4
            else:
                self.found[letter] = 3
        self.guess_num = 6
        app.redraw()


class Timer:
    def __init__(self, frame):
        self.counter = 0
        self.time_str = datetime.fromtimestamp(self.counter).strftime("0m 00s")
        self.mFrame = frame
        self.watch = tk.Label(self.mFrame, text=self.time_str, font=(FNT, 13, BLD), bg=MAIN_BG,
                              bd=0, fg=TXT_COL, anchor=tk.E)
        self.watch.pack()
        self.running = False

    def start(self):
        self.running = True

        def count():
            if self.running:
                self.watch['text'] = format_time(self.counter)
                self.watch.after(200, count)
                self.counter += 0.2
        count()

    def reset(self):
        self.counter = 0
        self.watch['text'] = "0m 00s"
        self.running = False


class App(tk.Tk):
    def __init__(self, game):
        super().__init__()
        self.title('Pydl')
        self.geometry("520x800")
        self.game = game
        self.main_window = None
        self.scoreboard = None
        try:
            self.iconbitmap("pencil.ico")
        except:
            pass
        self.configure(bg=MAIN_BG)
        self.style = ttk.Style()  # add styling
        self.style.theme_use('clam')  # add theme
        self.title = tk.LabelFrame(self, bg=MAIN_BG, padx=20, pady=0, bd=0)
        self.title.pack(pady=15)
        self.title_text = tk.Label(self.title, text="🐍ⓓⓛ", font=(FNT, 36, 'bold'), bg=MAIN_BG, fg=TXT_COL)
        self.title_text.grid(row=1, column=1)
        self.pydle = tk.LabelFrame(self, bg=MAIN_BG, padx=0, pady=0, bd=3)

        self.reset_btn = tk.Button(self, text="NEW   ", font=(FNT, 12, BLD), bg=MAIN_BG, bd=0, fg=TXT_COL,
                                   command=lambda: self.new_game(), anchor=tk.CENTER,
                                   highlightthickness=0, relief='ridge')
        self.reset_btn.place(x=0, y=0)
        self.ldrboard_btn = tk.Button(self, text="SCORES", font=(FNT, 12, BLD), bg=MAIN_BG, bd=0, fg=TXT_COL,
                                      command=lambda: self.toggle_leaderboard(), anchor=tk.CENTER,
                                      highlightthickness=0, relief='ridge')
        self.ldrboard_btn.place(x=0, y=30)
        self.end_btn = tk.Button(self, text="RESIGN", font=(FNT, 12, BLD), bg=MAIN_BG, bd=0, fg=TXT_COL,
                                 command=lambda: self.game.give_up(self), anchor=tk.CENTER,
                                 highlightthickness=0, relief='ridge')
        self.end_btn.place(x=0, y=60)

        self.timer_canvas = tk.Canvas(self, width=100, height=80, bg=MAIN_BG, bd=0, highlightthickness=0)
        self.timer_canvas.place(x=375, y=70)
        self.timelabel = Timer(self.timer_canvas)
        self.pydle.pack()

        self.button_frame = tk.Canvas(self, bd=0, bg=MAIN_BG)
        self.button_frame.pack(pady=0)

        self.tip_canvas = tk.Canvas(self, width=500, height=40, bg=MAIN_BG, bd=0, highlightthickness=0, relief='ridge')
        self.tip_canvas.pack(pady=15)
        self.tip = self.tip_canvas.create_text(250, 20, text='', anchor=tk.CENTER, font=(FNT, 18, BLD))

        self.entry_frame = tk.LabelFrame(self, bg=MAIN_BG, bd=0)
        self.entry_frame.pack()
        self.entry = tk.Entry(self.entry_frame, bg=HILITE, font=(FNT, 36, BLD), width=13, justify=tk.CENTER, bd=3)
        self.entry.pack(padx=10, pady=0)

        self.cmd_btn_frame = tk.LabelFrame(self, bd=0, bg=MAIN_BG)
        self.cmd_btn_frame.pack()

        self.clr_btn = tk.Button(self.cmd_btn_frame, text="CLEAR", font=(FNT, 12, BLD), bd=2, bg=HILITE, fg=TXT_COL,
                                 width=12, command=lambda: self.send_btn(27))
        self.enter_btn = tk.Button(self.cmd_btn_frame, text="ENTER", font=(FNT, 12, BLD), bd=2, bg=HILITE, fg=TXT_COL,
                                   width=12, command=lambda: self.game.logic(self))
        self.clr_btn.pack(side=tk.LEFT, padx=20, pady=10)
        self.enter_btn.pack(side=tk.RIGHT, padx=20, pady=10)
        self.entry.focus()

        self.qwerty_frame = tk.Canvas(self, bg=MAIN_BG, bd=0, highlightthickness=0, relief='ridge')
        self.qwerty_frame.pack(pady=15)
        self.entry.bind('<Return>', lambda x=None: self.game.logic(self))
        self.redraw()
        self.update_tip(random.choice(GREETINGS))

    def update_tip(self, tip_str, pauses=True):
        delta = 20
        delay = 0
        for x in range (len(tip_str)+1):
            sleep = 0
            t = tip_str[:x]
            if pauses and len(t) > 1:
                if t[-1].isdigit():
                    sleep = int(t[-1])*50
                    t = t[:-1]
                    tip_str = tip_str[:len(t)] + tip_str[len(t)+1:]
            new = lambda t=t: self.tip_canvas.itemconfigure(self.tip, text=t)
            self.tip_canvas.after(delay+sleep,new)
            delay += delta + sleep

    def new_game(self, greet=True):
        self.timelabel.reset()
        self.entry.delete(0, tk.END)
        self.game = GameState(self.game.db)
        self.redraw()
        if greet:
            self.update_tip(random.choice(GREETINGS))

    def redraw(self):
        self.ldrboard_btn['text'] = "SCORES"
        self.draw_main_panel()
        self.draw_qwerty()

    def draw_main_panel(self):
        if self.button_frame is not None:
            for button in self.button_frame.winfo_children():
                button.destroy()
        border = 4
        self.btn = [[None for col in range(5)] for row in range(6)]  # 6 = rows; 5 = cols
        for row in range(6):
            for col in range(5):
                colour = EVAL_LTRS[self.game.eval_grid[row][col]]
                ltr = " " + self.game.guesses[row][col] + " "
                self.btn[row][col] = tk.Button(self.button_frame, text=ltr, font=(FNT, 19, BLD),
                                               bd=border, bg=colour, fg=TXT_COL, width=4, height=1)
                self.btn[row][col].grid(column=col, row=row)

    def send_btn(self, x):
        if x == 27:
            self.entry.delete(0, tk.END)
            self.entry.focus()
        elif x == 26:
            self.game.logic(self)
            self.entry.focus()
        else:
            self.entry.insert(tk.END, QWERTY[x])

    def get_guess(self):
        guess = self.entry.get().upper()
        if len(guess) != 5:
            self.update_tip("five letter words, 1please.")
            self.entry.delete(0, tk.END)
            return False
        if guess.lower() not in FULL_WORD_ARRAY:
            self.update_tip("'" + guess + "' is not a valid word.")
            self.entry.delete(0, tk.END)
            return False
        self.game.guesses[self.game.guess_num] = [*(self.entry.get().upper())]
        self.entry.delete(0, tk.END)
        return guess

    def draw_qwerty(self):
        for button in self.qwerty_frame.winfo_children():
            button.destroy()
        self.top_row = tk.LabelFrame(self.qwerty_frame, bg=TXT_COL)
        self.second_row = tk.LabelFrame(self.qwerty_frame, bg=TXT_COL)
        self.third_row = tk.LabelFrame(self.qwerty_frame, bg=TXT_COL)
        self.top_row.pack()
        self.second_row.pack()
        self.third_row.pack()
        qwerty = 0
        self.btn = [0 for x in range(28)]
        for x in range(27):
            ltr = " " + QWERTY[qwerty]
            col = EVAL_LTRS[self.game.found[x]]
            if x < 10:
                frame = self.top_row
                current_row = 0
            elif x < 19:
                frame = self.second_row
                current_row = 1
            elif x < 27:
                frame = self.third_row
                current_row = 2
            self.btn[x] = tk.Button(frame, text=ltr, font=(FNT, 14, BLD), bd=6,
                                    bg=col, fg=TXT_COL, command=lambda x=x: self.send_btn(x))
            self.btn[x].grid(column=x, row=current_row)
            qwerty += 1

    def display_time(self):
        pass

    def toggle_leaderboard(self):
        if self.ldrboard_btn['text'] == "BACK  ":
            self.ldrboard_btn['text'] = "SCORES"
            self.draw_main_panel()
            self.update_tip("hello again!")
        else:
            self.ldrboard_btn['text'] = "BACK  "
            self.prev_tip = self.tip_canvas.itemcget(self.tip, 'text')
            self.update_tip("this is the pydl leaderboard.")
            headers = ['INITIALS', 'DATE', 'ATTEMPTS', 'TIME', 'WORD']
            if self.button_frame is not None:
                for button in self.button_frame.winfo_children():
                    button.destroy()
            border = 4
            records = self.game.db.sql_query("SELECT * FROM "
                                             "(SELECT * FROM Leaderboard "
                                             "ORDER BY timetaken) ORDER BY guessnum", True)

            self.leaderboard_headers = [0 for x in range(5)]
            for x in range(5):
                self.leaderboard_headers[x] = tk.Button(self.button_frame, text=headers[x], font=(FNT, 10, BLD),
                                                        bd=border, bg=HILITE, fg=TXT_COL, width=8, height=1)
                self.leaderboard_headers[x].grid(column=x, row=0)
            self.btn = [[0 for x in range(10)] for y in range(5)]  # 10 rows, 4 cols
            for x in range(10):
                for y in range(5):
                    try:
                        if y == 3:
                            txt = format_time(records[x][y])
                        else:
                            txt = records[x][y]
                    except IndexError:
                        txt = '  '
                    self.btn[y][x] = tk.Button(self.button_frame, text=txt, font=(FNT, 10, BLD),
                                               bd=border, bg=BTN_COL, fg=TXT_COL, width=8, height=1)
                    self.btn[y][x].grid(column=y, row=x + 1)


def run_pydle():
    db = PydlDatabase('Pydle.db')
    db.sql_query(db.CREATE_QUERY)
    game = GameState(db)
    app = App(game)
    app.mainloop()


if __name__ == "__main__":
    run_pydle()
