from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import SignUpForm, AddRecordForm, PokemonForm
from .models import Record
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain import LLMChain
from .serializers import RecordSerializer
from django.views.decorators.csrf import csrf_exempt
import requests
import os
import json

OPEN_API_KEY = os.environ.get('OPENAI_API_KEY')
llm = ChatOpenAI(temperature=0.9, openai_api_key=OPEN_API_KEY, model='gpt-3.5-turbo')

def home(request):
	records = Record.objects.all()
	# Check to see if logging in
	if request.method == 'POST':
		username = request.POST['username']
		password = request.POST['password']
		# Authenticate
		user = authenticate(request, username=username, password=password)
		if user is not None:
			login(request, user)
			messages.success(request, "You Have Been Logged In!")
			return redirect('home')
		else:
			messages.success(request, "There Was An Error Logging In, Please Try Again...")
			return redirect('home')
	else:
		return render(request, 'home.html', {'records':records})



def logout_user(request):
	logout(request)
	messages.success(request, "You Have Been Logged Out...")
	return redirect('home')


def register_user(request):
	if request.method == 'POST':
		form = SignUpForm(request.POST)
		if form.is_valid():
			form.save()
			# Authenticate and login
			username = form.cleaned_data['username']
			password = form.cleaned_data['password1']
			user = authenticate(username=username, password=password)
			login(request, user)
			messages.success(request, "You Have Successfully Registered! Welcome!")
			return redirect('home')
	else:
		form = SignUpForm()
		return render(request, 'register.html', {'form':form})

	return render(request, 'register.html', {'form':form})



def customer_record(request, pk):
	if request.user.is_authenticated:
		# Look Up Records
		customer_record = Record.objects.get(id=pk)
		return render(request, 'record.html', {'customer_record':customer_record})
	else:
		messages.success(request, "You Must Be Logged In To View That Page...")
		return redirect('home')



def delete_record(request, pk):
	if request.user.is_authenticated:
		delete_it = Record.objects.get(id=pk)
		delete_it.delete()
		messages.success(request, "Record Deleted Successfully...")
		return redirect('home')
	else:
		messages.success(request, "You Must Be Logged In To Do That...")
		return redirect('home')


def add_record(request):
    desc_form = PokemonForm(request.POST or None)
    form = AddRecordForm(request.POST or None)
    if request.user.is_authenticated:
        if request.method == "POST":
            if form.is_valid():
                add_record = form.save()
                messages.success(request, "Record Added...")
                return redirect('home')
        return render(request, 'add_record.html', {'form': form, 'desc_form': desc_form})
    else:
        messages.success(request, "You Must Be Logged In...")
        return redirect('home')


def update_record(request, pk):
	if request.user.is_authenticated:
		current_record = Record.objects.get(id=pk)
		form = AddRecordForm(request.POST or None, instance=current_record)
		if form.is_valid():
			form.save()
			messages.success(request, "Record Has Been Updated!")
			return redirect('home')
		return render(request, 'update_record.html', {'form':form})
	else:
		messages.success(request, "You Must Be Logged In...")
		return redirect('home')

def voice_add(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            desc_form = PokemonForm(request.POST)
            if desc_form.is_valid():
                input_text = desc_form.cleaned_data['describe_pokemon']
                template = '''You are embedded in a pokedex tool that enables pokemon trainers to leave a
short voice memo about a pokemon. Utilize the text from the voice memo to guess the name of the Pokemon. 
If the pokemon cannot be guessed, return 'NA'.

Here's the json response format.

"name": "",
"description": ""

Only provide the pokemon name and a description in the above json format, no other text in the answer, here is the text:

{text}'''

                prompt = PromptTemplate(
                    input_variables=["text"],
                    template=template)
                llm_chain = LLMChain(prompt=prompt, llm=llm)
                response = llm_chain.run({
                    "text": input_text,
                })

                pokemon_data = json.loads(response)
                pokemon_name = pokemon_data['name'].lower()
                pokemon_description = pokemon_data['description']

                response = requests.get(f'https://pokeapi.co/api/v2/pokemon/{pokemon_name}')
                
                if response.status_code == 200:
                    resp_data = response.json()
                    table_data = {
                        'id': resp_data['id'],
                        'name': resp_data['name'],
                        'experience': resp_data['base_experience'],
                        'height': resp_data['height'],
                        'image_url': resp_data['sprites']['other']['dream_world']['front_default'] if resp_data['sprites']['other']['dream_world']['front_default'] else resp_data['sprites']['other']['home']['front_default'],
                        'description': pokemon_description
                    }
                    serializer = RecordSerializer(data=table_data)
                    if serializer.is_valid():
                        serializer.save()
                        messages.success(request, "Record Added...")
                        return redirect('record', pk=table_data['id'])
                    else:
                        messages.error(request, "Record Not Added...")
                else:
                    messages.error(request, "Pokemon not found...")
        else:
            desc_form = PokemonForm()
        return render(request, 'add_record.html', {'desc_form': desc_form})
    else:
        messages.success(request, "You Must Be Logged In...")
        return redirect('home')
