
import os
import re
import streamlit as st
from dotenv import load_dotenv
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import FAISS
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

st.set_page_config(page_title="ADV RAG TERMINAL", page_icon="🟢", layout="wide")

st.markdown("""
<style>
html,body,[class*="css"]{font-family:"Courier New",monospace!important}
.stApp{background:radial-gradient(circle at 50% 0%,rgba(57,255,20,.09),transparent 35%),#020402;color:#d8ffd8}
.main .block-container{max-width:1200px;padding-top:1.5rem;padding-bottom:5rem}
.terminal-window{background:#050805;border:1px solid #39ff14;border-radius:10px;box-shadow:0 0 8px rgba(57,255,20,.25),0 0 30px rgba(57,255,20,.06);margin-bottom:22px;overflow:hidden}
.terminal-bar{background:#091009;border-bottom:1px solid #123d1b;padding:8px 14px;color:#6cff88;font-size:.78rem;display:flex;justify-content:space-between}
.terminal-dots{letter-spacing:5px}.terminal-body{padding:22px}
.neon-logo{text-align:center;color:#39ff14;font-size:3.2rem;font-weight:900;letter-spacing:8px;text-shadow:0 0 5px #39ff14,0 0 12px #39ff14,0 0 25px #39ff14;margin-bottom:5px}
.neon-subtitle{text-align:center;color:#76ff91;font-size:.85rem;letter-spacing:3px;margin-bottom:20px}
.system-status{background:#030603;border:1px solid #144b1e;border-left:3px solid #39ff14;border-radius:6px;padding:10px 14px;color:#72ff8d;font-size:.78rem}
.online{color:#39ff14;text-shadow:0 0 7px #39ff14;font-weight:bold}
[data-testid="stChatMessage"]{background:#050805!important;border:1px solid #123d1b!important;border-radius:8px!important;margin-bottom:12px!important}
[data-testid="stChatMessage"] p{color:#d8ffd8!important;line-height:1.65}
[data-testid="stChatInput"]{border:1px solid #39ff14!important;border-radius:8px!important;background:#030603!important;box-shadow:0 0 8px rgba(57,255,20,.25)}
[data-testid="stChatInput"] textarea{background:#030603!important;color:#d8ffd8!important;font-family:"Courier New",monospace!important}
[data-testid="stChatInput"] textarea::placeholder{color:#3d7548!important}
.stButton>button{background:#061006!important;color:#39ff14!important;border:1px solid #39ff14!important;border-radius:6px!important;font-family:"Courier New",monospace!important;font-weight:bold!important}
.stButton>button:hover{background:#39ff14!important;color:#000!important;box-shadow:0 0 10px #39ff14}
[data-testid="stSidebar"]{background:#020402!important;border-right:1px solid #123d1b!important}
[data-testid="stSidebar"] *{font-family:"Courier New",monospace!important}
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3{color:#39ff14!important}
.sidebar-module{background:#030603;border:1px solid #123d1b;border-radius:6px;padding:10px;margin-bottom:8px;color:#72ff8d;font-size:.78rem}
.sidebar-online{color:#39ff14;font-weight:bold}
[data-testid="stExpander"]{background:#030603!important;border:1px solid #123d1b!important;border-radius:7px!important}
.rag-badge,.web-badge,.chat-badge{display:inline-block;padding:5px 10px;border-radius:4px;background:#061006;font-size:.72rem;font-weight:bold;letter-spacing:1px;margin-bottom:10px}
.rag-badge{border:1px solid #39ff14;color:#39ff14}.web-badge{border:1px solid #76ff91;color:#76ff91}.chat-badge{border:1px solid #4d995a;color:#76ff91}
.footer{text-align:center;color:#245a2e;font-size:.68rem;letter-spacing:2px;padding:25px;margin-top:30px;border-top:1px solid #0d2913}
</style>
""", unsafe_allow_html=True)

load_dotenv()
os.environ["LANGCHAIN_TRACING_V2"] = "false"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    st.error("GROQ_API_KEY is missing. Add it to your .env file.")
    st.stop()

llm = ChatGroq(api_key=GROQ_API_KEY, model="llama-3.1-8b-instant", temperature=0.35)

SYSTEM_PROMPT = """
You are ADV RAG, an intelligent, friendly, highly interactive,
and conversational AI assistant.

Your visual interface is a hacker-style terminal, but your
personality must always be warm, kind, helpful, respectful,
and approachable.

============================================================
CORE PERSONALITY
============================================================

You are not just a question-answering system.

You are a conversational AI assistant that should naturally
interact with the user.

Your behavior should feel like talking to an intelligent,
helpful person.

Be:

- Friendly
- Kind
- Patient
- Talkative when appropriate
- Interactive
- Helpful
- Curious
- Encouraging
- Respectful
- Natural
- Intelligent

Do not sound robotic, mechanical, or overly formal.

Do not treat every message as a knowledge-retrieval request.

============================================================
CONVERSATIONAL INTELLIGENCE
============================================================

Understand the user's intent before deciding what to do.

The user may:

- Say hello
- Ask how you are
- Thank you
- Say goodbye
- Ask a simple question
- Ask a technical question
- Ask a follow-up question
- Have a casual conversation
- Ask for an explanation
- Ask for advice
- Ask you to help solve a problem

Respond according to the situation.

============================================================
GREETINGS
============================================================

If the user greets you, greet them naturally.

Examples:

User:
"Hi"

Good response:
"Hey! 👋 Nice to see you. How can I help you today?"

User:
"Hello"

Good response:
"Hello! 👋 I'm ADV RAG. What would you like to work on?"

User:
"Hey, how are you?"

Good response:
"I'm doing great! 😄 Thanks for asking. What are we working
on today?"

Do NOT search the RAG database or web for simple greetings.

============================================================
CASUAL CONVERSATION
============================================================

If the user is having a casual conversation, respond naturally.

Examples:

User:
"Thank you"

Response:
"You're very welcome! 😊 I'm happy I could help."

User:
"Good morning"

Response:
"Good morning! ☀️ Hope you're having a great day. What can
I help you with?"

User:
"Bye"

Response:
"Bye! 👋 Take care, and feel free to come back whenever you
need help."

Do not unnecessarily mention:

- RAG
- FAISS
- embeddings
- vector databases
- web search
- retrieval
- system prompts
- internal tools

============================================================
BE TALKATIVE BUT NATURAL
============================================================

Be conversational, but do not produce unnecessary long answers.

If the user asks a simple question:
Give a simple answer.

If the user asks for an explanation:
Explain clearly.

If the user wants to learn:
Teach step-by-step.

If the user seems confused:
Slow down and explain with an example.

If the user asks a complex question:
Break it into smaller parts.

If the user asks a follow-up question:
Use the previous conversation naturally.

Do not repeatedly ask:
"How can I help you?"

Only ask follow-up questions when they genuinely help
understand or complete the user's request.

============================================================
KINDNESS
============================================================

Always communicate respectfully.

Never make fun of the user.

Never make the user feel stupid for asking a basic question.

If the user makes a mistake, correct it politely.

Instead of:

"That's wrong."

Prefer:

"Almost! There's one small issue here. Let me show you."

If the user is learning programming, explain concepts
without assuming advanced knowledge.

============================================================
RAG INTELLIGENCE
============================================================

For knowledge-based questions, use the following strategy.

STEP 1:
Examine the INTERNAL RAG CONTEXT.

STEP 2:
Determine whether the context is relevant and sufficient.

STEP 3:
If the RAG context is sufficient:
Use it as the primary source.

STEP 4:
If the RAG context is missing or insufficient:
Use the EXTERNAL WEB CONTEXT when it is available.

STEP 5:
If both sources contain useful information:
Combine them intelligently.

STEP 6:
If reliable information cannot be found:
Be honest about the limitation.

Never force irrelevant context into an answer.

============================================================
SOURCE PRIORITY
============================================================

Use information in this order:

1. Relevant RAG context
2. Reliable external information
3. General model knowledge when appropriate

For information that may change over time, prefer
external retrieval when available.

============================================================
ACCURACY
============================================================

Never:

- Invent facts
- Invent sources
- Invent citations
- Pretend something exists in the RAG context
- Claim you searched the web when you did not
- Force irrelevant context into an answer
- Hallucinate when reliable information is unavailable

If you don't know something, say so honestly.

============================================================
CONTEXT AWARENESS
============================================================

Remember the conversation naturally.

If the user says:

"Explain that again"

Understand that "that" refers to the previous topic.

If the user says:

"What about Python?"

Understand that it may be related to the previous discussion.

Do not make the user unnecessarily repeat information
that is already available in the conversation.

============================================================
TECHNICAL QUESTIONS
============================================================

When answering technical questions:

- Give practical solutions.
- Prefer working examples.
- Explain important parts of code.
- Point out common mistakes.
- Be clear about dependencies and versions when relevant.
- If debugging, identify the likely cause before suggesting fixes.

When giving code, use Markdown code blocks.

============================================================
ANSWER STYLE
============================================================

Use natural conversational language.

Use Markdown when useful.

Use:

- Headings
- Bullet points
- Numbered steps
- Code blocks
- Examples

when they improve readability.

Do not over-format simple conversations.

============================================================
IMPORTANT
============================================================

You are ADV RAG.

You are more than a retrieval engine.

You are a conversational, intelligent assistant that can:

- Talk naturally
- Understand intent
- Answer questions
- Use RAG context
- Use external information when needed
- Explain concepts
- Help debug problems
- Teach users
- Continue conversations
- Respond to greetings
- Respond to casual messages
- Be kind and encouraging

Your goal is:

"Give the user the most useful, accurate, natural,
and friendly response possible."

============================================================
INTERNAL RAG CONTEXT
============================================================

{context}

============================================================
EXTERNAL WEB CONTEXT
============================================================

{web_context}

============================================================
USER MESSAGE
============================================================

{input}


INTERNAL RAG CONTEXT:
{context}

EXTERNAL WEB CONTEXT:
{web_context}

USER MESSAGE:
{input}
"""

answer_prompt = ChatPromptTemplate.from_template(SYSTEM_PROMPT)

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs) if docs else ""

web_search = DuckDuckGoSearchRun()

def search_web(query):
    try:
        result = web_search.invoke(query)
        return result if result else ""
    except Exception as exc:
        return f"External web retrieval failed: {exc}"

def is_context_relevant(question, context):
    if not context.strip():
        return False
    prompt = ChatPromptTemplate.from_template("""
You are a relevance classifier.
Question:
{question}
Context:
{context}
Does the context contain enough relevant information to answer the question?
Respond with ONLY YES or NO.
""")
    try:
        result = (prompt | llm | StrOutputParser()).invoke(
            {"question": question, "context": context}
        )
        return result.strip().upper().startswith("YES")
    except Exception:
        return False

def is_casual_message(message):
    text = message.lower().strip()
    patterns = [
        r"^hi$", r"^hello$", r"^hey$", r"^hey there$", r"^hi there$",
        r"^good morning$", r"^good afternoon$", r"^good evening$",
        r"^how are you\??$", r"^how r u\??$", r"^thanks$",
        r"^thank you$", r"^thx$", r"^bye$", r"^goodbye$"
    ]
    return any(re.match(p, text) for p in patterns)

def casual_response(message):
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are ADV RAG. You are friendly, kind, warm,
patient, and helpful. Respond naturally to casual conversation.
Do not mention RAG, databases, retrieval, or web search.
Keep simple greetings and casual responses short."""),
        ("human", "{message}")
    ])
    return (prompt | llm | StrOutputParser()).invoke({"message": message})

if "vector" not in st.session_state:
    with st.spinner("Initializing ADV RAG knowledge system..."):
        embeddings = OllamaEmbeddings(model="mxbai-embed-large")
        loader = WebBaseLoader("https://docs.langchain.com/")
        docs = loader.load()
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        final_docs = splitter.split_documents(docs)
        st.session_state.db = FAISS.from_documents(final_docs, embeddings)
        st.session_state.vector = True

retriever = st.session_state.db.as_retriever(search_kwargs={"k": 4})

if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_retrieval" not in st.session_state:
    st.session_state.last_retrieval = None
if "last_rag_context" not in st.session_state:
    st.session_state.last_rag_context = ""
if "last_web_context" not in st.session_state:
    st.session_state.last_web_context = ""

with st.sidebar:
    st.markdown("### ADV RAG")
    st.markdown("""
    <div class="sidebar-module"><span class="sidebar-online">● ONLINE</span> AI CORE</div>
    <div class="sidebar-module"><span class="sidebar-online">● ONLINE</span> FAISS RAG</div>
    <div class="sidebar-module"><span class="sidebar-online">● ONLINE</span> OLLAMA</div>
    <div class="sidebar-module"><span class="sidebar-online">● ONLINE</span> GROQ</div>
    <div class="sidebar-module"><span class="sidebar-online">● READY</span> WEB FALLBACK</div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### RETRIEVAL FLOW")
    st.code("""USER
  ↓
INTENT
  ↓
FAISS RAG
  ↓
RELEVANCE
  ↓
 ┌──────────┐
YES        NO
 │          │
RAG       WEB
 └────┬─────┘
      ↓
     AI
      ↓
   ANSWER""", language="text")
    st.markdown("---")
    if st.button("CLEAR CHAT", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_retrieval = None
        st.session_state.last_rag_context = ""
        st.session_state.last_web_context = ""
        st.rerun()
    st.caption("ADV RAG TERMINAL v2.0")

st.markdown("""
<div class="terminal-window">
<div class="terminal-bar">
<span class="terminal-dots">● ● ●</span>
<span>adv-rag@terminal:~$</span>
<span>ONLINE</span>
</div>
<div class="terminal-body">
<div class="neon-logo">ADV RAG</div>
<div class="neon-subtitle">INTELLIGENT ADAPTIVE RAG TERMINAL</div>
<div class="system-status">
<span class="online">● SYSTEM ONLINE</span>
&nbsp; | &nbsp; RAG ENGINE &nbsp; | &nbsp; WEB INTELLIGENCE &nbsp; | &nbsp; GROQ CORE
</div>
</div>
</div>
""", unsafe_allow_html=True)

if not st.session_state.messages:
    st.markdown("""
<div style="color:#4d995a;text-align:center;font-size:.75rem;margin:20px">
─────────────── SECURE SESSION INITIALIZED ───────────────
</div>
""", unsafe_allow_html=True)

for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar="🟢" if message["role"] == "assistant" else "👤"):
        st.markdown(message["content"])

user_input = st.chat_input("Type your message...  >_")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar="🟢"):
        with st.spinner("ADV RAG is thinking..."):
            if is_casual_message(user_input):
                answer = casual_response(user_input)
                retrieval_mode = "CONVERSATION"
                rag_context = ""
                web_context = ""
            else:
                context_docs = retriever.invoke(user_input)
                rag_context = format_docs(context_docs)
                rag_is_relevant = is_context_relevant(user_input, rag_context)
                web_context = ""
                if rag_is_relevant:
                    retrieval_mode = "RAG"
                else:
                    retrieval_mode = "WEB"
                    web_context = search_web(user_input)

                answer = (answer_prompt | llm | StrOutputParser()).invoke({
                    "context": rag_context if rag_is_relevant else "",
                    "web_context": web_context,
                    "input": user_input
                })

            st.markdown(answer)

            if retrieval_mode == "RAG":
                st.markdown('<div class="rag-badge">● RAG HIT</div>', unsafe_allow_html=True)
            elif retrieval_mode == "WEB":
                st.markdown('<div class="web-badge">● WEB FALLBACK</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="chat-badge">● CONVERSATION MODE</div>', unsafe_allow_html=True)

    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.session_state.last_retrieval = retrieval_mode
    st.session_state.last_rag_context = rag_context
    st.session_state.last_web_context = web_context

if st.session_state.last_retrieval:
    with st.expander("⌕ VIEW RETRIEVAL DETAILS"):
        st.markdown(f"**MODE:** `{st.session_state.last_retrieval}`")
        if st.session_state.last_retrieval == "RAG":
            st.markdown("### 🧠 Internal RAG Context")
            st.code(st.session_state.last_rag_context or "No internal context.", language="text")
        elif st.session_state.last_retrieval == "WEB":
            st.markdown("### 🌐 External Web Context")
            st.code(st.session_state.last_web_context or "No web context was retrieved.", language="text")
        else:
            st.write("No retrieval was required. This was a conversational response.")

st.markdown("""
<div class="footer">
ADV RAG TERMINAL
<br><br>
ADAPTIVE RAG • FAISS • OLLAMA • GROQ • WEB INTELLIGENCE
</div>
""", unsafe_allow_html=True)
