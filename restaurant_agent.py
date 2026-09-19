"""Interactive restaurant ordering agent built with LangGraph.

Set GROQ_API_KEY before running:
    pip install -r requirements.txt
    python restaurant_agent.py
"""

from __future__ import annotations

import random
import os
from functools import lru_cache
from typing import Annotated, Literal, TypedDict
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field


load_dotenv()

# Change stock here to match the restaurant's real menu.
MENU: dict[str, int] = {
    "pizza": 8,
    "burger": 5,
    "pasta": 6,
    "salad": 4,
    "sandwich": 7,
}

ORDER_RETRIES = 3
COOK_RETRIES = 2
DELIVERY_RETRIES = 2


class ExtractedOrder(BaseModel):
    """The only information the LLM is permitted to extract."""

    is_food_order: bool = Field(description="True only for a request to order food.")
    dish_name: str | None = Field(default=None, description="Requested dish, lower case.")
    quantity: int | None = Field(default=None, ge=1, description="Positive requested quantity.")


class RestaurantState(TypedDict, total=False):
    # Annotated reducer preserves the conversation between user and agent.
    messages: Annotated[list[BaseMessage], add_messages]
    dish_name: str
    required_quantity: int
    available_quantity: int
    status: str
    order_retries_left: int
    cook_retries_left: int
    delivery_retries_left: int
    final_result: Literal["complete", "cancelled"]


def assistant_message(text: str) -> dict:
    print(f"Agent: {text}")
    return {"messages": [AIMessage(content=text)]}


def ask_for_order(_: RestaurantState) -> dict:
    text = input("You: ").strip()
    return {"messages": [HumanMessage(content=text)]}


@lru_cache(maxsize=1)
def get_extractor() -> tuple[ChatGroq, PydanticOutputParser]:
    """Create the API client only when an order is actually being processed."""
    parser = PydanticOutputParser(pydantic_object=ExtractedOrder)
    api_key = os.getenv("GROQ_API_KEY")
    model = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
    groq_api_key=api_key
)
    return model, parser


EXTRACTION_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You extract restaurant orders. A valid request must ask to order exactly one "
            "food dish and a positive quantity. Do not invent missing values. "
            "Return only the requested JSON.\n{format_instructions}",
        ),
        ("human", "{request}"),
    ]
)


def extract_order(state: RestaurantState) -> dict:
    request = state["messages"][-1].content
    model, parser = get_extractor()
    chain = EXTRACTION_PROMPT | model | parser
    order = chain.invoke(
        {"request": request, "format_instructions": parser.get_format_instructions()}
    )
    if not order.is_food_order or not order.dish_name or not order.quantity:
        update = assistant_message(
            "I’m a food-ordering agent. Please order one dish and specify its quantity."
        )
        return {**update, "status": "INVALID_REQUEST", "final_result": "cancelled"}
    return {
        "dish_name": order.dish_name.strip().lower(),
        "required_quantity": order.quantity,
        "status": "ORDER_RECEIVED",
    }


def confirm_order(state: RestaurantState) -> dict:
    available = MENU.get(state["dish_name"], 0)
    requested = state["required_quantity"]
    if available == 0:
        status = "NOT_AVAILABLE"
    elif available < requested:
        status = "PARTIALLY_AVAILABLE"
    else:
        status = "ORDER_CONFIRMED"
    return {"available_quantity": available, "status": status}


def partial_choice(state: RestaurantState) -> dict:
    dish, available = state["dish_name"], state["available_quantity"]
    answer = input(
        f"Agent: Only {available} {dish} are available. Type 'continue' to order them, "
        "or enter a new order: \nYou: "
    ).strip()
    if answer.lower() == "continue":
        return {
            "required_quantity": available,
            "status": "ORDER_CONFIRMED",
            "messages": [HumanMessage(content="continue")],
        }
    remaining = state["order_retries_left"] - 1
    if remaining <= 0:
        update = assistant_message("I’m sorry, the order could not be finalized. Goodbye.")
        return {**update, "status": "ORDER_CANCELLED", "order_retries_left": 0,
                "final_result": "cancelled"}
    return {"status": "REORDER", "order_retries_left": remaining,
            "messages": [HumanMessage(content=answer)]}


def unavailable_choice(state: RestaurantState) -> dict:
    remaining = state["order_retries_left"] - 1
    dish = state["dish_name"]
    answer = input(
        f"Agent: Sorry, {dish} is unavailable. Please enter another order: \nYou: "
    ).strip()
    if remaining <= 0:
        update = assistant_message("I’m sorry, the order could not be finalized. Goodbye.")
        return {**update, "status": "ORDER_CANCELLED", "order_retries_left": 0,
                "final_result": "cancelled"}
    return {"status": "REORDER", "order_retries_left": remaining,
            "messages": [HumanMessage(content=answer)]}


def cook_order(state: RestaurantState) -> dict:
    if random.random() < 0.60:
        update = assistant_message("Your order is ready and is being served.")
        return {**update, "status": "READY"}
    retries = state["cook_retries_left"] - 1
    if retries <= 0:
        update = assistant_message("We’re sorry, the kitchen could not prepare your order. It is cancelled.")
        return {**update, "status": "COOK_FAILED", "cook_retries_left": 0,
                "final_result": "cancelled"}
    update = assistant_message("The kitchen had an issue; we are trying once more.")
    return {**update, "status": "COOK_RETRY", "cook_retries_left": retries}


def serve_order(state: RestaurantState) -> dict:
    if random.random() < 0.60:
        update = assistant_message("Your order is complete. Enjoy your meal!")
        return {**update, "status": "COMPLETE", "final_result": "complete"}
    retries = state["delivery_retries_left"] - 1
    if retries <= 0:
        update = assistant_message("We’re sorry, we could not serve your order. It is cancelled.")
        return {**update, "status": "SERVE_FAILED", "delivery_retries_left": 0,
                "final_result": "cancelled"}
    update = assistant_message("Serving failed; we are sending the order back to the kitchen.")
    return {**update, "status": "SERVE_RETRY", "delivery_retries_left": retries}


def route_confirmation(state: RestaurantState) -> str:
    return state["status"]


def route_cook(state: RestaurantState) -> str:
    return "cook" if state["status"] == "COOK_RETRY" else "serve" if state["status"] == "READY" else "end"


def route_serve(state: RestaurantState) -> str:
    return "cook" if state["status"] == "SERVE_RETRY" else "end"


def build_graph():
    graph = StateGraph(RestaurantState)
    graph.add_node("ask_for_order", ask_for_order)
    graph.add_node("extract_order", extract_order)
    graph.add_node("confirm_order", confirm_order)
    graph.add_node("partial_choice", partial_choice)
    graph.add_node("unavailable_choice", unavailable_choice)
    graph.add_node("cook", cook_order)
    graph.add_node("serve", serve_order)
    graph.add_edge(START, "ask_for_order")
    graph.add_edge("ask_for_order", "extract_order")
    graph.add_conditional_edges("extract_order", lambda s: "end" if s["status"] == "INVALID_REQUEST" else "confirm_order", {"end": END, "confirm_order": "confirm_order"})
    graph.add_conditional_edges("confirm_order", route_confirmation, {"ORDER_CONFIRMED": "cook", "PARTIALLY_AVAILABLE": "partial_choice", "NOT_AVAILABLE": "unavailable_choice"})
    graph.add_conditional_edges("partial_choice", lambda s: "cook" if s["status"] == "ORDER_CONFIRMED" else "extract" if s["status"] == "REORDER" else "end", {"cook": "cook", "extract": "extract_order", "end": END})
    graph.add_conditional_edges("unavailable_choice", lambda s: "extract" if s["status"] == "REORDER" else "end", {"extract": "extract_order", "end": END})
    graph.add_conditional_edges("cook", route_cook, {"cook": "cook", "serve": "serve", "end": END})
    graph.add_conditional_edges("serve", route_serve, {"cook": "cook", "end": END})
    return graph.compile()


if __name__ == "__main__":
    app = build_graph()
    result = app.invoke({
        "messages": [],
        "status": "STARTED",
        "order_retries_left": ORDER_RETRIES,
        "cook_retries_left": COOK_RETRIES,
        "delivery_retries_left": DELIVERY_RETRIES,
    })
    print(f"Final result: {result['final_result']}")
