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
