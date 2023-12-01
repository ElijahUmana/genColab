import settings
import discord
from discord import app_commands
from discord.ext import commands
import traceback, json, openai, settings, requests
import re 

openai.api_key = "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"

def send_request(endpoint, data):
    url = f'http://127.0.0.1:5000/{endpoint}'
    response = requests.post(url, json=data)
    return response.json()

def get_request(endpoint):
    url = f'http://127.0.0.1:5000/{endpoint}'
    response = requests.post(url)
    return response.json()

class FeedbackModal(discord.ui.Modal, title="Make Project!"):
    tit = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="Project Title",
        required=True,
        placeholder="Title of your project."
    )

    descrip = discord.ui.TextInput(
        style=discord.TextStyle.long,
        label="Project Description",
        required=True, 
        max_length=1000,
        placeholder="Describe your project in 500 characters or less."
    )

    flow = discord.ui.TextInput(
        style=discord.TextStyle.long,
        label="User flow",
        required=True, 
        max_length=1000,
        placeholder="How should a user interact with your app?"
    )

    stack = discord.ui.TextInput(
        style=discord.TextStyle.long,
        label="Tech Stack",
        required=True,
        max_length=200,
        placeholder="What tech stack did you want to use? Seperate by commas."
    )

    roles = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="Member Roles",
        required=True,
        max_length=100,
        placeholder="What are the roles of members in your team? Seperate by commas."
    )

    async def on_submit(self, interaction: discord.Interaction):
        await self.create_project(interaction.guild)


      
    async def create_project(self, guild):

        role_names = self.roles.value.split(',')
        roles = await self.create_roles(guild, role_names)

        main_category_name = self.tit.value
        main_category = await self.create_category(guild, main_category_name, roles, False)

        form_data = {
            'title': self.tit.value,
            'project_idea': self.descrip.value,
            'user_flow': self.flow.value,
            'tech_stack': self.stack.value,
            'team_roles': self.roles.value,
        }

        channel = await self.create_text_channel(guild, "outline", main_category, send_messages=False, roles=roles)

        messa = f"**Project Name:** {self.tit.value}\n**Project Description:** {self.descrip.value}\n**Tech Stack:** {self.stack.value}\n**Roles:** {self.roles.value}"
        embed = discord.Embed(title="Project Details", color=discord.Color.blurple(),
                              description=messa)
        await guild.get_channel(1166928199603736739).send(embed=embed)
        outline = send_request('submit-form', form_data)['outline']

        embed = discord.Embed(title="Outline", color=discord.Color.blurple(),
                      description='```\n' + outline + '\n```')
        await channel.send(embed=embed)
        
        role_emoji_mapping = await self.create_role_assignment_channel(guild, main_category, roles)
        print(role_emoji_mapping)
        with open(r'C:\AA-Codebench\hacks\genCollab\src\mapping.txt', 'w') as file: 
           json.dump(role_emoji_mapping, file)  
        print(type(role_emoji_mapping))
        form_data['emoji_role_mapping'] = json.dumps(role_emoji_mapping)

        status = send_request('update-form', form_data)
        return 1 
    
    async def create_roles(self, guild, role_names):
      roles = {}
      for name in role_names:
          role = await guild.create_role(name=name)
          roles[name] = role
      return roles

    async def create_category(self, guild, category_name, roles, default_role_read_false):
        if default_role_read_false: 
          overwrites = {
              guild.default_role: discord.PermissionOverwrite(read_messages=False)  
          }
        else: 
          overwrites = {}
        
        for role_name, role in roles.items():
            overwrites[role] = discord.PermissionOverwrite(read_messages=True)

        category = await guild.create_category(name=category_name, overwrites=overwrites)
        return category


    async def create_text_channel(self, guild, name, category, send_messages=False, roles=None):
      overwrites = {}
      if roles:
          for role in roles.values():
              overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=send_messages)

      channel = await guild.create_text_channel(name=name, category=category, overwrites=overwrites)
      return channel
    

    async def create_role_assignment_channel(self, guild, main_category, roles):
      role_assignment_channel = await guild.create_text_channel(name='role-assignment', category=main_category)

      role_emoji_mapping = await self.map_roles_to_emojis(roles)

      text = ""
      for emoji in role_emoji_mapping: 
         text += f"Hit {emoji} for {role_emoji_mapping[emoji]}\n"

      embed = discord.Embed(title="Role Assignment", description=f"React to get a role!\n{text}", color=discord.Color.green())
      role_message = await role_assignment_channel.send(embed=embed)

      for emoji, _  in role_emoji_mapping.items():
          await role_message.add_reaction(emoji)

      return role_emoji_mapping

    async def map_roles_to_emojis(self, role_names):
        roles = role_names
        role_names = list(roles.keys())
        emoji_list = ['🍎', '🍌', '🍇', '🍉', '🍒', '🍓', '🍍', '🥑', '🥦', '🥕']

        return {emoji: role_name for role_name, emoji in zip(role_names, emoji_list[:len(role_names)])}

    
    async def on_error(self, interaction: discord.Interaction, error : Exception):
        traceback.print_exc()

    

def run(): 
  intents =  discord.Intents.all()

  bot = commands.Bot(command_prefix='.', intents=intents)

  @bot.event
  async def on_ready(): 
    bot.tree.copy_global_to(guild=settings.GUILDS_ID)
    await bot.tree.sync(guild=settings.GUILDS_ID)

  @bot.command(
      brief='Answers with pong',
  )
  async def ping(ctx): 
    """ Answers with pong """
    await ctx.send('pong')

  @bot.tree.command()
  async def make_project(interaction: discord.Interaction):
      feedback_modal = FeedbackModal()
      feedback_modal.user = interaction.user
      await interaction.response.send_modal(feedback_modal)

  @bot.tree.command(name='refine_output')
  @app_commands.describe(feedback = "What should change about the outline?")
  async def refine(interaction: discord.Interaction, feedback: str):
    channel = interaction.channel
    
    if str(channel).lower() == "outline": 
        await interaction.response.send_message("Refining output... This takes a second", ephemeral=True)

        refinement_data = {
            'feedback': feedback
        }
        refined_outline = send_request('refine-outline', refinement_data)['refined_outline']
      
        await channel.purge()
        embed = discord.Embed(title="Outline", color=discord.Color.blurple(),
                        description='```\n' + refined_outline + '\n```')
        embed.set_author(name=interaction.user.nick)
        await channel.send(embed=embed)

  @bot.tree.command(name='approved')
  async def approved(interaction: discord.Interaction):


    channel = interaction.channel
    if str(channel).lower() == "outline":
        await interaction.response.send_message("Making the dashboards!", ephemeral=True)
        everyone_role = discord.utils.get(interaction.guild.roles, name="@everyone")
        await channel.set_permissions(everyone_role, send_messages=False)
        form_data = send_request('get-form-data', {'sample': 'sample'})['form_data']
        feedback_modal = FeedbackModal()
        title = form_data['title']
        emoji_role_mapping = form_data['emoji_role_mapping']
        tasks = form_data['project_outline']

        
        for emoji in emoji_role_mapping:
            role_name = emoji_role_mapping[emoji]
            role = discord.utils.get(interaction.guild.roles, name=role_name)
            category_name = f"{title} : {role_name}"
            category = await feedback_modal.create_category(interaction.guild, category_name, {role_name: role}, True)

            role_outline = send_request('generate-role-outlines', {'role': emoji_role_mapping[emoji]})
            role_outline = json.loads(role_outline['role_outline'])

            with open(r'C:\AA-Codebench\hacks\genCollab\src\check.txt', 'w') as file: 
                json.dump(role_outline, file)

            # def extract_and_convert_to_json(text):
            #     # Define the regex pattern to capture content between ``` and a newline, and ```
            #     pattern = re.compile(r'```(.*?)\n(.*?)```', re.DOTALL)
            #     # Search for the pattern in the text
            #     match = pattern.search(text)
            #     if match:
            #         # If a match is found, get the matched string, and remove leading/trailing whitespaces
            #         json_string = match.group(2).strip()
            #         # Convert the string to a JSON object
            #         json_object = json.loads(json_string)
            #         return json_object
            #     else:
            #         raise ValueError("No JSON found")
    
            # role_outline = extract_and_convert_to_json(str(role_outline))

            for x in role_outline['bob'][0]:
                for task_key, task_value in x.items(): 
                    channel_name = f"{task_key.replace('.', '_')}_{task_value['title'].replace(' ', '_')}"
                    channel = await feedback_modal.create_text_channel(feedback_modal.guild, channel_name, category, send_messages=True, roles={role_name: role})
                    embed = discord.Embed(color=discord.Color.red(),
                        description=json.dumps(task_value, indent=4))
                    embed.set_author(name=feedback_modal.user.nick)
                    await channel.send(embed=embed)
        

  @bot.event
  async def on_raw_reaction_add(payload):
      channel = bot.get_channel(payload.channel_id)
      if channel.name == 'role-assignment':
          guild = discord.utils.get(bot.guilds, id=payload.guild_id)
          emoji_list = ['🍎', '🍌', '🍇', '🍉', '🍒', '🍓', '🍍', '🥑', '🥦', '🥕']
          with open(r'C:\AA-Codebench\hacks\genCollab\src\mapping.txt', 'r') as file: 
             role_emoji_mapping = json.loads(file.read())
          role_name = role_emoji_mapping[payload.emoji.name] 
          role = discord.utils.get(guild.roles, name=role_name)
          if role:
              user = guild.get_member(payload.user_id)
              await user.add_roles(role)

  bot.run(settings.DISCORD_API_SECRET, root_logger = True)

if __name__=="__main__": 
  run()