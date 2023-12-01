from flask import Flask, request, jsonify
import redis
import json
import requests
import os
import openai

# Initialize Flask app
app = Flask(__name__)

# Initialize Redis client
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# OpenAI API setup
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')  # Make sure to set this environment variable

# Function to make API call to GPT-4
def make_api_call(prompt, system_context=None):
    ENDPOINT = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "gpt-4",   
        "messages": [
            {"role": "system", "content": system_context if system_context else "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    }
    
    response = requests.post(ENDPOINT, headers=headers, json=data)
    response_data = response.json()

    if 'choices' in response_data and response_data['choices']:
        message = response_data['choices'][0]['message']['content'].strip()
        return message
    else:
        print(f"Unexpected API response: {response_data}")
        return None

@app.route('/submit-form', methods=['POST'])
def submit_form():
    form_data = request.json
    redis_client.set('form_data', json.dumps(form_data))

    # Constructing the prompt and system context
    project_idea = form_data.get('project_idea')
    user_flow = form_data.get('user_flow')
    tech_stack = form_data.get('tech_stack')
    team_roles = form_data.get('team_roles')
    project_scope = form_data.get('project_scope')
    
    
    redis_client.set('project_idea', project_idea)
    redis_client.set('user_flow', user_flow)
    redis_client.set('tech_stack', tech_stack)
    redis_client.set('team_roles', team_roles)
    
    prompt = f"Generate a full step-by-step outline development plan for creating the app based on the project idea, user flow, tech stack and exclusively on current scope. Return your answer fully in JSON. do not add any text"
    system_context = f"The project idea is {project_idea}. The current user flow is {user_flow}. The tech stack is {tech_stack}. Current scope is: {project_scope}"


    # Make the API call to GPT-4
    outline = make_api_call(prompt, system_context)

    redis_client.set('project_outline', outline)
    return jsonify({'outline': outline})


@app.route('/refine-outline', methods=['POST'])
def refine_outline():
    # Receive refinement data from the Discord bot
    refinement_data = request.json
    user_feedback = refinement_data.get('feedback')
    
    # Fetch the current outline from Redis
    current_outline = redis_client.get('project_outline')
    
    # Construct the prompt for GPT-4
    prompt = f"Refine the following project outline based on user feedback:"
    system_context = f"The current project outline is: {current_outline}. The user feedback is: {user_feedback}."
    
    # Make the API call to GPT-4 for refinement
    refined_outline = make_api_call(prompt, system_context)
    
    # Update the outline stored in Redis
    redis_client.set('project_outline', refined_outline)
    
    # Send the refined outline back to the Discord bot
    return jsonify({'refined_outline': refined_outline})



@app.route('/generate-role-outlines', methods=['POST'])
def generate_role_outlines():
    # Retrieve the general project outline from Redis
    general_outline = redis_client.get('project_outline')

    # The POST request will contain the team roles
    team_roles = request.json.get('team_roles')
    
    role_outlines = {}

    for role in team_roles:
        # The system context includes the general project outline
        system_context = (
                 f"You are an AI that only responds with a JSON response"
                 f"The JSON you return is based on the users input and the context you have. But you only return a JSON"
                 f"This is the context you have: The general project outline is: {general_outline}."
        )

        # The prompt instructs GPT-4 to create a detailed step-by-step plan with a specific JSON structure
        prompt = (
            f"Create a detailed step-by-step plan for a {role}, formatted as a JSON response. "
            f"Include task  task number, title, and sub-tasks for each step. "
            f"Structure the JSON with an array of tasks, where each task is an object with keys "
            f"'task_number', 'task_title', and 'sub_tasks' that contains an array of strings."
        )

        # Make the GPT-4 API call
        role_outline = make_api_call(prompt, system_context=system_context)
        
        # Assume the API returns structured data; parse and save each role's plan
        # Here, it's important to handle the possibility that the return value may not be proper JSON
        try:
            role_outlines[role] = json.loads(role_outline)
        except json.JSONDecodeError:
            print(f"Failed to parse JSON for role: {role}")
            role_outlines[role] = None
            
        # Save the structured role outlines in Redis, handling the case where role_outlines might not be serializable
        try:
            redis_client.set('role_outlines', json.dumps(role_outlines))
        except (TypeError, json.JSONDecodeError):
            print("Failed to serialize role outlines for storage in Redis.")

    
    # Return confirmation to the frontend
    return jsonify({'message': 'Role-specific outlines generated successfully.'})

@app.route('/task-implementation', methods=['POST'])
def task_implementation():
    task_data = request.json
    role = task_data.get('role')
    task_number = task_data.get('task_number')
    
    role_outlines = json.loads(redis_client.get('role_outlines'))
    role_specific_outline = role_outlines.get(role, {})

    # Extract task title and subtitles from the role-specific outline
    task_details = role_specific_outline.get(f"task_{task_number}")
    if not task_details:
        return jsonify({'error': f"No task found with number: {task_number}"}), 404

    task_title = task_details.get('task_title')
    task_subtitles = task_details.get('sub_tasks')
    
    general_outline = redis_client.get('project_outline')

    # Retrieve the role-specific outline from Redis
    
    role_outlines = json.loads(redis_client.get('role_outlines'))
    role_specific_outline = role_outlines.get(role, {})

    # Determine the context based on if it's the first task or a subsequent task
    if task_number == 1:
        system_context =(
            f"You know that this is the fully generated outline for the project: {general_outline}"
            f"This is the fully generated outline for the role specifically: {role_specific_outline} "   
        ) 
        
        
    else:
        # Fetch the context buffer (summary of completed tasks) from Redis
        context_buffer = json.loads(redis_client.get('context_buffer') or '{}')
        
        full_logs_needed = determine_if_full_logs_needed(task_subtitles, task_number, context_buffer)
        
        if full_logs_needed:
            context_buffer = update_context_buffer_with_log2(full_logs_needed, role)
        else:
            context_buffer = context_buffer
                            
        system_context =(
            f"You know that this is the fully generated outline for the project: {general_outline}"
            f"This is the fully generated outline for the role specifically: {role_specific_outline}"   
            f"This is the following needed logs of completed tasks: {context_buffer}."
        ) 

    # Construct the prompt for GPT-4 to generate the implementation details for the task
    prompt = f"Given all you know as context, only return a full implementation for the task with task number: {task_number} titled '{task_title}' given its subtasks where these: {task_subtitles}."

    # Make the API call to GPT-4 for the task implementation
    task_implementation_details = make_api_call(prompt, system_context)

    # Store the task implementation in Redis, keying by role and task number
    redis_client.hset(f"task_implementation_{role}", task_number, task_implementation_details)

    return jsonify({'task_implementation_details': task_implementation_details})


def determine_if_full_logs_needed(task_subtitles, context_buffer, role_specific_outline):
    # Construct the system context for GPT-4
    system_context = (
        f"The role-specific outline for this role is: {json.dumps(role_specific_outline)}. "
        "For each previous task there are two types of logs in the contex : Log 1 contains concise summaries, "
        "and Log 2 contains full implementation details."
        f"This is the current context buffer: {context_buffer}"
    )

    # Construct the prompt for GPT-4
    prompt = (
        "Given the role-specific outline and the context buffer with Log 1 summaries, "
        "determine if the full logs (Log 2) are needed for an accurate generation of the "
        "implementation for the following task subtitles below. If full logs are needed, respond only with a list data structure of the "
        "task numbers for which the detailed logs should be retrieved. Otherwise, respond only with 'No full logs needed'. "
        f"Task subtitles to be impelmented: {task_subtitles}"
    )

    # Make the API call to GPT-4
    response = make_api_call(prompt, system_context)

    # Process the response to identify if full logs are needed
    if response.lower() == 'no full logs needed':
        return []  # Return an empty list if no full logs are required
    else:
        try:
            # Try to parse the response as JSON and return it
            task_numbers = json.loads(response)
            return task_numbers  # Return the list of task numbers requiring full logs
        except json.JSONDecodeError:
            print(f"Failed to parse response as JSON: {response}")
            return []  # Return an empty list if parsing fails


def update_context_buffer_with_log2(task_numbers_needing_log2, role):
    # Fetch the current context buffer
    context_buffer = json.loads(redis_client.get('context_buffer') or '{}')
    
    # Update the context buffer with Log 2 (detailed) summaries for the specified tasks
    for task_number in task_numbers_needing_log2:
        task_key = f"{role}_{task_number}"
        
        # Fetch the Log 2 (detailed) summary for the task
        log2_detailed = redis_client.hget(f"task_summary_{role}", f"{task_number}_log2")
        if log2_detailed:
            # Replace the Log 1 summary with the Log 2 (detailed) summary for the specified task
            context_buffer[task_key] = log2_detailed
        else:
            print(f"Log 2 detailed summary for task {task_number} not found.")
    
    # Save the updated context buffer back to Redis
    redis_client.set('context_buffer', json.dumps(context_buffer))

    return context_buffer


@app.route('/refine-task-implementation', methods=['POST'])
def refine_task_implementation():
    # Receive data from the Discord bot
    refinement_data = request.json
    role = refinement_data.get('role')
    task_number = refinement_data.get('task_number')
    user_feedback = refinement_data.get('feedback')

    # Fetch the current implementation from Redis
    current_implementation = redis_client.hget(f"task_implementation_{role}", task_number)
    
    # Construct the system context and prompt for GPT-4
    system_context = f"The current task implementation for {role} task number {task_number} is: {current_implementation}."
    prompt = f"Based on the user feedback: {user_feedback}, return the complete refined task implementation."

    # Make the API call to GPT-4 for refinement
    refined_implementation = make_api_call(prompt, system_context=system_context)
    
    # Update the task implementation in Redis
    redis_client.hset(f"task_implementation_{role}", task_number, refined_implementation)
    
    # Send the refined implementation back to the user
    return jsonify({'refined_implementation': refined_implementation})


@app.route('/summarize-task', methods=['POST'])
def summarize_task():
    # Receive task details from the Discord bot
    task_data = request.json
    role = task_data.get('role')
    task_number = task_data.get('task_number')
    
    
    task_implementation = redis_client.hget(f"task_implementation_{role}", task_number)
    role_outlines = json.loads(redis_client.get('role_outlines'))
    role_specific_outline = role_outlines.get(role, {})



    # Construct the prompt for GPT-4 to create the summary
    # Define the system context for the AI
    system_context = (
        f"The current role for this task fall under is {role}, working on task number {task_number}."
        f"The full outline for this role's implementation was this: {role_specific_outline}"
        f"You understand our memory system: ""In this hierarchical memory system, Log 1 contains concise, detailed summaries for quick reference, while Log 2 hold the entire implementation details for that task, enabling the system to efficiently access varying levels of information as required for ongoing or subsequent tasks."""
    )

    prompt = (
        f"With the task implementation details provided below, create a hierarchical summary. "
        f"Generate a concise overview (Log 1) that captures the essence of the implementation, "
        f"and a detailed account (Log 2) that includes the entire task implementation information. "
        f"Your response to this should be in JSON with only 'log1' and 'log2' as keys for the respective summaries. "
        f"Task implementation: {task_implementation}"
    )


    # Make the API call to GPT-4 for summarization
    summary = make_api_call(prompt, system_context=system_context)

    # Parse the summary into two logs (assuming the API returns a JSON with two keys: 'log1' and 'log2')
    summary_data = json.loads(summary)
    log1_summary = summary_data.get('log1')
    log2_detailed = summary_data.get('log2')

    # Store the summaries in Redis
    # Save the concise overview (Log 1)
    redis_client.hset(f"task_summary_{role}", f"{task_number}_log1", log1_summary)
    # Save the detailed summary (Log 2)
    redis_client.hset(f"task_summary_{role}", f"{task_number}_log2", log2_detailed)

    # Update the context buffer with the new summary (Log 1)
    context_buffer = json.loads(redis_client.get('context_buffer') or '{}')
    context_buffer[f"{role}_{task_number}"] = log1_summary
    redis_client.set('context_buffer', json.dumps(context_buffer))

    return jsonify({'log1_summary': log1_summary, 'log2_detailed': log2_detailed})


 

@app.route('/')
def index():
    return "Backend for genCollab is running!"

if __name__ == "__main__":
    app.run(debug=True)

