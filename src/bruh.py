import json 

stri = """
{"bob": [{"task_number": 1, "task_title": "Define Project Scope and Requirements for 'bro'", "sub_tasks": ["Specify the 'bro' project details, objectives and deliverables", "Identify the software and hardware requirements", "Outline the project timeline"]}, {"task_number": 2, "task_title": "Design 'bro' App architecture", "sub_tasks": ["Outline the backend structures, APIs, and data management using Django", "Plan the front-end flow for the 'bro' app", "Draft the architecture diagrams"]}, {"task_number": 6, "task_title": "Design User Interface for 'bro'", "sub_tasks": ["Create sketches and wireframes of the user interface", "Design the user interface in more detail using a design tool", "Ask for feedback on the design and implement changes"]}, {"task_number": 8, "task_title": "'bro' Front-End and Back-End Integration", "sub_tasks": ["Integrate the front-end and back-end services of 'bro'", "Test the interaction between front-end and back-end services", "Debug and solve any problems found during testing"]}, {"task_number": 9, "task_title": "Testing 'bro'", "sub_tasks": ["Perform unit testing", "Perform integration testing", "Perform usability testing and fix any issues discovered"]}, {"task_number": 10, "task_title": "Deployment and Monitoring of 'bro'", "sub_tasks": ["Deploy the 'bro' app to a live server", "Monitor its performance and fix bugs", "Provide maintenance and updates as necessary"]}]}
"""

for i in json.loads(stri)['bob'][0].items():
    print(i)
    print([[name, value] for name, value in i])
# print([[name, value] for name, value in json.loads(stri)['bob'][0].items()])