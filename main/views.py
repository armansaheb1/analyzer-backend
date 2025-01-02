from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from . import models
from . import serializers
import urllib.request
from urllib.request import urlopen
import json
import time
import google.generativeai as genai
import os
import json
from rest_framework.authentication import (
    
    BasicAuthentication,
    TokenAuthentication,
)
from rest_framework.permissions import IsAuthenticated, AllowAny
import sys
import threading
import time
import requests
from Analyzer import settings
from openai import OpenAI
client = OpenAI(
    # defaults to os.environ.get("OPENAI_API_KEY")
    api_key=settings.OPEN_AI_KEY,
)
# from langchain_community.document_loaders import AsyncHtmlLoader, RSSFeedLoader
# from llama_index.core import SimpleDirectoryReader, GPTVectorStoreIndex, StorageContext, load_index_from_storage
# from llama_index.core import Settings
# from llama_index.embeddings.openai import OpenAIEmbedding
# from llama_index.core.node_parser import SentenceSplitter
# from llama_index.llms.openai import OpenAI
# from llama_index.core import Settings
from Analyzer import settings
from langchain_community.document_loaders import WebBaseLoader
genai.configure(api_key = settings.GEMINI_KEY)

model = genai.GenerativeModel("gemini-1.5-flash")


def newser(ids, modeled):
    modeled = models.NewsResult.objects.get(id = modeled)
    
    service = models.NewsService.objects.get(id=ids)
    loader = WebBaseLoader(
        web_path = service.category.url
    )

    prompt = service.prompt
    prompt = prompt.replace(
        "$link", f"متن اصلی : {str(loader.load())}"
    )
    prompt = prompt + '\n اخبار به دست آمده را به صورت فقط یک لیست جیسون بدون اضافات و توضیحات ارایه کن . هر آیتم لیست باید دارای دو فیلد title , text  باشد . دقت کن که تیتر کوتاه و متن بلند باشد ولی از ۲۰۰ کاراکتر بیشتر نشود\n'
    response = model.generate_content(prompt)
    modeled.json = json.loads(response.text.replace('json', '').replace('```', '').replace('```', ''))
    print(modeled)
    modeled.save()

def get_social(subject):
    pass


def get_news(subject):
    today = ""
    for itemm in models.NewsSite.objects.all().order_by("-id"):
        fp = urllib.request.urlopen(itemm.url)
        mybytes = fp.read()

        mystr = mybytes.decode("utf8")
        print(itemm.url)
        fp.close()
        today = today + mystr + "\n\n\n"

        prompt = f"content related to {subject} as only a json with pic,description and title based on {today} "
    response = model.generate_content(prompt).text
    
    response = response.replace("```json", "").replace("```", "")
    print(response)
    response = json.loads(response)
    for itemm in response:
        if "title" in itemm and "pic" in itemm and "description" in itemm:
            if not len(models.NewsReport.objects.filter(pic=itemm["pic"])):
                models.NewsReport.objects.create(
                    title=itemm["title"],
                    text=itemm["description"],
                    pic=itemm["pic"],
                    subject=subject,
                )


class NewsSites(APIView):
    def get(self, request):
        query = models.NewsSite.objects.all()
        serializer = serializers.NewsSiteSerializer(query, many=True)
        return Response(serializer.data)


class Categories(APIView):
    def get(self, request):
        query = models.Category.objects.all()
        serializer = serializers.CategorySerializer(query, many=True)
        return Response(serializer.data)

    def post(self, request, id):
        query = models.Category.objects.filter(template = 3)
        serializer = serializers.CategorySerializer(query, many=True)
        return Response(serializer.data)

class NewsCategories(APIView):
    def get(self, request):
        query = models.NewsService.objects.all()
        serializer = serializers.NewsServiceSerializer(query, many=True)
        return Response(serializer.data)


class ServicesOne(APIView):
    def get(self, request, slug):
        query = models.Service.objects.get(slug=slug)
        serializer = serializers.UserServiceSerializer(query)
        return Response(serializer.data)


class Services(APIView):
    def get(self, request):
        query = models.Service.objects.all()
        serializer = serializers.UserServiceSerializer(query, many=True)
        return Response(serializer.data)
    
class FormatServices(APIView):
    def get(self, request):
        query = models.FormatService.objects.all()
        serializer = serializers.FormatServiceSerializer(query, many=True)
        return Response(serializer.data)
    
class RebuildServices(APIView):
    def get(self, request):
        query = models.RebuildService.objects.all()
        serializer = serializers.RebuildServiceSerializer(query, many=True)
        return Response(serializer.data)


class OccasionServices(APIView):
    def get(self, request):
        query = models.OccasionService.objects.all()
        serializer = serializers.OccasionServiceSerializer(query, many=True)
        return Response(serializer.data)


class NewsServices(APIView):
    def get(self, request):
        query = models.NewsService.objects.all().order_by('-id')
        serializer = serializers.NewsServiceSerializer(query, many=True)
        return Response(serializer.data)

class NewsSubServices(APIView):
    def get(self, request):
        query = models.NewsSubService.objects.all().order_by('-id')
        serializer = serializers.NewsSubServiceSerializer(query, many=True)
        return Response(serializer.data)
    

class ImageServices(APIView):
    def get(self, request):
        query = models.ImageService.objects.all().order_by('-id')
        serializer = serializers.ImageServiceSerializer(query, many=True)
        return Response(serializer.data)

class NewsIntrests(APIView):
    def get(self, request):
        query = models.NewsIntrest.objects.filter(user=request.user).order_by('-id')
        serializer = serializers.NewsIntrestSerializer(query, many=True)
        return Response(serializer.data)
    def post(self, request):
        serializer = serializers.NewsIntrestSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user = request.user)
        query = models.NewsIntrest.objects.filter(user=request.user).order_by('-id')
        serializer = serializers.NewsIntrestSerializer(query, many=True)
        x = threading.Thread(target=get_news_gpt, args=(request.data['subject'],request.user))
        x.start()
        return Response(serializer.data)
    
    def delete(self, request, id):
        query = models.NewsIntrest.objects.get(id=id).delete()
        query = models.NewsIntrest.objects.filter(user=request.user).order_by('-id')
        serializer = serializers.NewsIntrestSerializer(query, many=True)
        return Response(serializer.data)


class Tones(APIView):
    def get(self, request):
        query = models.Tone.objects.all().order_by('-id')
        serializer = serializers.ToneSerializer(query, many=True)
        return Response(serializer.data)
    
class IdeaEntries(APIView):
    def get(self, request):
        query = models.IdeaStaticEntry.objects.all().order_by('-id')
        serializer = serializers.IdeaStaticEntrySerializer(query, many=True)
        return Response(serializer.data)

class StaticEntries(APIView):
    def get(self, request):
        query = models.StaticEntry.objects.all().order_by('-id')
        serializer = serializers.StaticEntrySerializer(query, many=True)
        return Response(serializer.data)


class Formats(APIView):
    def get(self, request):
        query = models.Format.objects.all().order_by('-id')
        serializer = serializers.FormatSerializer(query, many=True)
        return Response(serializer.data)

class SocialIntrests(APIView):
    def get(self, request):
        query = models.SocialIntrest.objects.all().order_by('-id')
        serializer = serializers.SocialIntrestSerializer(query, many=True)
        return Response(serializer.data)
    def post(self, request):
        serializer = serializers.SocialIntrestSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user = request.user)
        query = models.SocialIntrest.objects.all().order_by('-id')
        serializer = serializers.SocialIntrestSerializer(query, many=True)
        x = threading.Thread(target=get_social, args=(request.data['subject'],))
        x.start()
        return Response(serializer.data)
    
    def delete(self, request, id):
        query = models.SocialIntrest.objects.get(id=id).delete()
        query = models.SocialIntrest.objects.all().order_by('-id')
        serializer = serializers.SocialIntrestSerializer(query, many=True)
        return Response(serializer.data)


class Reports(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if len(models.NewsIntrest.objects.filter(user= request.user)) < 1:
            return Response(1)
        else:
            query = models.NewsReport.objects.filter(user= request.user).order_by('-id')
            serializer = serializers.NewsReportSerializer(query, many=True)
            return Response(serializer.data)

class SocialReports(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if len(models.SocialIntrest.objects.filter(user= request.user)) < 1:
            return Response(1)
        else:
            query = models.NewsReport.objects.all().order_by('-id')
            serializer = serializers.NewsReportSerializer(query, many=True)
            return Response(serializer.data)

class GPTBuilder(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        import logging
        logger = logging.getLogger('django')
        
        query = models.Service.objects.get(slug=slug)
        prompt = query.prompt
        prompt = prompt + '\n return result as only a responsive html text without pictures and code details with maximum header of h4 \n'
        for item in query.static_variables.all():
            if request.data["data2"]['n' + str(item.id)]:
                prompt = prompt + '\n' + item.prompt.replace('$entry', request.data["data2"]['n' + str(item.id)])
        prompt = prompt + '\n متن اصلی : \n' + request.data["maintext"]
        completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
        response = completion.choices[0].message.content
        # response = model.generate_content(prompt)
        return Response(response)



class GBuilder(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        import logging
        logger = logging.getLogger('django')

        query = models.Service.objects.get(slug=slug)
        prompt = query.prompt
        prompt = prompt + "\n به فرمت h6,b,p تبدیل کن. اطمینان حاصل کن که متن به پاراگراف‌های مناسب با تگ‌های <p> تقسیم شده و برای تمام عناوین از تگ <h6> استفاده شود و تمام تگ ها justify باشد. برای جدا تمام کردن پاراگراف‌ها و هدر ها از تگ <br> استفاده کن.\n"
        prompt = prompt + 'بدون توضیحات و اضافات'
        for item in query.static_variables.all():
            if request.data["data2"]['n' + str(item.id)]:
                prompt = prompt + '\n' + item.prompt.replace('$entry', request.data["data2"]['n' + str(item.id)])
        for item in query.variables:
            prompt = prompt.replace('$' + item["slug"], request.data["data"][item["slug"]])
        
        prompt = prompt + '\n متن اصلی : \n' + request.data["maintext"]
        
        logger.info(prompt)
        
        completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
        response = completion.choices[0].message.content
        # response = model.generate_content(prompt)
        return Response(response)


class GBuilderWrite(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        import logging
        logger = logging.getLogger('django')
        query = models.StaticEntry.objects.all()

        prompt = "\n به فرمت h6,b,p تبدیل کن. اطمینان حاصل کن که متن به پاراگراف‌های مناسب با تگ‌های <p> تقسیم شده و برای تمام عناوین از تگ <h6> استفاده شود و تمام تگ ها justify باشد. برای جدا تمام کردن پاراگراف‌ها و هدر ها از تگ <br> استفاده کن.\n"
        prompt = prompt + 'بدون توضیحات و اضافات'
        for item in query:
            if request.data["data2"]['n' + str(item.id)]:
                prompt = prompt + '\n' + item.prompt.replace('$entry', request.data["data2"]['n' + str(item.id)])
        prompt = prompt + '\n متن اصلی : \n' + request.data["maintext"]
        
        logger.info(prompt)
        completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
        response = completion.choices[0].message.content
        # response = model.generate_content(prompt)
        return Response(response)
class GBuilderRebuild(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        query = models.RebuildService.objects.get(id = id)

        prompt = "\n به فرمت h6,b,p تبدیل کن. اطمینان حاصل کن که متن به پاراگراف‌های مناسب با تگ‌های <p> تقسیم شده و برای تمام عناوین از تگ <h6> استفاده شود و تمام تگ ها justify باشد. برای جدا تمام کردن پاراگراف‌ها و هدر ها از تگ <br> استفاده کن.\n"
        prompt = prompt + 'بدون توضیحات و اضافات'
        prompt = prompt + query.prompt
        prompt = prompt + '\n متن اصلی : \n' + request.data["text"]
        
        completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
        response = completion.choices[0].message.content
        # response = model.generate_content(prompt)
        return Response(response.replace('```html','').replace('```',''))

class GBuilderFormat(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        query = models.FormatService.objects.get(id = id)

        prompt = "\n به فرمت h6,b,p تبدیل کن. اطمینان حاصل کن که متن به پاراگراف‌های مناسب با تگ‌های <p> تقسیم شده و برای تمام عناوین از تگ <h6> استفاده شود و تمام تگ ها justify باشد. برای جدا تمام کردن پاراگراف‌ها و هدر ها از تگ <br> استفاده کن.\n"
        prompt = prompt + '\nبدون توضیحات و اضافات\n'
        prompt = prompt + query.prompt
        prompt = prompt + '\n متن اصلی : \n' + request.data["text"]
        
        completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
        response = completion.choices[0].message.content
        # response = model.generate_content(prompt)
        return Response(response.replace('```html','').replace('```',''))

class GBuilderNews(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        result = {}
        service = models.NewsService.objects.get(id = request.data['subject'])
        sub =  models.NewsSubService.objects.get(id = request.data['sub'])
        genai.configure(api_key = settings.GEMINI_KEY)

        model = genai.GenerativeModel("gemini-1.5-flash")

        for item in request.data['sources']:
            site = models.NewsSite.objects.get(id = item)
            # link = models.NewsLink.objects.get(site= site, service=service)
            # if not site.json:
            #     result[service.id] = {}
            #     site.json = {}
            #     loader = WebBaseLoader(
            #             web_path = link.url
            #         )
            #     prompt = service.prompt
            #     prompt = prompt + sub.prompt
                
            #     prompt = prompt + '\n اخبار به دست آمده را به صورت فقط یک لیست جیسون بدون اضافات و توضیحات ارایه کن . هر آیتم لیست باید دارای دو فیلد title , text  باشد . دقت کن که تیتر کوتاه و متن بلند باشد ولی از ۲۰۰ کاراکتر بیشتر نشود\n'

            #     prompt = prompt + f"متن اصلی : {str(loader.load())}"
            #     response = model.generate_content(prompt).text.replace('json', '').replace('```', '').replace('```', '')
            #     response = json.loads(response)
            #     site.json[service.id] = {sub.id : response}  
            #     site.save()
            # elif not str(service.id) in site.json:
            #     loader = WebBaseLoader(
            #             web_path = link.url
            #         )
            #     prompt = service.prompt
            #     prompt = prompt + sub.prompt
                
            #     prompt = prompt + '\n اخبار به دست آمده را به صورت فقط یک لیست جیسون بدون اضافات و توضیحات ارایه کن . هر آیتم لیست باید دارای دو فیلد title , text  باشد . دقت کن که تیتر کوتاه و متن بلند باشد ولی از ۲۰۰ کاراکتر بیشتر نشود\n'

            #     prompt = prompt + f"متن اصلی : {str(loader.load())}"
            #     response = model.generate_content(prompt).text.replace('json', '').replace('```', '').replace('```', '')
            #     response = json.loads(response)
            #     site.json[service.id] = {sub.id : response}  
            #     site.save()
            # elif not str(sub.id) in site.json[str(service.id)]:
            #     loader = WebBaseLoader(
            #             web_path = site.url
            #         )
            #     prompt = service.prompt
            #     prompt = prompt + sub.prompt
                
            #     prompt = prompt + '\n اخبار به دست آمده را به صورت فقط یک لیست جیسون بدون اضافات و توضیحات ارایه کن . هر آیتم لیست باید دارای دو فیلد title , text  باشد . دقت کن که تیتر کوتاه و متن بلند باشد ولی از ۲۰۰ کاراکتر بیشتر نشود\n'

            #     prompt = prompt + f"متن اصلی : {str(loader.load())}"
            #     response = model.generate_content(prompt).text.replace('json', '').replace('```', '').replace('```', '')
            #     response = json.loads(response)
            #     site.json[service.id][sub.id] = response
            #     site.save()
            result[site.name] = site.json[str(service.id)][str(sub.id)]
        model = models.NewsResult.objects.create(text = '', json = result)
        return Response(model.id)
    
    def post(self, request, ids):
        query = models.NewsResult.objects.get(id =ids)
        if query.json != None:
            return Response({'news': query.json, 'id': query.id})
        elif query.text:
            return Response({'text': query.text, 'id': query.id})
        return Response(status = 400)

class GBuilderFile(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        service= models.ImageService.objects.get(id= request.data['id'])
        client = OpenAI(api_key= settings.OPEN_AI_KEY)
        # file = client.files.create( file=open(request.data["file"], "rb"), purpose="fine-tune" ) 
        completion = client.chat.completions.create( model="gpt-4o",
        messages=[ {"role": "system", "content": "You are a helpful assistant that can read image Files and only extract the text inside it and return error in persian if it's not any text in image. به فرمت h6,b,p تبدیل کن. اطمینان حاصل کن که متن به پاراگراف‌های مناسب با تگ‌های <p> تقسیم شده و برای تمام عناوین از تگ <h6> استفاده شود و تمام تگ ها justify باشد. برای جدا تمام کردن پاراگراف‌ها و هدر ها از تگ <br> استفاده کن."}, 
                    { "role": "user", "content": [
                        {
                        "type": "image_url",
                        "image_url": {
                            "url": request.data['file']
                        }
                        }
                    ] 
                    },
                   {"role": "user", "content": service.prompt} ] ) 
        print(completion.choices[0].message) 
        return Response(completion.choices[0].message)

class GBuilderFileManual(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        client = OpenAI(api_key= settings.OPEN_AI_KEY)
        # file = client.files.create( file=open(request.data["file"], "rb"), purpose="fine-tune" ) 
        completion = client.chat.completions.create( model="gpt-4o",
        messages=[ {"role": "system", "content": " .\n"}, 
                    { "role": "user", "content": [
                        {
                        "type": "image_url",
                        "image_url": {
                            "url": request.data['file']
                        }
                        }
                    ] 
                    },
                   {"role": "user", "content": request.data['maintext']} ] ) 
        print(completion.choices[0].message) 
        return Response(completion.choices[0].message)



class GBuilderIdea(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        import logging
        logger = logging.getLogger('django')
        prompt = f'\n return only a json list with title and description with 3 article ideas for {request.data["maintext"]} all in persian'
        logger.info(prompt + '\n')

        # for item in models.IdeaStaticEntry.objects.all():
        #     if request.data["data"]['n' + str(item.id)]:
        #         prompt = prompt + '\n' + item.prompt.replace('$entry', str(request.data["data"]['n' + str(item.id)]))

        
        completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
        response = completion.choices[0].message.content
        # response = model.generate_content(prompt)
        return Response(json.loads(response.replace('```json', '').replace('```', '')))


class Uploader(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = serializers.FileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
        return Response(serializer.data)


class Occasions(APIView):
    def post(self, request):
        date = str(request.data['date'].replace('/','').replace('/','')).replace('/','')
        r = urlopen(f'https://persianholiday.site/api/v1/day?date={date}')
        # r = json.loads(r)
        return Response(json.loads(r.read().decode('utf-8')))



class OccasionBuilder(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, sid):
        modeled = models.NewsResult.objects.create(text = '')
        service = models.OccasionService.objects.get(id=sid)
        prompt = service.prompt
        prompt = prompt + '\n' + 'مناسبت:' + request.data['text']
        prompt =  prompt + "\n به فرمت h6,b,p تبدیل کن. اطمینان حاصل کن که متن به پاراگراف‌های مناسب با تگ‌های <p> تقسیم شده و برای تمام عناوین از تگ <h6> استفاده شود و تمام تگ ها justify باشد. برای جدا تمام کردن پاراگراف‌ها و هدر ها از تگ <br> استفاده کن.\n"
        prompt = prompt + 'بدون توضیحات و اضافات'
        description = model.generate_content(prompt).text
        modeled.text= description.replace('```html', '').replace('```', '')
        modeled.save()
        return Response(modeled.id)
