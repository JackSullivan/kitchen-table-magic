import re

def elem(name):
    def f(body, attrs={}, **kwargs):
        attrs = attrs | kwargs
        if 'clazz' in attrs:
            attrs['class'] = attrs['clazz']
            attrs.pop('clazz')
        attr_str = ' '.join(f'{attr}="{str(val)}"' for attr, val in attrs.items())
        if body:
            body = body if isinstance(body, str) else '\n'.join(body)
            body = re.sub('^', '  ', body, flags=re.MULTILINE)
            return "<{} {}>\n{}\n</{}>".format(name, attr_str, body, name)
        else:
            return "<{} {}/>".format(name, attr_str)
    return f

def css(*args):
    rules = []
    for template, format in ((args[i],args[i+1]) for i in range(0,len(args)-1,2)):
        format_str = "\n".join(f"  {k}: {v};" for k,v in format.items())
        rules.append('{} {{\n{}\n}}'.format(template, format_str))
    return '\n\n'.join(rules)

table = elem("table")
tr = elem("tr")
td = elem("td")
img = elem("img")
html =elem('html')
head =elem('head')
body =elem('body')
thead = elem("thead")
tbody = elem("tbody")
div = elem("div")
style = elem("style")
caption = elem("caption")
th = elem("th")
h1 = elem("h1")
h2 = elem("h2")
h3 = elem("h3")
script = elem('script')

common_style = style(css(
    '.binder_container > div', {'padding': '10px',
        'border-radius': '5px',
        'border-color':'black',
        'border':'solid',
        'width':'100%'},
    '.binder_container', {'display':'grid'},
    '.binder', {
        'display':'grid',
        'grid-template-columns':'repeat(6, 1fr)',
        'grid-auto-flow':'row',
        'border-radius': '5px',
        'border-color': 'green',
        'border':'solid'},
    '.binder_pool_cards', {
        'display':'grid',
        'grid-template-columns':'repeat(6, 1fr)',
        'grid-auto-flow':'row',
        'border-radius': '5px',
        'border-color': 'green',
        'border':'solid'},
    '.card', {'object-fit':'contain', 'max-width': '100%', 'height': 'auto'},
    'h1', {'grid-row':1, 'grid-column': '1 / 7'},
    'h2', {'grid-row':1, 'grid-column': '1 / 7'},
    'h3', {'align-items': 'center', 'font-size': '30px'}))
