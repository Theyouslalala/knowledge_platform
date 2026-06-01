"""Gradio frontend application."""

import uuid

import gradio as gr

from ..config import get_settings
from ..core.token_tracker import tracker as token_tracker

settings = get_settings()

from ..core.agents.orchestrator import get_orchestrator


def create_demo():
    with gr.Blocks(title="Knowledge Platform", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# Knowledge Platform")
        gr.Markdown("Knowledge-Enhanced Multi-Agent Collaboration Platform")

        with gr.Tabs():
            with gr.Tab("Chat"):
                chat_interface()

            with gr.Tab("Documents"):
                documents_interface()

            with gr.Tab("Tasks"):
                tasks_interface()

            with gr.Tab("Dashboard"):
                dashboard_interface()

            with gr.Tab("Demo"):
                demo_interface()

    return demo


def chat_interface():
    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(label="Conversation", height=400)
            msg = gr.Textbox(label="Message", placeholder="Ask anything...")
            with gr.Row():
                submit = gr.Button("Send", variant="primary")
                clear = gr.Button("Clear")

        with gr.Column(scale=1):
            gr.Markdown("### Settings")
            agent_mode = gr.Dropdown(
                choices=["auto", "planner", "researcher", "analyst", "writer"],
                value="auto",
                label="Agent Mode",
            )
            max_iterations = gr.Slider(1, 5, value=3, step=1, label="Max Iterations")

    async def respond(message, history, mode, max_iter):
        if not message:
            return history, ""

        history.append([message, None])

        try:
            orchestrator = get_orchestrator()
            task_id = f"chat_{uuid.uuid4().hex[:8]}"
            state = await orchestrator.run(
                task_id=task_id, query=message, max_iterations=int(max_iter)
            )
            response = state.get("final_output", "No response generated.")
        except Exception as e:
            response = f"Error: {e}"

        history[-1][1] = response
        return history, ""

    submit.click(respond, [msg, chatbot, agent_mode, max_iterations], [chatbot, msg])
    msg.submit(respond, [msg, chatbot, agent_mode, max_iterations], [chatbot, msg])
    clear.click(lambda: ([], ""), outputs=[chatbot, msg])


def documents_interface():
    gr.Markdown("### Document Management")
    gr.Markdown("Upload documents to build a knowledge base for RAG retrieval.")

    with gr.Row():
        file_upload = gr.File(
            label="Upload Document", file_types=[".txt", ".md", ".pdf", ".docx"]
        )
        upload_btn = gr.Button("Upload", variant="primary")

    status = gr.Textbox(label="Status", interactive=False)

    async def handle_upload(file):
        if file is None:
            return "No file selected"
        from pathlib import Path

        name = Path(file.name).name
        size_kb = Path(file.name).stat().st_size / 1024

        try:
            from ..core.rag.pipeline import RAGPipeline

            pipeline = RAGPipeline()
            result = await pipeline.ingest(file.name)
            chunks = result.get("chunks", 0)
            return f"Uploaded: {name} ({size_kb:.1f} KB) - {chunks} chunks indexed for RAG"
        except Exception as e:
            return f"Upload failed: {e}"

    upload_btn.click(handle_upload, [file_upload], [status])


def tasks_interface():
    gr.Markdown("### Task Management")
    with gr.Row():
        task_input = gr.Textbox(
            label="Task Description", placeholder="Describe your task..."
        )
        task_type = gr.Dropdown(
            choices=["research", "analysis", "writing", "complex"],
            value="complex",
            label="Task Type",
        )
        run_btn = gr.Button("Run Task", variant="primary")

    output = gr.Markdown(label="Result")
    trace = gr.JSON(label="Execution Trace")

    async def run_task(description, task_type):
        if not description:
            return "Please enter a task description.", {}

        try:
            from ..core.execution_tracer import tracer as execution_tracer

            orchestrator = get_orchestrator()
            task_id = f"task_{uuid.uuid4().hex[:8]}"
            state = await orchestrator.run(task_id=task_id, query=description)

            result = state.get("final_output", "No result")
            trace_data = execution_tracer.get_summary(task_id)
            trace_data["plan"] = state.get("plan", "")
            trace_data["iterations"] = state.get("iteration", 0)
            trace_data["status"] = state.get("status", "")
            return result, trace_data
        except Exception as e:
            return f"Error: {e}", {}

    run_btn.click(run_task, [task_input, task_type], [output, trace])


def dashboard_interface():
    gr.Markdown("### Analytics Dashboard")

    with gr.Row():
        with gr.Column():
            total_tokens = gr.Number(
                label="Total Tokens Used", value=0, interactive=False
            )
            total_cost = gr.Number(
                label="Total Cost (USD)", value=0.0, interactive=False
            )
            total_calls = gr.Number(
                label="Total LLM Calls", value=0, interactive=False
            )

    refresh_btn = gr.Button("Refresh Stats")
    stats_json = gr.JSON(label="Detailed Breakdown")

    def refresh_stats():
        summary = token_tracker.get_total_summary()
        return (
            summary.get("total_tokens", 0),
            summary.get("total_cost", 0.0),
            summary.get("total_records", 0),
            summary,
        )

    refresh_btn.click(
        refresh_stats, outputs=[total_tokens, total_cost, total_calls, stats_json]
    )


def demo_interface():
    gr.Markdown("### Demo Mode")
    gr.Markdown("Try these pre-built examples (no API key required in demo mode):")

    examples = [
        (
            "Explain RAG",
            "Explain the concept of Retrieval-Augmented Generation (RAG) and its key components",
        ),
        (
            "Compare Chunking",
            "Compare different text chunking strategies for RAG pipelines",
        ),
        (
            "Multi-Agent Design",
            "What are the key components of a multi-agent system and how do they communicate?",
        ),
    ]

    demo_output = gr.Markdown(label="Demo Result")

    async def run_demo_example(example_query):
        try:
            orchestrator = get_orchestrator()
            task_id = f"demo_{uuid.uuid4().hex[:8]}"
            state = await orchestrator.run(
                task_id=task_id, query=example_query, max_iterations=2
            )
            return state.get("final_output", "No result generated.")
        except Exception as e:
            return f"Demo error (API key may be required): {e}"

    for label, query in examples:
        btn = gr.Button(label, variant="secondary")
        btn.click(
            run_demo_example,
            inputs=[gr.Textbox(value=query, visible=False)],
            outputs=[demo_output],
        )


if __name__ == "__main__":
    demo = create_demo()
    demo.launch(server_name="0.0.0.0", server_port=7860)
