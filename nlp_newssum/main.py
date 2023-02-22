from fastapi import FastAPI, Form, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from pydantic import BaseModel
from typing import Optional, List
import json

import ml_code



app = FastAPI()
templates = Jinja2Templates(directory='')


@app.get('/search')
def get_login_form(request: Request):
    return templates.TemplateResponse('search_results.html', context={'request':request})


# @app.get("/search", response_class=HTMLResponse)
# async def login(request: Request, word:str=Form(...), contents:dict=Form(...)):
#     contents = ml_code.main(word)
#     return templates.TemplateResponse("search_results2.html", {"request": request, "contents": contents})

# @app.post('/search')
# def login(request: Request):
#     word = str('fdas')
#     contents = str('ewrrew')
#     return templates.TemplateResponse("search_results2.html", {"request": request, "word": word, "contents": contents})


@app.post('/search')
def login(request: Request, word:str=Form(...)):
    contents = ml_code.main(word)

    return templates.TemplateResponse("search_results2.html", {"request": request, "word": word, "contents": contents})


# @app.get("/items/{item_name}")
# def read_item(item_name: str):
#     contents = ml_code.main(item_name)
    
#     return contents
