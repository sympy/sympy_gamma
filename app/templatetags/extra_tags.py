from django import template
import urllib
register = template.Library()

@register.inclusion_tag('card.html')
def show_card(cell, input):
    return {'cell': cell, 'input': input}

@register.tag(name='make_query')
def do_make_query(parser, token):
    try:
        tag_name, query = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires a single argument" % token.contents.split()[0])

    return QueryNode(query)

class QueryNode(template.Node):
    def __init__(self, query):
        if query[0] == query[-1] and query[0] in ('"', "'"):
            self.query = query
        else:
            self.query = template.Variable(query)

    def render(self, context):
        if isinstance(self.query, unicode):
            return "/input/?i=" + urllib.quote(self.query[1:-1])
        else:
            return "/input/?i=" + urllib.quote(self.query.resolve(context))

@register.tag(name='make_query_link')
def do_make_query(parser, token):
    try:
        tag_name, query = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires a single argument" % token.contents.split()[0])

    return QueryLinkNode(query)

class QueryLinkNode(template.Node):
    def __init__(self, query):
        if query[0] == query[-1] and query[0] in ('"', "'"):
            self.query = query
        else:
            self.query = template.Variable(query)

    def render(self, context):
        if isinstance(self.query, unicode) or isinstance(self.query, str):
            q = self.query[1:-1]
        else:
            q = self.query.resolve(context)

        link = '<a href="/input/?i={0}">{1}</a>'.format(urllib.quote(q), q)
        return link
