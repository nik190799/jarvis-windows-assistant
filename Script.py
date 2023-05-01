import sys
import os
import subprocess
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton
import openai
import json

openai.api_key = "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"

class AIAssistantUI(QWidget):
    def __init__(self):
        super().__init__()
        self.current_directory = os.getcwd()
        self.default_path = 'C:/Users/16823/Documents/New folder/Windows Assistant/messages.json'
        self.init_ui()
        
    def save_messages(self, messages):
        # Save the message array to a file
        with open(self.default_path, 'w') as f:
            json.dump(messages, f)

    def load_messages(self):
        # Load the message array from a file
        
        if os.path.exists(self.default_path):
            with open(self.default_path, 'r') as f:
                messages = json.load(f)
            return messages
        else:
            return []

    def init_ui(self):
        
        # Set up the layout and components
        layout = QVBoxLayout()

        title = QLabel("Jarvis-like AI Assistant")
        layout.addWidget(title)

        input_label = QLabel("Enter your query:")
        layout.addWidget(input_label)

        self.text_input = QLineEdit()
        layout.addWidget(self.text_input)
        self.text_input.installEventFilter(self)  # Install event filter to listen for Enter key press

        response_label = QLabel("Assistant's response:")
        layout.addWidget(response_label)

        self.text_response = QTextEdit()
        self.text_response.setReadOnly(True)
        layout.addWidget(self.text_response)

        send_button = QPushButton("Send")
        layout.addWidget(send_button)
        send_button.clicked.connect(self.send_query)

        self.setLayout(layout)
        self.setWindowTitle("AI Assistant")
        self.setGeometry(300, 300, 400, 300)
        
    def get_response(self, user_input):

        messages = self.load_messages()
        
        # Send a text query to the OpenAI API
        response = openai.ChatCompletion.create(
          model="gpt-3.5-turbo",
          messages = messages + [
            {"role":"user","content": user_input}]
        )
        
        # Add the user's input and the OpenAI API's response to the message array
        messages.append({"role": "user", "content": user_input})
        messages.append({"role": "assistant", "content": response.choices[0].message.content})

        # Save the message array to a file
        self.save_messages(messages)
        return response.choices[0].message.content

    def eventFilter(self, source, event):
        # Check if the event is a key press event from the text_input widget and if the key is Enter
        if (event.type() == QEvent.KeyPress and source is self.text_input and
                (event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter)):
            self.send_query()
            return True

        return super().eventFilter(source, event)

    def send_query(self):
        # Placeholder for processing the query and receiving a response
        user_query = self.text_input.text()
        assistant_response = self.get_response(user_query)
        self.run_command(assistant_response)
        
        self.text_response.setPlainText(assistant_response)
        self.text_input.clear()
        
        
    def run_command(self, command):

        # Change the working directory to the selected directory
        os.chdir(self.current_directory)
        
        # Run the command using subprocess
        subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ai_assistant_ui = AIAssistantUI()
    ai_assistant_ui.show()
    sys.exit(app.exec_())