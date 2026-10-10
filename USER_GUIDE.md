# LocalMind: Beginner's User Guide

Welcome to LocalMind! Think of this app as a highly intelligent, private assistant that lives on your computer. You give it access to specific folders, it reads the files inside them, and then you can ask it questions, have it summarize things, or even tell it to organize your files—all using plain English.

Here is everything you need to know, explained simply.

---

## Part 1: How Everything Works

### 1. When I first open LocalMind, what do I see?
You will see a dark, clean workspace divided into two main areas:
*   **The Left Sidebar:** This is your control panel. It shows which folders the app is allowed to look at, and the buttons to make it "read" your files.
*   **The Main Area (Right):** This is where you actually work. Across the top, there are tabs (**Ask**, **Summarize**, **Compare**, **CSV**, **File Ops**, **Activity**, **Files**) that let you choose what kind of task you want to do.

### 2. What does every important button/section do?
*   **Workspace (Sidebar):** Shows the folders you have given the app permission to see.
*   **+ Add Folder (Sidebar):** How you link a new folder from your computer to the app.
*   **Index / Re-index (Sidebar):** These buttons tell the app to open and read your files so it can answer questions about them.
*   **Top Tabs:** Change the mode of the app (e.g., answering questions vs. comparing two documents).

### 3. Where should I click first?
Click **+ Add demo workspace** in the left sidebar. This is the safest way to learn! It creates a safe, temporary folder with fake files for you to play around with without touching your real personal files.

### 4. How do I connect/add a folder?
1. Look at the left sidebar.
2. Click the **+ Add folder** button.
3. Type the exact path to a folder on your computer (for example: `C:\Users\YourName\Documents\Notes`).
4. Click **Authorize**.

### 5. How do I use the Demo Data?
Simply click **+ Add demo workspace** in the sidebar. The app will automatically create a folder filled with sample text files and spreadsheets, and connect it for you. 

### 6. How do I index/re-index files?
Click the green **Index** button at the bottom of the left sidebar. 
*Why do you need to do this?* Even if you connect a folder, the app doesn't automatically read the files. "Indexing" is the process where the app reads the files and stores them in its memory. If you add or change files in your folder later, click **Re-index** to update the app's memory.

### 7. How do I ask questions about my files?
Click the **Ask** tab at the top of the main screen. Type your question in the text box (like "What is our marketing strategy?") and press Enter. The app will read through your indexed files and type out an answer.

### 8. How do I know which files the answer came from?
Right underneath the AI's answer, you will see a box listing its "Sources." It will tell you the exact filename (like `report.txt`) it used to come up with that answer.

### 9. How do I summarize a document?
1. Click the **Summarize** tab at the top.
2. Use the dropdown menu to select one of your files.
3. Click the **Summarize Document** button. The app will read that specific file and give you a short, bulleted summary.

### 10. How do I compare two documents?
1. Click the **Compare** tab at the top.
2. Select your first file from the left dropdown.
3. Select your second file from the right dropdown.
4. Click **Compare Documents**. The app will tell you what they have in common and how they are different.

### 11. How do I analyze a CSV?
*(A CSV is just a simple spreadsheet file).*
1. Click the **CSV** tab at the top.
2. Select your spreadsheet from the dropdown.
3. Type a question about the numbers (like "What was the highest selling item?").
4. Click **Analyze Data**.

### 12. How do I use File Operations?
Click the **File Ops** tab at the top. Instead of clicking menus to move or rename files, you just type what you want to do in plain English. The AI figures out how to do it for you.

### 13. Give me 3-5 exact example commands I can type into File Operations.
*   "Move all .txt files to the Archive folder."
*   "Rename the file notes.txt to final_notes.txt."
*   "Create a new folder called Revision Notes."
*   "Find the sales report and move it into the Finance folder."

### 14. Explain what happens after I submit a file-operation request
LocalMind is built to be extremely safe. It will **never** move or delete files behind your back. It follows a strict 5-step rule:
1.  **Request:** You type what you want ("Move my notes").
2.  **Proposal:** The AI thinks about it and shows you a plan ("I will move `notes.txt` to the `Archive` folder. Is this okay?").
3.  **Confirmation:** You read the plan. If it looks good, you click **Confirm & Execute All**. 
4.  **Execution:** *Only now* does the app actually move your file.
5.  **Verification:** The app double-checks the computer to make sure the file successfully arrived at its new home.

### 15. Explain the Action Log in simple language.
Click the **Activity** tab to see this. The Action Log is just a history book. It keeps a permanent list of every time a file was created, renamed, or moved by the app. If you ever wonder "Did I move that file yesterday?", you can check the log.

### 16. Explain what the Indexed Files section shows.
Click the **Files** tab to see this. It is a simple inventory list. It shows you exactly which files the app has successfully read and placed into its memory. If a file is not on this list, the app cannot answer questions about it.

### 17. Explain what the LLM status means in simple terms.
"LLM" stands for Large Language Model—it is the "AI brain" (in this case, Google Gemini). Look at the bottom of the left sidebar:
*   If it says **Ready**, the brain is awake, connected to the internet, and ready to work.
*   If it shows an error, it means the app is having trouble connecting to the AI brain (usually because you aren't connected to the internet, or an access key is missing).

### 18. Tell me what I should NOT do / common mistakes to avoid.
*   **Mistake:** Forgetting to click "Index". If you add a new file to your folder, the app won't know it exists until you click the green Index button.
*   **Mistake:** Connecting your entire `C:\` drive. The app will try to read thousands of computer system files, which will take forever. Only connect specific folders containing your documents.
*   **Mistake:** Asking the app to do things outside its allowed folders. For your safety, the app is strictly locked into the folders you authorize. It cannot move a file to your Desktop if your Desktop isn't authorized.

---

## Part 2: Hands-On Testing Walkthrough

Follow these tests in order to see exactly how LocalMind works.

### TEST 1: Setup Demo Data
STEP 1: Look at the left sidebar.
STEP 2: Click the button that says "+ Add demo workspace".
EXPECTED RESULT: A new folder path appears under "Workspace", and a small success message pops up saying the demo folder was created.

### TEST 2: Read the Files
STEP 1: Look at the bottom left of the sidebar.
STEP 2: Click the green "Index" button.
EXPECTED RESULT: A progress bar will appear. Within a few seconds, the "Files indexed" number in the sidebar will go from 0 up to a higher number (like 5 or 10).

### TEST 3: Check the Inventory
STEP 1: Click the "Files" tab at the top of the main screen.
STEP 2: Look at the list on the screen.
EXPECTED RESULT: You should see a neat list of all the demo files the app just read (e.g., CSVs and Text files).

### TEST 4: Ask a Question
STEP 1: Click the "Ask" tab at the top of the screen.
STEP 2: Click inside the text box at the bottom of the screen.
TYPE THIS:
"What are these files about?"
EXPECTED RESULT: The AI will write a paragraph explaining the contents of the demo files, and a "Sources" box will appear below it proving which files it read.

### TEST 5: Summarize a File
STEP 1: Click the "Summarize" tab at the top of the screen.
STEP 2: Click the dropdown menu and select any `.txt` file from the list.
STEP 3: Click the "Summarize Document" button.
EXPECTED RESULT: The app will output a short, structured summary with bullet points about that specific document.

### TEST 6: Analyze a Spreadsheet
STEP 1: Click the "CSV" tab at the top of the screen.
STEP 2: Click the dropdown menu and select a `.csv` file.
STEP 3: Click inside the text box.
TYPE THIS:
"What is the most interesting trend in this data?"
STEP 4: Click "Analyze Data".
EXPECTED RESULT: The AI will read the spreadsheet numbers and write out an analysis answering your question.

### TEST 7: Ask an Unanswerable Question
STEP 1: Click the "Ask" tab at the top of the screen.
STEP 2: Click inside the text box at the bottom.
TYPE THIS:
"What is the secret recipe for Coca-Cola?"
EXPECTED RESULT: Because the app is strictly focused on your local files, it should honestly reply that it cannot find that information in your documents.

### TEST 8: Propose a Safe File Operation (Create Folder)
STEP 1: Click the "File Ops" tab at the top of the screen.
STEP 2: Click inside the "Natural Language Request" text box.
TYPE THIS:
"Create a new folder called TestFolder"
STEP 3: Click the "Plan Operations" button.
EXPECTED RESULT: A "Confirm before executing" card will appear. It will clearly show a plan to create `TestFolder`. The file is NOT created yet. 

### TEST 9: Execute a File Operation
STEP 1: Look at the confirmation card generated in Test 8.
STEP 2: Click the primary "Confirm & Execute All" button.
EXPECTED RESULT: The app will show a loading spinner, and then a green "Verified" message will appear, proving the folder was successfully created on your computer.

### TEST 10: Check the Action History
STEP 1: Click the "Activity" tab at the top of the screen.
STEP 2: Look at the log table.
EXPECTED RESULT: You will see a timestamped record proving that you just created "TestFolder". It will say "completed" and "Verified".
