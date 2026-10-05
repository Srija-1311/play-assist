import ast, json, operator, re, sqlite3
from pathlib import Path
from langchain_core.tools import tool

DATA = Path(__file__).parent / "data"
DB = DATA / "players.db"

KB = [
    {"title": "Reset password", "text": "Open Account Settings, choose Security, then Reset Password. A link is emailed and expires in 30 minutes."},
    {"title": "Refund policy", "text": "Digital purchases can be refunded within 14 days of purchase if playtime is under 2 hours."},
    {"title": "Connection issues", "text": "Restart the game, check NAT type is Open or Moderate, and switch to a wired connection if lag persists."},
    {"title": "Ranked matchmaking", "text": "Ranked matches pair players within one tier. Placement takes 10 matches before a rank is shown."},
]

def init_db():
    DATA.mkdir(exist_ok=True)
    con = sqlite3.connect(DB)
    con.execute("CREATE TABLE IF NOT EXISTS players(name TEXT PRIMARY KEY, matches INT, wins INT, kills INT, deaths INT, hours REAL)")
    if con.execute("SELECT COUNT(*) FROM players").fetchone()[0] == 0:
        con.executemany("INSERT INTO players VALUES(?,?,?,?,?,?)", [
            ("alex", 240, 132, 3100, 2200, 118.5), ("maya", 410, 251, 5400, 3300, 207.0), ("ravi", 95, 41, 900, 1100, 44.2)])
    con.commit(); con.close()

@tool
def get_player_stats(name: str) -> str:
    """Look up a player's matches, wins, kills, deaths and hours played by player name."""
    con = sqlite3.connect(DB)
    row = con.execute("SELECT * FROM players WHERE name = ?", (name.strip().lower(),)).fetchone()
    con.close()
    if not row:
        return f"No player named '{name}' found."
    return json.dumps(dict(zip(["name", "matches", "wins", "kills", "deaths", "hours"], row)))

@tool
def search_kb(query: str) -> str:
    """Search the game support knowledge base (passwords, refunds, lag, matchmaking). Returns the best matches."""
    words = set(re.findall(r"\w+", query.lower()))
    scored = sorted(KB, key=lambda d: -len(words & set(re.findall(r"\w+", (d["title"] + " " + d["text"]).lower()))))
    return json.dumps([d for d in scored[:2] if words & set(re.findall(r"\w+", (d["title"] + " " + d["text"]).lower()))] or "No relevant article found.")

_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv, ast.Pow: operator.pow, ast.USub: operator.neg}

def _eval(n):
    if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)): return n.value
    if isinstance(n, ast.BinOp) and type(n.op) in _OPS: return _OPS[type(n.op)](_eval(n.left), _eval(n.right))
    if isinstance(n, ast.UnaryOp) and type(n.op) in _OPS: return _OPS[type(n.op)](_eval(n.operand))
    raise ValueError("Unsupported expression")

@tool
def calculate(expression: str) -> str:
    """Safely evaluate a math expression such as '132/240*100'. Use for any arithmetic like win rate or K/D."""
    return str(_eval(ast.parse(expression, mode="eval").body))

TOOLS = [get_player_stats, search_kb, calculate]
TOOL_MAP = {t.name: t for t in TOOLS}
