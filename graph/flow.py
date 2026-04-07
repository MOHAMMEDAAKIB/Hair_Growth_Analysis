from langgraph.graph import StateGraph, END
from graph.state import HairState
from graph.nodes import (
    detect_head,
    crop_head,
    analyze_hair,
    generate_report,
    check_error
)

def create_hair_graph():
    workflow = StateGraph(HairState)

    # Nodes add
    workflow.add_node("detect_head", detect_head)
    workflow.add_node("crop_head", crop_head)
    workflow.add_node("analyze_hair", analyze_hair)
    workflow.add_node("generate_report", generate_report)

    # Entry point
    workflow.set_entry_point("detect_head")

    # Edges — Error check பண்ணிட்டு போ
    workflow.add_conditional_edges(
        "detect_head",
        check_error,
        {
            "error": END,
            "continue": "crop_head"
        }
    )

    workflow.add_edge("crop_head", "analyze_hair")
    workflow.add_edge("analyze_hair", "generate_report")
    workflow.add_edge("generate_report", END)

    return workflow.compile()

# Graph instance
hair_graph = create_hair_graph()