from main import models
import google.generativeai as genai
import json
from langchain_community.document_loaders import WebBaseLoader
from Analyzer import settings
from django.core.management.base import BaseCommand
import time
genai.configure(api_key = settings.GEMINI_KEY)

model = genai.GenerativeModel("gemini-1.5-flash")
from openai import OpenAI
client = OpenAI(
    # defaults to os.environ.get("OPENAI_API_KEY")
    api_key=settings.OPEN_AI_KEY,
)



def newser():
    
    for site in models.NewsSite.objects.all().order_by('-id'):
        print(site.name)
        jsons = {}
        for service in models.NewsService.objects.all():
            link = models.NewsLink.objects.get(site= site, service=service)
            loader = WebBaseLoader(
                        web_path = link.url
                    )
            
            jsons[str(service.id)] = {}
            for subservice in models.NewsSubService.objects.all():
                try:
                    prompt = service.prompt
                    prompt = prompt + subservice.prompt
                    
                    prompt = prompt + '\n اخبار به دست آمده را به صورت فقط یک لیست جیسون بدون اضافات و توضیحات ارایه کن . هر آیتم لیست باید دارای دو فیلد title , text  باشد . دقت کن که تیتر کوتاه و متن بلند باشد \n'
                    prompt = prompt + '\n  . اگر بخشی از متن با سیاست های شما مشکل داشت آن را در نظر نگیر و ادامه بده \n'
                    prompt = prompt + f"متن خبر : {str(loader.load())}"
                    completion = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                                {"role": "system", "content": "You are a News Analyzer."},
                                {
                                    "role": "user",
                                    "content": prompt
                                }
                            ]
                        )
                    response = completion.choices[0].message.content.replace('json', '').replace('```', '').replace('```', '')
                    # response = model.generate_content(prompt).text.replace('json', '').replace('```', '').replace('```', '')
                    response = json.loads(response)
                    jsons[str(service.id)][str(subservice.id)] = response
                except:
                    try:
                        prompt = service.prompt
                        prompt = prompt + subservice.prompt
                        
                        prompt = prompt + '\n اخبار به دست آمده را به صورت فقط یک لیست جیسون بدون اضافات و توضیحات ارایه کن . هر آیتم لیست باید دارای دو فیلد title , text  باشد . دقت کن که تیتر کوتاه و متن بلند باشد ولی از ۲۰۰ کاراکتر بیشتر نشود\n'
                        prompt = prompt + '\n  . اگر بخشی از متن با سیاست های شما مشکل داشت آن را در نظر نگیر و ادامه بده \n'
                        prompt = prompt + f"متن اصلی : {str(loader.load())}"
                        completion = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                    {"role": "system", "content": "You are a News Analyzer."},
                                    {
                                        "role": "user",
                                        "content": prompt
                                    }
                                ]
                            )
                        response = completion.choices[0].message.content.replace('json', '').replace('```', '').replace('```', '')
                        # response = model.generate_content(prompt).text.replace('json', '').replace('```', '').replace('```', '')
                        response = json.loads(response)
                        jsons[str(service.id)][str(subservice.id)] = response
                    except:
                        jsons[str(service.id)][str(subservice.id)] = {}
        print('Done')
        site.json = jsons
        site.save()

class Command(BaseCommand):
    def handle(self, *args, **options):
            # get_news()
            newser()
