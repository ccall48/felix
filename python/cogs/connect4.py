"""This is a cog for a discord.py bot.
It will provide a connect4 type game for everyone to play.
"""

from discord.ext import commands
from discord import Member, Embed, Message

COLUMN_EMOJI = ('1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣')
TOKEN = {
    0: '⚫',
    1: '🔴',
    2: '⚪',
}
P1_COLOR = 'red'
P2_COLOR = 'white'


class Connect4Engine:
    MOVE_ACCEPTED = 0
    PLAYER1_WINNER = 1
    PLAYER2_WINNER = 2
    INVALID_MOVE = 3
    WRONG_PLAYER = 4
    DRAW = 5

    def __init__(self, player1, player2):
        self.player1 = player1
        self.player2 = player2
        self.state = [0] * 6 * 7

    @property
    def next_turn(self):
        return self.player1 if self.state.count(0) % 2 == 0 else self.player2

    def print_state(self):
        for i in range(6):
            print(self.state[i * 7:(i + 1) * 7])

    def play_move(self, player, column):
        # Wrong player
        if self.next_turn != player:
            return Connect4Engine.WRONG_PLAYER

        # Invalid Column
        if not 1 <= column <= 7:
            return Connect4Engine.INVALID_MOVE

        # Column full
        if self.state[column - 1]:
            return Connect4Engine.INVALID_MOVE

        return self.apply_move(player, column)

    def apply_move(self, player, column):
        next_empty = self.find_next_empty(column)
        self.state[next_empty] = 1 if player == self.player1 else 2
        winning_move = self.check_4_in_a_row(next_empty)
        # self.print_state()
        if winning_move:
            if player == self.player1:
                return Connect4Engine.PLAYER1_WINNER
            else:
                return Connect4Engine.PLAYER2_WINNER
        else:
            if self.state.count(0) == 0:
                return Connect4Engine.DRAW
            else:
                return Connect4Engine.MOVE_ACCEPTED

    def check_4_in_a_row(self, last_added):
        target_value = self.state[last_added]
        for direction in [1, 6, 7, 8]:
            in_a_row = 1

            current = last_added + direction
            while 0 <= current <= 41:
                if self.state[current] != target_value:
                    break
                in_a_row += 1
                current += direction

            direction *= -1
            current = last_added + direction
            while 0 <= current <= 41:
                if self.state[current] != target_value:
                    break
                in_a_row += 1
                current += direction

            if in_a_row >= 4:
                return True

        return False

    def find_next_empty(self, column):
        current = column - 1
        while True:
            if current + 7 > 41:
                break
            if self.state[current + 7]:
                break
            current += 7
        return current


class Connect4Game():
    MOVE_ACCEPTED = 0
    PLAYER1_WINNER = 1
    PLAYER2_WINNER = 2
    INVALID_MOVE = 3
    WRONG_PLAYER = 4
    DRAW = 5

    def __init__(self, player1: Member, player2: Member):
        self.player1 = player1
        self.player2 = player2
        self.engine = Connect4Engine(player1.id, player2.id)

    @property
    def next_turn(self):
        return self.engine.next_turn

    def play_move(self, player, column):
        return self.engine.play_move(player.id, column)

    def get_embed(self, custom_footer=False):
        next_up = self.player1 if self.next_turn == self.player1.id else self.player2

        title = f'Connect 4: {self.player1.display_name} VS {self.player2.display_name}'
        content = ''.join(COLUMN_EMOJI) + '\n'

        for line in range(6):
            line_state = self.engine.state[line*7:(line+1)*7]
            content += ''.join(TOKEN[x] for x in line_state) + '\n'

        e = Embed(
            title=title,
            description=content,
            color=0x2ECC71,
        )
        if custom_footer:
            e.set_footer(text=custom_footer)
        else:
            color = P1_COLOR if next_up == self.player1 else P2_COLOR
            e.set_footer(text=f'Next Up: {next_up.display_name} ({color})')

        return e


class Connect4(commands.Cog, name='Connect4'):
    def __init__(self, client):
        self.client = client
        self.waiting_games = dict()
        self.active_games = dict()

    async def start_game(self, player1: Member, player2: Member, message: Message):
        await message.clear_reactions()
        await message.edit(content='Loading ....')
        for emoji in COLUMN_EMOJI:
            await message.add_reaction(emoji)
        game = Connect4Game(player1, player2)
        self.active_games[message.id] = (game, message)
        await message.edit(content=None, embed=game.get_embed())

    async def finish_game(self, game, message, result):
        await message.clear_reactions()
        if result == game.DRAW:
            footer = 'The game was a draw!!'
        elif result == game.PLAYER1_WINNER:
            footer = f'{game.player1.display_name} has won the game'
        elif result == game.PLAYER2_WINNER:
            footer = f'{game.player2.display_name} has won the game'

        await message.edit(embed=game.get_embed(custom_footer=footer))
        del self.active_games[message.id]

    @commands.command(
        name='connect4',
        aliases=['c4'],
    )
    async def connect4(self, ctx):
        """Start a game of Connect 4"""
        msg = await ctx.send(
            f'{ctx.author.display_name} wants to start a game of Connect 4\n'
            'react with 🆗 to join!'
            )
        await msg.add_reaction('🆗')
        self.waiting_games[msg.id] = (msg, ctx.author)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.id == self.client.user.id:
            return
        if reaction.message.id in self.waiting_games:
            message, player1 = self.waiting_games[reaction.message.id]
            if reaction.emoji != '🆗' or user.id == player1.id:
                await message.remove_reaction(reaction.emoji, user)
                return

            player2 = user
            del self.waiting_games[reaction.message.id]
            await self.start_game(player1, player2, message)
            return

        elif reaction.message.id in self.active_games:
            game, message = self.active_games[reaction.message.id]
            next_up = game.next_turn
            if next_up != user.id:
                await message.remove_reaction(reaction.emoji, user)
                return

            result = game.play_move(user, COLUMN_EMOJI.index(reaction.emoji) + 1)
            if result in (game.PLAYER1_WINNER, game.PLAYER2_WINNER, game.DRAW):
                await self.finish_game(game, message, result)
            elif result == 0:
                await message.edit(embed=game.get_embed())

        await message.remove_reaction(reaction.emoji, user)


def setup(client):
    """This is called when the cog is loaded via load_extension"""
    client.add_cog(Connect4(client))