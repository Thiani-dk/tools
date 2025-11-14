Running the Tool in VS Code
Open the Terminal: In VS Code, go to Terminal > New Terminal (or press `Ctrl+``).

Create a Virtual Environment: This creates an isolated sandbox for our project's libraries.


python -m venv .venv
(You might see a .venv folder appear. VS Code may also ask if you want to use it—say yes!)

Activate the Environment:

On Windows (PowerShell/CMD):
.\.venv\Scripts\activate

On Mac/Linux (bash/zsh):
source .venv/bin/activate
(You'll know it worked because your terminal prompt will change to show (.venv) at the beginning.)


Install Dependencies: Now install all the libraries from our requirements.txt file into this environment.


pip install -r requirements.txt


Run the Tool! Now you're ready to run the main script.
python src/main.py

The script will start, and you'll see the welcome message and prompts!