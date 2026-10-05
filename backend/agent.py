import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from tools import TOOLS, TOOL_MAP

MAX_STEPS = 5
SYSTEM = ("You are PlayAssist, a game support and match-insights assistant. "
          "Answer ONLY the user's latest message; earlier messages are context, so never repeat earlier answers. "
          "Use tools for player data, support articles and arithmetic; never guess numbers. "
          "For support questions, base your answer strictly on what search_kb returns. Do not add steps, links, "
          "contact details or timelines that the article does not state. "
          "If the article does not cover something, say you don't have that information. "
          "If a tool finds nothing, say so.")
_llm = None

def get_llm():
    global _llm
    if _llm is None:  # OPENAI_API_KEY is read by the client; OPENAI_BASE_URL allows a custom endpoint
        _llm = ChatOpenAI(model=os.getenv("MODEL", "gpt-4o-mini"), base_url=os.getenv("OPENAI_BASE_URL") or None,
                          temperature=0).bind_tools(TOOLS)
    return _llm

def run_agent(history):
    msgs = [SystemMessage(SYSTEM)] + [HumanMessage(m["content"]) if m["role"] == "user" else AIMessage(m["content"]) for m in history]
    trace = []
    for _ in range(MAX_STEPS):
        ai = get_llm().invoke(msgs)
        msgs.append(ai)
        if not ai.tool_calls:
            return ai.content, trace
        for call in ai.tool_calls:
            try:
                out = TOOL_MAP[call["name"]].invoke(call["args"])
            except Exception as e:
                out = f"Tool error: {e}"
            trace.append({"tool": call["name"], "args": call["args"], "result": str(out)[:500]})
            msgs.append(ToolMessage(content=str(out), tool_call_id=call["id"]))
    return "I couldn't finish within the step limit.", trace
