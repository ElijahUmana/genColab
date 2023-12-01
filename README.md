# genCollab 

<img width="978" alt="Screenshot 2023-12-01 at 3 17 15 PM" src="https://github.com/ElijahUmana/genCollab/assets/121345656/8a090346-4fed-4d5f-8203-8a5f4e31c3cc">

## Overview

genCollab is an innovative AI-powered tool designed to transform how engineering teams collaborate on coding projects.  It extends beyond individual coding assistance, offering a scalable, collaborative environment. Unlike traditional code generators, genCollab emphasizes collaborative features, integrating a unique "Hierarchical Memory" system for superior context retention and project alignment. This tool is integrated with Discord, providing an interactive and seamless experience for team development.

## Features

- **Hierarchical Memory System**: Organizes context in a tree-like structure, allowing for dynamic expansion and efficient context management.
- **Discord Integration**: Seamlessly integrated within Discord, enhancing team communication and collaboration.
- **Intelligent Task Allocation**: Automatically develops roadmaps and allocates tasks based on roles.
- **Scalable Code Generation**: Generates code that aligns with the project's overarching goals and easily integrates into the existing codebase.


<img width="1160" alt="Screenshot 2023-12-01 at 1 24 35 PM" src="https://github.com/ElijahUmana/genCollab/assets/121345656/efc64d9e-15ce-4efc-a03a-74e6c5c4b9ba">

## Workflow

1. **Initial Setup**: Users submit a form via a Discord bot, detailing the project idea, user flow, tech stack, and team roles.
2. **Outline Generation**: The system uses GPT-4 to create a detailed project outline, which is stored and sent back to the user.
3. **Outline Refinement**: Users can refine the outline by submitting feedback, which is processed to update the outline.
4. **Role-Specific Plans**: Upon receiving the .done command, the system generates a detailed, role-specific plan for each team member.
5. **Task Implementation**: Team members can request implementation details for specific tasks, which are generated and refined as needed.
6. **Hierarchical Memory Summarization**: After task completion, the system summarizes the implementation in two tiers, enabling efficient recall and context management.

## Technical Implementation

- **Frontend**: Created using [discord.py](http://dicord.py) library.
- **Backend**: Developed with Flask, employing NLP techniques for real-time code generation and ensuring syntactical and logical coherence.
- **Storage and Caching**: Utilizes Redis for efficient data handling and temporary caching.

## Getting Started
1. **Set Up Discord Bot**: Utilize discord.py to interact with GenCollab through Discord.
2. **Deploy Flask Backend**: Host the Flask application to manage requests and AI interactions.
3. **Configure Redis**: Set up Redis for data storage and caching.
