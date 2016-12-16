from decimal import Decimal
import getpass


class Accounts(object):
    def __init__(self, rows):
        self.rows = list(rows)

    def exists(self, number):
        return number in [
            number for number, pin in self.rows
        ]

    def pin(self, account_number):
        pins = [
            pin.strip()
            for number, pin
            in self.rows
            if number == account_number
        ]
        return pins[0]

    def for_(self, number):
        if self.exists(number):
            pin = self.pin(number)
            return UnauthenticatedAccount(number, pin)
        return UnknownAccount()


class UnauthenticatedAccount(object):
    def __init__(self, number, pin):
        self.number = number
        self.pin = pin

    def validate(self):
        return self

    def authenticate(self):
        for _ in range(3):
            print('Please enter PIN. Entry will be hidden.')
            entered_pin = getpass.getpass('Pin: ')
            if entered_pin == self.pin:
                return Account(self.number)
        return LockedAccount()


class UnknownAccount(object):
    def validate(self):
        print("Unknown Account.")
        exit()


class Account(object):
    def __init__(self, number):
        self.number = number

    def act(self, choice):
        choice.act(self)

    def authenticate(self):
        return self


class LockedAccount(object):
    def act(self, choice):
        print('You failed to authenticate.')
        exit()


class History(object):
    def __init__(self, rows):
        self.rows = list(rows)

    def remember_deposit(self, account_number, amount):
        self.rows.append((account_number, Decimal(amount)))

    def remember_withdraw(self, account_number, amount):
        self.rows.append((account_number, -1 * Decimal(amount)))

    def transactions(self, account_number):
        return [(number, Decimal(amount))
                for number, amount
                in self.rows
                if number == account_number
                ]

    def save(self):
        lines = ['%s,%s' % row for row in self.rows]
        content = '\n'.join(lines)
        with open('history.txt', 'w') as file_:
            file_.write(content)


class Deposit(object):
    def __init__(self, history):
        self.history = history

    def act(self, account):
        print('Deposit')
        amount = input('Amount: ')
        amount = Decimal(amount)
        history.remember_deposit(account.number, amount)


class Withdraw(object):
    def __init__(self, history):
        self.history = history

    def act(self, account):
        print('Withdraw')
        amount = input('Amount: ')
        amount = Decimal(amount)
        history.remember_withdraw(account.number, amount)


class Balance(object):
    def __init__(self, history):
        self.history = history

    def act(self, account):
        print("Balance")
        balance = sum(
            amount
            for number, amount
            in self.history.transactions(
                account.number
            )
        )
        print(balance)


class Report(object):
    def __init__(self, history):
        self.history = history

    def report_line(self, amount):
        if amount < Decimal(0.0):
            return '%s Withdraw' % (amount * Decimal(-1))
        return '%s Deposit' % amount

    def act(self, account):
        print('Report')
        lines = [
            self.report_line(amount)
            for number, amount
            in self.history.transactions(
                account.number
            )
        ]
        print('\n'.join(lines))


class Quit(object):
    def __init__(self, history):
        self.history = history

    def act(self, account):
        self.history.save()
        print('Thank you for using Heidelberg Student Bank services')
        exit()


class Choice(object):
    def act(self, account):
        pass

    @classmethod
    def ask(self, history):
        choice = input("Select: ").lower()

        if choice.strip() not in 'bdwrq':
            return Choice()

        if choice == 'b':
            return Balance(history)

        if choice == 'd':
            return Deposit(history)

        if choice == 'w':
            return Withdraw(history)

        if choice == 'r':
            return Report(history)

        if choice == 'q':
            return Quit(history)


class File(object):
    def __init__(self, path):
        self.path = path

    def lines(self):
        with open(self.path) as file_:
            for line in file_:
                yield line.strip()


class Table(object):
    def __init__(self, file):
        self.file = file

    def rows(self):
        for line in self.file.lines():
            yield tuple(line.split(','))


class Session(object):
    def __init__(self, account, history):
        self.account = account
        self.history = history

    def menu(self):
        print("Menu")
        print("(B)alance (D)eposit (W)ithdraw (R)eport (Q)uit")

    def run(self):
        self.menu()
        choice = Choice.ask(self.history)

        self.account = self.account.authenticate()

        self.account.act(choice)


class Atm(object):
    def __init__(self, accounts, history):
        self.accounts = accounts
        self.history = history

    def header(self):
        print('***********************')
        print('Heidelberg Student Bank')
        print('***********************')

    def run(self):
        self.header()

        account_number = input('Account Number: ')
        account = self.accounts.for_(account_number)
        account = account.validate()

        self.session = Session(account, self.history)
        while True:
            self.session.run()


if __name__ == '__main__':
    accounts = Accounts(
        Table(
            File('accounts.txt')
        ).rows()
    )
    history = History(
        Table(
            File('history.txt')
        ).rows()
    )

    Atm(accounts, history).run()
