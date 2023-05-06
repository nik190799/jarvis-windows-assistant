import sys
import os
import subprocess
from PyQt5.QtCore import Qt, QEvent, pyqtSignal, pyqtSlot, QThread
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton, QProgressDialog, QHBoxLayout
import openai
import json
import ast
import threading
import time

openai.api_key = YOUR_OPENAI_API_KEY
num_devs = 2

class GetTasksValueThread(QThread):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

    def run(self):
        self.parent.get_tasks_value()

class AIAssistantUI(QWidget):
    update_text_signal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        #self.current_directory = os.getcwd()
        self.current_directory = 'test\\GPT'
        self.default_manager_path = 'test/Windows Assistant/ModelDatasets/messages_android.json'
        self.default_dev1_path = 'test/Windows Assistant/ModelDatasets/cmdDev1.json'
        self.default_dev2_path = 'test/Windows Assistant/ModelDatasets/cmdDev1.json'
        self.init_ui()
        
        self.running = True
        self.user_inputs_handler = True
        
        self.update_text_signal.connect(self.update_text)
        self.start_get_tasks_value_thread()
        
        
    def init_ui(self):
        # Set up the layout and components
        main_layout = QVBoxLayout()

        title = QLabel("AI Assistant")
        main_layout.addWidget(title)

        response_label = QLabel("Assistant's response:")
        main_layout.addWidget(response_label)

        self.text_response = QTextEdit()
        self.text_response.setReadOnly(True)
        main_layout.addWidget(self.text_response)

        input_layout = QHBoxLayout()

        input_label = QLabel("Enter your query:")
        input_layout.addWidget(input_label)

        self.text_input = QLineEdit()
        input_layout.addWidget(self.text_input)
        self.text_input.installEventFilter(self)  # Install event filter to listen for Enter key press

        send_button = QPushButton("Send")
        input_layout.addWidget(send_button)
        send_button.clicked.connect(self.send_query)

        main_layout.addLayout(input_layout)
        self.setLayout(main_layout)
        self.setWindowTitle("Jarvis")
        self.setGeometry(500, 500, 600, 500)
        
    def formatDirectoryLocation(self, command):
        replaced_command = command.replace('root190799', self.current_directory)
        replaced_command = replaced_command.replace('\\','////')
        replaced_command = replaced_command.replace('////',chr(92))
        
        return replaced_command

    
    def closeEvent(self, event):
        self.running = False  # Set the flag to False when closing the application
        
        self.get_tasks_value_thread.wait()

        super().closeEvent(event)
        
    def distribute_tasks(self, content, num_devs):
        task_chunks = self.split_tasks(content['tasks'], num_devs)
    
        for dev_id, tasks in enumerate(task_chunks, start=1):
            new_item = content.copy()
            new_item['tasks'] = tasks
            self.process_dev(dev_id, new_item)

    def split_tasks(self, tasks, num_devs):
        task_count = len(tasks)
        chunk_size = task_count // num_devs
        if task_count % num_devs != 0:
            chunk_size += 1

        return [tasks[i:i + chunk_size] for i in range(0, task_count, chunk_size)]
        
    def process_dev(self, dev_id, new_item):
        
        elements = self.load_messages(dev_id)
        elements.append({"role": "user", "content": str(new_item)})
        self.save_messages(dev_id, elements)
        
        self.text_response.append(f"adding dev{dev_id} user inputs...")
        
        response = self.get_response(dev_id, str(new_item))
        
        elements.append({"role": "assistant", "content": response})
        self.save_messages(dev_id, elements)
        self.text_response.append(f"dev{dev_id} tasks completed...")
        
        commands = ast.literal_eval(response)
        
        print(type(commands))
        print(commands)
        
        for command in commands:
            replaced_command = self.formatDirectoryLocation(command['location'])

            if command['code'] != 'No code required':
                for line in command['code'].split('\n'):
                    with open(replaced_command, 'a') as file:
                        file.write(line)
            else:
                self.run_command(command['fileType'],replaced_command)

        
    @pyqtSlot(str)
    def update_text(self, text):
        self.text_response.setPlainText(text)
    
    def get_tasks_value(self):
        while self.running:
            elements_manager = self.load_messages(0)
            
            if elements_manager[-1]['role'] == 'assistant':
                content = ast.literal_eval(elements_manager[-1]['content'])
                if content['status'] == 0:
                    self.text_response.append(f"Total {len(content['tasks'])} tasks created.")
                    self.user_inputs_handler = False
                    
                    # Call the distribute_tasks function
                    self.distribute_tasks(content, num_devs)
                    
                    elements_manager[-1]['content'] = elements_manager[-1]['content'][0:11] + '1' + elements_manager[-1]['content'][12:]
                    
                    self.save_messages(0, elements_manager)
                    
                else:
                    print("No user input...")
    
                self.user_inputs_handler = True
            time.sleep(5)
    
    def start_get_tasks_value_thread(self):
        self.get_tasks_value_thread = GetTasksValueThread(self)
        self.get_tasks_value_thread.start()

        
    def save_messages(self, user_id, messages):
        if user_id == 0:
            with open(self.default_manager_path, 'w') as f:
                json.dump(messages, f)
        elif user_id == 1:
            with open(self.default_dev1_path, 'w') as f:
                json.dump(messages, f)
        else:
            with open(self.default_dev2_path, 'w') as f:
                json.dump(messages, f)


    def load_messages(self, user_id):
        path = ""
        if user_id == 0:
            path = self.default_manager_path
        elif user_id == 1:
            path = self.default_dev1_path
        else:
            path = self.default_dev2_path
            
        # Load the message array from a file
        if os.path.exists(path):
            with open(path, 'r') as f:
                messages = json.load(f)
            return messages
        else:
            return []
        
    def get_response(self, user_id, user_input):

        
        messages = self.load_messages(user_id)
            
        # Send a text query to the OpenAI API
        response = openai.ChatCompletion.create(
          model="gpt-3.5-turbo",
          messages = messages + [
            {"role":"user","content": user_input}]
        )
        
        # Making sure the newly created task runs at least ones.
        if user_id == 0:
            response.choices[0].message.content = response.choices[0].message.content[0:11] + '0' + response.choices[0].message.content[12:]
        
        messages.append({"role": "user", "content": user_input})
        messages.append({"role": "assistant", "content": response.choices[0].message.content})

        # Save the message array to a file
        self.save_messages(user_id, messages)
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
        assistant_response = self.get_response(0, user_query)


    def run_command(self, fileType, command):
        if fileType == 'folder':
            cmd = f'mkdir {command}'
        else:
            cmd = f'type nul > {command}'
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        stdout, stderr = process.communicate()

        if process.returncode == 0:
            print("Command executed successfully!")
            print("Output:\n", stdout.decode())
        else:
            print(cmd)
            print("An error occurred while executing the command.")
            print("Error:\n", stderr.decode())
        


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ai_assistant_ui = AIAssistantUI()
    ai_assistant_ui.show()
    sys.exit(app.exec_())