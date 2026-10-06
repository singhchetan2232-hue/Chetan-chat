from flask import Flask, request, redirect, session, render_template_string
import sqlite3

app = Flask(__name__)
app.secret_key = "chetan_chat_secret"

DATABASE = "chetan_chat_simple.db"


# =========================
# DATABASE
# =========================

def db():
    con = sqlite3.connect(DATABASE)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    con = db()

    con.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    con.commit()
    con.close()


# =========================
# STYLE
# =========================

STYLE = """
<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #f1f3f6;
}

.box {
    width: 90%;
    max-width: 400px;
    margin: 80px auto;
    background: white;
    padding: 25px;
    border-radius: 18px;
    box-shadow: 0 5px 20px #0002;
}

h1 {
    text-align: center;
}

input {
    width: 100%;
    padding: 14px;
    margin: 8px 0;
    border: 1px solid #ddd;
    border-radius: 10px;
    font-size: 16px;
}

button {
    border: none;
    border-radius: 10px;
    background: #222;
    color: white;
    padding: 13px;
    cursor: pointer;
}

.login-button {
    width: 100%;
}

.navbar {
    background: white;
    padding: 16px;
    display: flex;
    justify-content: space-between;
    box-shadow: 0 2px 8px #0001;
}

.users {
    width: 95%;
    max-width: 600px;
    margin: 25px auto;
    background: white;
    padding: 15px;
    border-radius: 15px;
}

.user {
    display: flex;
    align-items: center;
    padding: 15px;
    border-bottom: 1px solid #eee;
    color: #222;
}

.avatar {
    width: 45px;
    height: 45px;
    border-radius: 50%;
    background: #222;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 15px;
}

.chat {
    width: 100%;
    max-width: 650px;
    height: 100vh;
    margin: auto;
    background: white;
    display: flex;
    flex-direction: column;
}

.chat-header {
    padding: 18px;
    border-bottom: 1px solid #ddd;
}

.messages {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
}

.message {
    max-width: 75%;
    padding: 11px 15px;
    margin: 8px 0;
    border-radius: 15px;
    word-wrap: break-word;
}

.sent {
    background: #222;
    color: white;
    margin-left: auto;
}

.received {
    background: #eee;
}

.message-form {
    display: flex;
    padding: 10px;
    border-top: 1px solid #ddd;
}

.message-form input {
    flex: 1;
    margin: 0;
}

.message-form button {
    width: 60px;
    margin-left: 8px;
}

a {
    text-decoration: none;
    color: inherit;
}

.logout {
    color: red;
}

</style>
"""


# =========================
# USERNAME PAGE
# =========================

USERNAME_PAGE = """
<!DOCTYPE html>
<html>
<head>
<title>Chetan Chat</title>
""" + STYLE + """
</head>

<body>

<div class="box">

<h1>💬 Chetan Chat</h1>

<p style="text-align:center;">
Apna username डालो और chat शुरू करो।
</p>

<form method="POST">

<input
type="text"
name="username"
placeholder="Enter username"
maxlength="30"
required
>

<button class="login-button" type="submit">
Continue
</button>

</form>

</div>

</body>
</html>
"""


# =========================
# HOME PAGE
# =========================

HOME_PAGE = """
<!DOCTYPE html>
<html>
<head>
<title>Chetan Chat</title>
""" + STYLE + """
</head>

<body>

<div class="navbar">

<strong>💬 Chetan Chat</strong>

<div>
{{ username }}
&nbsp; | &nbsp;
<a class="logout" href="/logout">Exit</a>
</div>

</div>


<div class="users">

<h2>People</h2>

{% if users %}

{% for user in users %}

<a href="/chat/{{ user.id }}">

<div class="user">

<div class="avatar">
{{ user.username[0].upper() }}
</div>

<div>

<strong>{{ user.username }}</strong>

<br>

<small>
Tap to chat
</small>

</div>

</div>

</a>

{% endfor %}

{% else %}

<p>
अभी कोई दूसरा user नहीं है।
दूसरे browser/device से दूसरा username बनाकर test कर सकते हो।
</p>

{% endif %}

</div>

</body>
</html>
"""


# =========================
# CHAT PAGE
# =========================

CHAT_PAGE = """
<!DOCTYPE html>
<html>

<head>

<title>
{{ other.username }}
</title>

""" + STYLE + """

</head>

<body>

<div class="chat">

<div class="chat-header">

<a href="/">
←
</a>

&nbsp;&nbsp;

<strong>
{{ other.username }}
</strong>

</div>


<div class="messages">

{% for msg in messages %}

{% if msg.sender_id == session["user_id"] %}

<div class="message sent">
{{ msg.message }}
</div>

{% else %}

<div class="message received">
{{ msg.message }}
</div>

{% endif %}

{% endfor %}

</div>


<form method="POST" class="message-form">

<input
type="text"
name="message"
placeholder="Type a message..."
maxlength="1000"
autocomplete="off"
required
>

<button type="submit">
➤
</button>

</form>

</div>

</body>
</html>
"""


# =========================
# START / USERNAME
# =========================

@app.route("/", methods=["GET", "POST"])
def start():

    if "user_id" in session:
        return redirect("/home")

    if request.method == "POST":

        username = request.form["username"].strip()

        if len(username) < 2:
            return "Username कम से कम 2 characters का होना चाहिए।"

        con = db()

        user = con.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        if user is None:

            try:

                con.execute(
                    "INSERT INTO users(username) VALUES (?)",
                    (username,)
                )

                con.commit()

                user = con.execute(
                    "SELECT * FROM users WHERE username = ?",
                    (username,)
                ).fetchone()

            except sqlite3.IntegrityError:

                user = con.execute(
                    "SELECT * FROM users WHERE username = ?",
                    (username,)
                ).fetchone()

        session["user_id"] = user["id"]
        session["username"] = user["username"]

        con.close()

        return redirect("/home")

    return render_template_string(USERNAME_PAGE)


# =========================
# HOME
# =========================

@app.route("/home")
def home():

    if "user_id" not in session:
        return redirect("/")

    con = db()

    users = con.execute(
        """
        SELECT id, username
        FROM users
        WHERE id != ?
        ORDER BY username
        """,
        (session["user_id"],)
    ).fetchall()

    con.close()

    return render_template_string(
        HOME_PAGE,
        username=session["username"],
        users=users
    )


# =========================
# CHAT
# =========================

@app.route("/chat/<int:user_id>", methods=["GET", "POST"])
def chat(user_id):

    if "user_id" not in session:
        return redirect("/")

    con = db()

    other = con.execute(
        """
        SELECT id, username
        FROM users
        WHERE id = ?
        """,
        (user_id,)
    ).fetchone()

    if other is None:
        con.close()
        return "User नहीं मिला।"

    if request.method == "POST":

        message = request.form["message"].strip()

        if message:

            con.execute(
                """
                INSERT INTO messages
                (sender_id, receiver_id, message)
                VALUES (?, ?, ?)
                """,
                (
                    session["user_id"],
                    user_id,
                    message
                )
            )

            con.commit()

        con.close()

        return redirect("/chat/" + str(user_id))

    messages = con.execute(
        """
        SELECT *
        FROM messages
        WHERE
        (sender_id = ? AND receiver_id = ?)
        OR
        (sender_id = ? AND receiver_id = ?)
        ORDER BY id ASC
        """,
        (
            session["user_id"],
            user_id,
            user_id,
            session["user_id"]
        )
    ).fetchall()

    con.close()

    return render_template_string(
        CHAT_PAGE,
        other=other,
        messages=messages
    )


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# =========================
# RUN
# =========================

if __name__ == "__main__":

    init_db()

    print("================================")
    print("       CHETAN CHAT")
    print("================================")
    print("Server started")
    print("Open: http://127.0.0.1:5000")
    print("================================")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
