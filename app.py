import gradio as gr
from ask_llm import ask_question

with gr.Blocks(title="Materials Data AI Chatbot") as interface:
    with gr.Row():
        gr.Markdown("<h1 style='text-align: center;'>Materials Data AI Chatbot</h1>")
    with gr.Row():
        gr.Markdown("""
        <p style='text-align: center; font-size: 1.2em;'>
        Engage in a conversational flow about materials data. Provide a query,
        and the chatbot will respond. Continue the conversation seamlessly.
        </p>
        """)

    chatbot = gr.Chatbot(type="messages")
    user_input = gr.Textbox(
        label="Your Query",
        placeholder="Type your question about materials data here...",
        lines=1,
    )

    conversation_state = gr.State(value=[])
    submit_button = gr.Button("Submit")
    clear = gr.ClearButton([user_input, chatbot, conversation_state])

    def handle_conversation(user_query, history):
        if not history:
            history = []

        history.append({"role": "user", "content": user_query})

        ai_response = ask_question(user_query, history[:-1])

        history.append({"role": "assistant", "content": ai_response})

        return "", history, history

    user_input.submit(
        handle_conversation,
        inputs=[user_input, conversation_state],
        outputs=[user_input, chatbot, conversation_state],
    )

    submit_button.click(
        handle_conversation,
        inputs=[user_input, conversation_state],
        outputs=[user_input, chatbot, conversation_state],
    )

# Launch the Gradio app
if __name__ == "__main__":
    interface.launch(server_name="0.0.0.0", server_port=7860)
