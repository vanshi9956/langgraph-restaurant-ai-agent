# 🍽️ LangGraph Restaurant AI Agent

An interactive AI-powered restaurant ordering agent built with **Python, LangGraph, LangChain, Groq, Pydantic, and structured LLM outputs**.

The agent understands natural-language food orders, checks inventory, handles partial/unavailable orders, simulates cooking and serving, and uses retry-based workflows.

---

## 🚀 Features

- 🗣️ Natural-language food ordering
- 🤖 LLM-based order extraction using Groq
- 📦 Structured order output using Pydantic
- 🧠 Stateful workflow using LangGraph
- 🍕 Menu and inventory validation
- 🔄 Retry workflows for cooking and serving
- ⚠️ Handles unavailable and partially available items
- 🔀 Conditional routing between workflow nodes
- 🔐 API key loaded securely through `.env`
- 🧩 Modular node-based architecture

---

## 🛠️ Tech Stack

- **Python 3.13**
- **LangGraph** – workflow orchestration and state management
- **LangChain** – LLM integration and output parsing
- **Groq** – LLM inference
- **Pydantic** – structured data validation
- **python-dotenv** – environment variable management

---

## 🧠 Why LangGraph?

This project uses LangGraph because a restaurant ordering agent is not just a single LLM request. It is a **multi-step workflow with state, decisions, loops, and retries**.

For example:

```text
Customer Order
      ↓
Extract Order
      ↓
Check Availability
   ↙    ↓       ↘
Partial  Confirm  Unavailable
   ↓      ↓          ↓
Choice   Cook      Reorder
            ↓
          Serve
            ↓
           END
```

LangGraph makes it easier to:

- Maintain shared state between steps
- Create independent workflow nodes
- Add conditional routing
- Implement loops and retry mechanisms
- Separate LLM reasoning from application logic
- Make the workflow easier to debug and extend

Instead of allowing the LLM to control the complete application flow, **LangGraph controls the workflow while the LLM is used where natural-language understanding is required.**

---

# 🧩 Graph Nodes

The application contains the following nodes:

| Node | Purpose |
|---|---|
| `ask_for_order` | Asks the customer for their food order |
| `extract_order` | Uses the LLM to convert natural language into structured order data |
| `confirm_order` | Checks the requested quantity against available inventory |
| `partial_choice` | Handles cases where only part of the requested quantity is available |
| `unavailable_choice` | Handles cases where the requested item is unavailable |
| `cook` | Simulates preparing/cooking the order |
| `serve` | Simulates serving the completed order |

### Node Flow

```text
START
  ↓
ask_for_order
  ↓
extract_order
  ↓
confirm_order
  ├── ORDER_CONFIRMED ─────→ cook
  ├── PARTIALLY_AVAILABLE → partial_choice
  └── NOT_AVAILABLE ──────→ unavailable_choice

cook
  ├── COOK_RETRY → cook
  └── READY → serve

serve
  ├── SERVE_RETRY → cook
  └── complete → END
```

Invalid requests can also terminate the workflow directly.

---

# 📦 State

LangGraph uses a shared `RestaurantState` to pass information between nodes.

```python
class RestaurantState(TypedDict, total=False):
    messages: list
    dish_name: str
    required_quantity: int
    available_quantity: int
    status: str
    order_retries: int
    cook_retries: int
    delivery_retries: int
    final_result: str
```

## Important State Fields

| State | Purpose |
|---|---|
| `messages` | Stores conversation/user messages |
| `dish_name` | Stores the requested food item |
| `required_quantity` | Stores the quantity requested by the customer |
| `available_quantity` | Stores available inventory |
| `status` | Controls workflow routing |
| `order_retries` | Tracks order-related retries |
| `cook_retries` | Tracks cooking retries |
| `delivery_retries` | Tracks serving/delivery retries |
| `final_result` | Stores the final outcome |

---

# 🔀 Status Values

The `status` field is used by conditional routing functions.

### Order statuses

```text
INVALID_REQUEST
ORDER_CONFIRMED
PARTIALLY_AVAILABLE
NOT_AVAILABLE
REORDER
```

### Cooking statuses

```text
COOK_RETRY
READY
```

### Serving statuses

```text
SERVE_RETRY
```

The routing functions inspect these values and decide which node should execute next.

For example:

```python
def route_confirmation(state: RestaurantState) -> str:
    return state["status"]
```

Then LangGraph maps the returned status to the appropriate node.

---

# 🤖 LLM + Structured Output

The agent uses **Groq** for natural-language understanding.

The customer might say:

```text
"I want two cheese pizzas"
```

Instead of relying on free-form LLM text, the application asks the model to return structured data using Pydantic:

```python
class ExtractedOrder(BaseModel):
    is_food_order: bool
    dish_name: str
    quantity: int
```

This allows the Python application to work with predictable data.

### Flow

```text
Natural Language
      ↓
Groq LLM
      ↓
Pydantic Parser
      ↓
ExtractedOrder
      ↓
RestaurantState
```

---

# 🔄 Retry Workflow

The agent contains retry logic for unreliable operations.

### Cooking

```text
cook
 ↓
COOK_RETRY
 ↓
cook
```

or:

```text
cook
 ↓
READY
 ↓
serve
```

### Serving

```text
serve
 ↓
SERVE_RETRY
 ↓
cook
```

This demonstrates how LangGraph can create **loops and recovery paths** rather than following only a linear workflow.

---

# 📋 Example

### User

```text
I want 9 burgers
```

### Agent

The agent checks the menu/inventory.

If only 5 burgers are available:

```text
Requested: 9
Available: 5
Status: PARTIALLY_AVAILABLE
```

The workflow moves to:

```text
partial_choice
```

The customer can then choose whether to continue with the available quantity or place another order.

---

# 📁 Project Structure

```text
restaurant_ai_agent/
│
├── restaurant_agent.py
├── prompt.md
├── requirements.txt
├── .gitignore
├── .env                 # Not committed to GitHub
└── README.md
```

---

# ⚙️ Setup

### 1. Clone the repository

```bash
git clone https://github.com/vanshi9956/langgraph-restaurant-ai-agent.git
cd langgraph-restaurant-ai-agent
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate it

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Create `.env`

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
```

Do **not** commit `.env` to GitHub.

### 6. Run the agent

```bash
python restaurant_agent.py
```

---

# 🏗️ Architecture

The project follows a simple separation of responsibilities:

```text
                 ┌──────────────────┐
                 │   User Input     │
                 └────────┬─────────┘
                          ↓
                 ┌──────────────────┐
                 │ ask_for_order    │
                 └────────┬─────────┘
                          ↓
                 ┌──────────────────┐
                 │ extract_order    │
                 │  Groq + Pydantic │
                 └────────┬─────────┘
                          ↓
                 ┌──────────────────┐
                 │ confirm_order    │
                 └────────┬─────────┘
                    Conditional
                   Routing by Status
                 ↙        ↓         ↘
        partial_choice   cook   unavailable_choice
                           ↓
                         serve
                           ↓
                          END
```

---

# 📝 Prompt Used to Develop the Project

The following prompt can be used to recreate or extend this project with an AI coding assistant:

```text
Build a beginner-friendly AI restaurant ordering agent in Python using LangGraph, LangChain, Groq, Pydantic, and python-dotenv.

Requirements:

1. Create a restaurant ordering workflow using LangGraph StateGraph.

2. Create a MENU dictionary with food items and available quantities/prices.

3. Define a RestaurantState TypedDict that stores:
   - messages
   - dish_name
   - required_quantity
   - available_quantity
   - status
   - order_retries
   - cook_retries
   - delivery_retries
   - final_result

4. Create a Pydantic model called ExtractedOrder with:
   - is_food_order: bool
   - dish_name: str
   - quantity: int

5. Use Groq as the LLM provider and load GROQ_API_KEY from a .env file.

6. Use PydanticOutputParser so that the LLM returns structured order information instead of free-form text.

7. Create these LangGraph nodes:
   - ask_for_order
   - extract_order
   - confirm_order
   - partial_choice
   - unavailable_choice
   - cook
   - serve

8. The extract_order node should convert natural-language input into ExtractedOrder and update the graph state.

9. The confirm_order node should:
   - check whether the requested dish exists
   - check available quantity
   - confirm the order if enough stock exists
   - handle partial availability
   - handle unavailable items

10. Use status values such as:
   - INVALID_REQUEST
   - ORDER_CONFIRMED
   - PARTIALLY_AVAILABLE
   - NOT_AVAILABLE
   - REORDER
   - COOK_RETRY
   - READY
   - SERVE_RETRY

11. Create conditional routing functions:
   - route_confirmation
   - route_cook
   - route_serve

12. Add retry logic for cooking and serving.

13. The graph should demonstrate:
   - conditional edges
   - loops
   - state updates
   - retry workflows
   - clean separation between LLM logic and application workflow

14. Do not let the LLM control the entire application flow. LangGraph/Python should control the workflow, while the LLM should primarily handle natural-language order extraction.

15. Keep the implementation beginner-friendly and explain every node, state field, routing function, and graph edge.

16. Generate a README.md documenting:
   - project overview
   - why LangGraph is used
   - node names and responsibilities
   - RestaurantState fields
   - status values
   - architecture/graph flow
   - setup instructions
   - example interaction
   - technologies used

17. Keep API keys out of source control and include .env, venv/, .venv/, __pycache__/, and *.pyc in .gitignore.
```

---

## 🎯 Learning Outcomes

This project demonstrates practical concepts in:

- LangGraph `StateGraph`
- Graph nodes and edges
- Conditional routing
- Shared state
- LLM structured output
- Pydantic validation
- Retry loops
- Workflow orchestration
- Environment variables
- Groq + LangChain integration

---

## 👩‍💻 Author

**Vanshika Jain**

Built as a hands-on project to learn **LangGraph, LLM workflows, structured outputs, and AI agent architecture**.
