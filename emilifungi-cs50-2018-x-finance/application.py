import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
from passlib.context import CryptContext
from datetime import datetime
import math

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    portfolio = db.execute("SELECT * FROM portfolio WHERE id = :user_id", user_id = session.get("user_id"))
    cash = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id = session.get("user_id"))[0].get("cash")
    total = cash
    stocks = []
    prices = []
    stock_tot = []
    for i in portfolio:
        total += (lookup(i.get("symbol")).get("price") * i.get("shares"))
        stocks.append(i)
        prices.append(usd(lookup(i.get("symbol")).get("price")))
        stock_tot.append(usd(lookup(i.get("symbol")).get("price") * i.get("shares")))
    length = len(stocks)
    return render_template("index.html", length = length, cash = usd(cash), stock_tot = stock_tot,
                            portfolio = portfolio, total = usd(total), prices = prices, stocks = stocks)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure stock symbol was submitted
        if not request.form.get("symbol"):
            return apology("must provide symbol", 400)

        # Ensure valid symbol was entered
        elif not lookup(request.form.get("symbol")):
            return apology("enter valid symbol", 400)

        # Ensure shares was submitted
        elif not request.form.get("shares"):
            return apology("must enter number of shares", 400)

        elif request.form.get("shares").isalpha():
            return apology("enter a valid number", 400)

        # Ensure shares is valid
        elif math.trunc(float(request.form.get("shares"))) <= 0 or math.floor(float(request.form.get("shares"))) != math.ceil(float(request.form.get("shares"))):
            return apology("enter a valid number", 400)

        cash = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id = session.get("user_id"))
        quote = lookup(request.form.get("symbol"))
        symbols = db.execute("SELECT symbol FROM portfolio WHERE id = :user_id", user_id = session.get("user_id"))

        # Ensure user has enough funds
        if float(cash[0].get("cash")) < (float(quote.get("price")) * int(request.form.get("shares"))):
            return apology("not enough funds", 400)

        # Update cash total if they can afford
        else:
            db.execute("UPDATE users SET cash = cash - :total WHERE id = :user_id",
                        total = float(quote.get("price")) * int(request.form.get("shares")), user_id = session.get("user_id"))
            result = []
            result.append(db.execute("SELECT symbol, shares FROM portfolio WHERE id = :user_id and symbol = :symb",
                            user_id = session.get("user_id"), symb = quote.get("symbol")))

            db.execute("INSERT INTO 'history' ('symbol', 'shares', 'price', 'transacted', 'id') VALUES (:s, :sh, :p, :d, :user_id)",
                        s = quote.get("symbol"), sh = request.form.get("shares"), p = quote.get("price"),
                        d = datetime.today(), user_id = session.get("user_id"))

            if len(result[0]) != 0:
                share = int(result[0][0].get("shares"))
                db.execute("UPDATE portfolio SET shares = shares + :num WHERE id = :user_id and symbol = :symb",
                            num = int(request.form.get("shares")), user_id = session.get("user_id"), symb = quote.get("symbol"))
            else:
                db.execute("INSERT INTO 'portfolio' ('id', 'symbol', 'name', 'shares') VALUES (:user_id, :symbol, :name, :shares )", user_id = session.get("user_id"),
                            symbol = quote.get("symbol"), name = quote.get("name"), shares = int(request.form.get("shares")))
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    history = db.execute("SELECT * FROM history WHERE id = :user_id", user_id = session.get("user_id"))
    prices = []
    shares = []
    dates = []
    symbols = []
    for i in history:
        prices.append(usd(i.get("price")))
        shares.append(i.get("shares"))
        dates.append(i.get("transacted"))
        symbols.append(i.get("symbol"))
    length = len(prices)
    return render_template("history.html", prices = prices, dates = dates, symbols = symbols, shares = shares, length = length)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 400)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure symbol was submitted
        if not request.form.get("symbol"):
            return apology("must enter stock symbol", 400)

        elif not lookup(request.form.get("symbol")):
            return apology("invalid symbol", 400)

        quote = lookup(request.form.get("symbol"))

        return render_template("display_quote.html", name = quote.get("name"),
                                symb = quote.get("symbol"), price = usd(quote.get("price")))

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords do not match", 400)

        hash_pwd = generate_password_hash(request.form.get("password"))

        # Query database for username
        result = db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)",
                            username=request.form.get("username"), hash = hash_pwd)
        if not result:
            return apology("username already exists", 400)

        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    symbols = db.execute("SELECT symbol FROM portfolio where id = :user_id", user_id = session.get("user_id"))

    if request.method == "POST":

        to_sell = db.execute("SELECT shares FROM portfolio WHERE id = :user_id and symbol = :s", user_id = session.get("user_id"), s = request.form.get("symbol"))[0].get("shares")

        if not request.form.get("shares"):

            # Ensure number of shares was sumbitted
            return apology("must provide value", 400)

        elif int(request.form.get("shares")) <= 0:
            return apology("enter valid number", 400)

        elif int(request.form.get("shares")) > to_sell:
            return apology("not enough shares", 400)

        elif request.form.get("symbol") == "":
            return apology("missing symbol", 400)

        else:
            quote = lookup(request.form.get("symbol"))

            db.execute("INSERT INTO 'history' ('symbol', 'shares', 'price', 'transacted', 'id') VALUES (:s, :sh, :p, :d, :user_id)",
                        s = quote.get("symbol"), sh = (0 - int(request.form.get("shares"))), p = quote.get("price"),
                        d = datetime.today(), user_id = session.get("user_id"))

            db.execute("UPDATE users SET cash = cash + :total WHERE id = :user_id", total = int(request.form.get("shares")) * float(quote.get("price")),
                        user_id = session.get("user_id"))
            db.execute("UPDATE portfolio SET shares = shares - :num WHERE id = :user_id and symbol = :s",
                        num = request.form.get("shares"), user_id = session.get("user_id"), s = request.form.get("symbol"))

            if int(request.form.get("shares")) - to_sell == 0:
                db.execute("DELETE FROM portfolio WHERE id = :user_id and symbol = :s", user_id = session.get("user_id"), s = quote.get("symbol"))
            return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("sell.html", symbols=symbols)

def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
