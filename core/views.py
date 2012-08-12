import logging
import markdown
from django.http import Http404, HttpResponse
from django.utils import simplejson as json
from django.conf import settings
from models import Entry

from google.appengine.ext import db

def create(request):
    """
    Returns:
        HttpResponse: containing the newly created Entry instance
    """
    data = json.loads(request.raw_post_data)
    entry = Entry(
        title=data['title'],
        body_markdown=data['body_markdown'],
        body_html=markdown.markdown(data['body_markdown'])
    )
    e = entry.put()
    content = entry.to_dict()
    content['id'] = e.id()
    content = json.dumps(content)
    return HttpResponse(content, mimetype='application/json')


def read(request, entry_id):
    """
    Args:
        entry_id: the id of the Entry
    Returns:
        HttpResponse: containing the Entry instance(if entry_id is matched) or all the Entry instances(if no entry_id is passed)
        Http404: if no Entry with entry_id is matched 
    """
    if not entry_id:
        entries = db.Query(Entry).order('-pub_date').fetch(limit=6)
        content = []
        for e in entries:
            di = e.to_dict()
            di['id'] = e.key().id()
            content.append(di)
    else:
        entry = Entry.get_by_id(int(id))
        if entry:
            content = entry.to_dict()
            content['id'] = entry.key().id()
        raise Http404
    content = json.dumps(content)
    return HttpResponse(content, mimetype='application/json')

 
def update(request, entry_id):
    """
    Args:
        entry_id: the id of the Entry
    Returns:
        HttpResponse containing the updated Entry
        Http404: if no Entry with entry_id was matched
    """
    if entry_id:
        entry = Entry.get_by_id(int(entry_id))
        if entry:
            data = json.loads(request.raw_post_data)
            for i in ('title', 'body_markdown'):
                entry.__setattr__(i, data[i])
            entry.body_html = markdown.markdown(data['body_markdown'])
            e = entry.put()
            content = entry.to_dict()
            content['id'] = e.id()
            content = json.dumps(content)
            return HttpResponse(content, mimetype='application/json')
    raise Http404


def delete(request, entry_id):
    """
    Args:
        entry_id: the id of the Entry
    Returns:
        Http404: if no Entry is matched
        HttpResponse: if an Entry is matched
    """
    if entry_id:
        entry = Entry.get_by_id(int(entry_id))
        if entry:
            entry.delete()
            return HttpResponse()
    raise Http404

CRUDS = {
    'POST': create,
    'GET': read,
    'PUT': update,
    'DELETE': delete
}
 
def crud_dispatcher(request, entry_id=None):
    if request.method == 'POST':
        return create(request)
    return CRUDS[request.method](request, entry_id)
