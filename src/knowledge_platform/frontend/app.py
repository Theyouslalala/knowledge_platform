"""Gradio frontend application."""

import gradio as gr

from ..config import get_settings

settings = get_settings()


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
            from ..core.agents.orchestrator import AgentOrchestrator

            orchestrator = AgentOrchestrator()
            state = await orchestrator.run(task_id="demo", query=message, max_iterations=int(max_iter))
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
    with gr.Row():
        file_upload = gr.File(label="Upload Document", file_types=[".txt", ".md", ".pdf", ".docx"])
        upload_btn = gr.Button("Upload", variant="primary")

    status = gr.Textbox(label="Status", interactive=False)
    doc_list = gr.Dataframe(
        headers=["Filename", "Type", "Size", "Status"],
        label="Documents",
    )

    upload_btn.click(lambda f: f"Uploaded: {f.name}" if f else "No file selected", [file_upload], [status])


def tasks_interface():
    gr.Markdown("### Task Management")
    with gr.Row():
        task_input = gr.Textbox(label="Task Description", placeholder="Describe your task...")
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
            from ..core.agents.orchestrator import AgentOrchestrator

            orchestrator = AgentOrchestrator()
            state = await orchestrator.run(task_id="demo_task", query=description)

            result = state.get("final_output", "No result")
            trace_data = {
                "plan": state.get("plan", ""),
                "iterations": state.get("iteration", 0),
                "status": state.get("status", ""),
            }
            return result, trace_data
        except Exception as e:
            return f"Error: {e}", {}

    run_btn.click(run_task, [task_input, task_type], [output, trace])


def dashboard_interface():
    gr.Markdown("### Analytics Dashboard")
    with gr.Row():
        gr.Markdown("""
        **Token Usage Summary**
        - Total Tokens: 0
        - Total Cost: $0.00
        - Tasks Completed: 0
        """)
    gr.JSON(value={"status": "No data yet"}, label="Detailed Stats")


def demo_interface():
    gr.Markdown("### Demo Mode")
    gr.Markdown("Try these pre-built examples (no API key required):")

    examples = [
        "Explain the concept of Retrieval-Augmented Generation (RAG)",
        "Compare different text chunking strategies for RAG",
        "What are the key components of a multi-agent system?",
    ]

    for example in examples:
        gr.Button(example, variant="secondary")


if __name__ == "__main__":
    demo = create_demo()
    demo.launch(server_name="0.0.0.0", server_port=7860)
