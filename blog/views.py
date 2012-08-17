import markdown
from django.http import HttpResponse
from django.utils import simplejson as json
from django.views.generic import View
from models import Entry

from google.appengine.ext import db



class JSONResponseMixin(object):
    response_class = HttpResponse

    def render_to_response(self, context, **response_kwargs):
        response_kwargs['content_type'] = 'application/json'
        return self.response_class(
            self.convert_context_to_json(context),
            **response_kwargs
        )

    def convert_context_to_json(self, context):
        return json.dumps(context)


class ApiView(JSONResponseMixin, View):
    
    def get(self, request, *args, **kwargs):
        entry_id = kwargs.get('entry_id')
        if not entry_id:
            entries = db.Query(Entry).order('-pub_date').fetch(limit=6)
            content = [e.to_dict() for e in entries]
        else:
            entry = Entry.get_by_id(int(entry_id))
            if not entry:
                status = 400
                content = create_error_message("Entry with id %s does not exist" %entry_id, status)
                return self.render_to_response(content, status=status)
                
            content = entry.to_dict()
        return self.render_to_response(content)


    def post(self, request, *args,  **kwargs):
        data = json.loads(request.raw_post_data)
        error_msg = ""
        for field in ('title', 'body_markdown'):
            if field not in data or not data[field]:
                error_msg += field + " " 
        if error_msg:
            error_msg = " and ".join(error_msg.split())
            status = 422
            content = create_error_message("%s missing" %error_msg, status)

            return self.render_to_response(content, status=status)
            
        entry = Entry(
            title=data['title'],
            body_markdown=data['body_markdown'],
            body_html=markdown.markdown(data['body_markdown'])
        )
        e = entry.put()
        content = entry.to_dict()
        return self.render_to_response(content)


    def put(self, request, *args, **kwargs):
        entry_id = kwargs.get('entry_id')
        content, error_msg = {}, ""
        if entry_id:
            entry = Entry.get_by_id(int(entry_id))
            if entry:
                data = json.loads(request.raw_post_data)
                for field in ('title', 'body_markdown'):
                    if field not in data or not data[field]:
                        error_msg += field + " " 
                if error_msg:
                    error_msg = " and ".join(error_msg.split())
                    status = 422
                    content = create_error_message("%s missing" %error_msg, status)
                else:
                    for i in ('title', 'body_markdown'):
                        entry.__setattr__(i, data[i])
                    entry.body_html = markdown.markdown(data['body_markdown'])
                    e = entry.put()
                    content = entry.to_dict()
                    return self.render_to_response(content)
            else:
                status = 404
                content = create_error_message("Entry with id %s does not exist" %entry_id, status)
        else:
            status = 400
            content = create_error_message("Specify an Entry instance to modify", status)
        return self.render_to_response(content, status=status)


    def delete(self, request, *args, **kwargs):
        entry_id = kwargs.get('entry_id')
        content = {}
        if entry_id:
            entry = Entry.get_by_id(int(entry_id))
            if entry:
                entry.delete()
                return self.render_to_response(content)
            status = 404
            content = create_error_message("Entry with id %s does not exist" %entry_id, status)
        else:
            status = 400
            content = create_error_message("Specify an Entry instance to delete", status)
        return self.render_to_response(content, status=status)

def create_error_message(msg, code):
    return {"errors": [{"message": msg, "code": code}]}
                        
