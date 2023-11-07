import json
import os.path
import random
import collections
from datetime import *
from table2ascii import table2ascii
import simplematrixbotlib as botlib


class AntiUwUBot:

    def __init__(self):
        self.creds = botlib.Creds("https://matrix.org", "<<username>>", "<<password>>")
        self.bot = botlib.Bot(self.creds)
        self.PREFIX = "`"
        self.json_path = "./data.json"

        if not os.path.isfile(self.json_path):
            with open(self.json_path, "w") as outfile:
                outfile.write("{}")

        with open(self.json_path) as json_file:
            self.stat_dict = json.load(json_file)

        self.add_commands()

    ''' vvvvvvvvvvvvvvvvvvvvvvvvvvvv Commands vvvvvvvvvvvvvvvvvvvvvvvvvvvv'''
    def add_commands(self):
        @self.bot.listener.on_message_event
        async def bot_help(room, message):
            bot_help_message = f"""
            Help Message:
                prefix: {self.PREFIX}
                Commands:
                    help:
                        command: help
                        description: display help command
                    gamble_coin:
                        command: gamble <amount>, bet <amount>
                        description: Test your luck.
                    get_balance:
                        command: balance
                        description: Show your current balance.
                    show_stats:
                        command: stats
                        description: Show everyone's balances.
                    get_daily_coin:
                        command: daily
                        description: Redeem your daily coin.
                    give:
                        command: give <recipient> <amount>
                        description: Charitable donations.
                    get_401k_losses:
                        command: 401k
                        description: Show total 401k losses :(
                        """
            match = botlib.MessageMatch(room, message, self.bot, self.PREFIX)
            if match.is_not_from_this_bot() and match.prefix() and (match.command("help")):
                await self.bot.api.send_text_message(room.room_id, bot_help_message)

        @self.bot.listener.on_message_event
        async def gamble_coin(room, message):
            match = botlib.MessageMatch(room, message, self.bot, self.PREFIX)
            if match.is_not_from_this_bot() and match.prefix() and (match.command("gamble") or match.command("bet")):
                win_rate = 55  # Percent
                user_name = str(message.sender)
                # Enforce positive integers
                try:
                    if match.args()[0] == '*':
                        amount = self.get_coin_balance(user=user_name)
                    else:
                        amount = abs(int(match.args()[0]))
                    # Check user has enough coin first
                    if self.get_coin_balance(user=user_name) >= amount:
                        roll = random.randint(1, 100)
                        if roll < win_rate:
                            self.add_coin(user=user_name, coins=amount)
                            await self.bot.api.send_text_message(room.room_id, f"{user_name} won {amount} weeb coin!")
                        else:
                            self.remove_coin(user=user_name, coins=amount)
                            await self.bot.api.send_text_message(room.room_id, f"{user_name} lost {amount} weeb coin!")
                    else:
                        await self.bot.api.send_text_message(room.room_id, "You are too poor for that")
                except:
                    await self.bot.api.send_text_message(room.room_id, "Try Again :(")
                    return

        @self.bot.listener.on_message_event
        async def get_balance(room, message):
            match = botlib.MessageMatch(room, message, self.bot, self.PREFIX)
            if match.is_not_from_this_bot() and match.prefix() and (match.command("balance")):
                user_name = str(message.sender)
                amount = self.get_coin_balance(user=user_name)
                await self.bot.api.send_text_message(room.room_id, f"{user_name} has {amount} weebcoin.")

        @self.bot.listener.on_message_event
        async def show_stats(room, message):
            match = botlib.MessageMatch(room, message, self.bot, self.PREFIX)
            if match.is_not_from_this_bot() and match.prefix() and (match.command("stats")):
                try:
                    results = []
                    sorted_entries = collections.OrderedDict(sorted(self.stat_dict.items(), key=lambda t: t[1]['coins'], reverse=True))
                    for name, val_dict in sorted_entries.items():
                        coins = val_dict['coins']
                        results.append([name, coins])

                    output = table2ascii(header=['Name', 'Weebcoins'], body=results)
                    await self.bot.api.send_text_message(room.room_id, output)
                except:
                    await self.bot.api.send_text_message(room.room_id, "Still gathering data..")

        @self.bot.listener.on_message_event
        async def get_daily_coin(room, message):
            match = botlib.MessageMatch(room, message, self.bot, self.PREFIX)
            if match.is_not_from_this_bot() and match.prefix() and (match.command("daily")):
                user_name = str(message.sender)
                if self.eligible_for_daily(user_name):
                    amount = 1000
                    self.add_coin(user=user_name, coins=amount)
                    await self.bot.api.send_text_message(room.room_id, f"{user_name} redeemed {amount} daily weebcoin!")
                else:
                    hours_rem, minutes_rem = self.daily_cd_remaining(user_name)
                    await self.bot.api.send_text_message(room.room_id, f"Please try again in {hours_rem} hours {minutes_rem} minutes")

        @self.bot.listener.on_message_event
        async def give(room, message):
            match = botlib.MessageMatch(room, message, self.bot, self.PREFIX)
            if match.is_not_from_this_bot() and match.prefix() and (match.command("give")):
                try:
                    user_name = str(message.sender)
                    recipient = match.args()[0]
                    donation = match.args()[1]
                    if donation == '*':
                        amount = self.get_coin_balance(user=user_name)
                    else:
                        amount = abs(int(donation))
                except:
                    await self.bot.api.send_text_message(room.room_id, "Please try again")
                    return

                if self.get_coin_balance(user=user_name) >= amount and recipient in self.stat_dict.keys():
                    self.remove_coin(user=user_name, coins=amount)
                    self.add_coin(user=recipient, coins=amount)
                    await self.bot.api.send_text_message(room.room_id, f"{user_name} gave {amount} weebcoin to {recipient}")
                    self.write_to_file()
                else:
                    await self.bot.api.send_text_message(room.room_id, "You are too poor, or they don't exist")

        @self.bot.listener.on_message_event
        async def get_401k_losses(room, message):
            match = botlib.MessageMatch(room, message, self.bot, self.PREFIX)
            if match.is_not_from_this_bot() and match.prefix() and (match.command("401k")):
                cur_day = datetime.now().day
                cur_month = datetime.now().month
                cur_year = datetime.now().year
                date_401k_stopped = date(2023, 2, 1)
                today = date(cur_year, cur_month, cur_day)
                paychecks_since = abs(date_401k_stopped - today).days // 14
                losses_so_far = int(paychecks_since * 225)
                formatted_losses_so_far = '{:,}'.format(int(paychecks_since * 225))
                compounded_losses = losses_so_far * (pow((1 + 0.08 / 1), 1 * 30))
                formatted_compounded_losses = '{:,}'.format(int(compounded_losses))
                await self.bot.api.send_text_message(room.room_id,
                                                     'Total losses so far -${}\nCompounded over the next 30 years, '
                                                     'that\'s -${}!\nFormula: A = P(1 + r/n)^nt\nA = Accrued amount '
                                                     '(principal + interest)\nP = Principal amount ($225/ paycheck '
                                                     'since 401k matching was cancelled)\nr = Annual interest rate '
                                                     '(8% market avg)\nn = Number of compounding periods per unit of '
                                                     'time (1)\nt = Time in decimal years (30)'.format(
                                                         formatted_losses_so_far, formatted_compounded_losses))

    ''' ^^^^^^^^^^^^^^^^^^^^^^^^^^^^ Commands ^^^^^^^^^^^^^^^^^^^^^^^^^^^'''
    def get_coin_balance(self, user):
        self.check_user_exists(user)
        try:
            return self.stat_dict[user]['coins']
        except:
            return 0
        self.write_to_file()

    def add_coin(self, user, coins):
        self.check_user_exists(user)
        self.stat_dict[user]['coins'] += coins  # Check to make sure they have enough
        self.write_to_file()

    def remove_coin(self, user, coins):
        self.check_user_exists(user)
        if self.stat_dict[user]['coins'] - coins < 0:
            self.stat_dict[user]['coins'] = 0
        else:
            self.stat_dict[user]['coins'] -= coins
        self.write_to_file()

    def eligible_for_daily(self, user):
        self.check_user_exists(user)
        seconds_elapsed = (datetime.now() - datetime.strptime(str(self.stat_dict[user]['last_daily']),
                                                              '%m/%d/%Y, %H:%M:%S')).total_seconds()
        print(f"SECONDS: {seconds_elapsed}")
        if seconds_elapsed > 60 * 60 * 24:  # 24 hours
            self.stat_dict[user]['last_daily'] = datetime.now().strftime('%m/%d/%Y, %H:%M:%S')  # Reset timer
            self.write_to_file()
            return True
        return False

    def daily_cd_remaining(self, user):
        if user not in self.stat_dict.keys():
            self.stat_dict[user] = {'coins': 0,
                                    'last_daily': (datetime.now() - timedelta(1)).strftime('%m/%d/%Y, %H:%M:%S')}
        seconds_elapsed = (datetime.now() - datetime.strptime(str(self.stat_dict[user]['last_daily']),
                                                              '%m/%d/%Y, %H:%M:%S')).total_seconds()
        hours, minutes = divmod((60 * 60 * 24 - seconds_elapsed) / 60, 60)
        hours_rem = '{0:.2f}'.format(hours)
        minutes_rem = '{0:.2f}'.format(minutes)
        # print(f"{hours_rem} hours and {minutes_rem} minutes remaining")
        return hours_rem, minutes_rem

    def check_user_exists(self, user):
        # Add user
        if user not in self.stat_dict.keys():
            self.stat_dict[user] = {'coins': 0,
                                    'last_daily': (datetime.now() - timedelta(1)).strftime('%m/%d/%Y, %H:%M:%S')}

    def write_to_file(self):
        with open(self.json_path, 'w') as json_file:
            json.dump(self.stat_dict, json_file)


uwu_inst = AntiUwUBot()
uwu_inst.bot.run()
