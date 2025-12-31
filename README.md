Student Expense Tracker 💸
A web-based expense tracking application designed to help students manage their daily spending, track monthly budgets, and gain better control over their finances.
📌 Problem Statement
Many students struggle to manage their finances due to:
Lack of visibility into daily and monthly expenses
Difficulty tracking spending by category
No clear comparison between budgeted and actual spending
Limited tools to review expenses over time
This often leads to overspending and poor financial planning.
💡 Solution Overview
The Student Expense Tracker solves this problem by providing:
A simple interface to record and categorise expenses
Monthly budget tracking with remaining balance calculation
Filtering and summary views to analyse spending
Admin functionality to manage and review all users’ expenses
⚙️ Key Features
👤 User Features
Register and log in securely
Add, edit, and delete expenses
Categorise expenses (Food, Transport, Rent, etc.)
Mark expenses as essential or non-essential
View total spending and totals by category
Set a monthly budget
View spent vs remaining budget for the selected month
🛠 Admin (Superuser) Features
View expenses for all users
Filter expenses by user, category, date, and essential status
View monthly budgets for individual users
Edit or delete any user’s expenses
Budget input is hidden in admin view (read-only monitoring)
🧭 How to Use the App
1️⃣ Registration & Login
New users can register using the Register page
Existing users log in via the Login page
2️⃣ Adding Expenses
Click + Add Expense
Enter amount, category, description, date, and essential status
Save to record the expense
3️⃣ Viewing & Filtering Expenses
Use filters at the top of the Expenses page:
Category
Date range
Essential / Non-essential
Admin users can also filter by User
4️⃣ Monthly Budget
Enter a monthly budget for the selected month
View:
Total spent
Remaining budget (shown in red if exceeded)
🔑 Test Login Details
👤 Normal User
Username: user1
Password: password123
🛠 Admin User
Username: admin
Password: admin123
⚠️ These accounts are for demonstration and assessment purposes only.
🧪 Testing
The application was tested using:
Manual functional testing
Input validation checks
Role-based access testing (user vs admin)
Budget calculation edge cases
UI behaviour for empty and over-budget states
Test plans and results are included in the project documentation.
🗂 Project Structure
Student_expense_tracker/
│
├── app.py
├── expenses.db
├── templates/
│   ├── expenses.html
│   ├── add_expense.html
│   ├── login.html
│   └── register.html
├── static/
│   └── css/style.css
├── requirements.txt
└── README.md
🚀 Technologies Used
Python (Flask)
SQLite
HTML5 / CSS3
Bootstrap
Jinja2 Templates
Git & GitHub
📈 Development Progress
Initial expense tracking features implemented
User authentication and role-based access added
Category management completed
Monthly budget tracking implemented
Admin dashboard enhancements
UI improvements and bug fixes
Testing and documentation completed
🔗 GitHub Repository
👉 https://github.com/Saedindho/Expense_tracker
🤖 AI Transparency Declaration
AI tools (ChatGPT) were used to:
Assist with debugging
Improve code structure
Generate documentation drafts
All code was reviewed, tested, and understood by the student before submission.
