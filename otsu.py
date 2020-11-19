import os
import shutil
import re
import glob
import sys
import json
import datetime
import zlib
import markdown
from markdown.extensions.toc import TocExtension

class Settings():
	def __init__(self):
		default = {
		'theme': 'default',
        'relative': True,
        'base_path': '/',
        'subtitle': 'Lorem Ipsum',
        'author': 'youaresoroman',
        'tags': 'none',
        'site_url': 'http://example.com',
        'list_description': '',
        'current_year': datetime.datetime.now().year,
        'post_posted_on': 'Posted on',
        'post_reading_time': 'minutes to read',
        'post_tags': 'Tags',
        'post_words': 'words',
		}
		self.__SETTINGS = { **default, **self.__get_settings()}

	def __get_settings(self):
		file = open("blog_settings.json")
		return json.load(file)

	def get(self):
		return self.__SETTINGS

class Path_Container():
	def __init__(self, path, src, recursive=False):
		self.__DATA = {
			"path_orig": path,
			"path_relative_root": self.__get_relative_path(path),
			"content_pathnames": self.__get_content_list(src, recursive)
		}

	def __get_relative_path(self, path):
		slash_count = path.count('/')
		if (slash_count == 0):
			return './'
		else:
			return slash_count*'../'

	def __get_content_list(self, src, recursive_do=False):
		return [src_path for src_path in glob.glob(src, recursive=recursive_do)]


	def get(self):
		return self.__DATA

class File_Container():
	def __init__(self, filename):
		self.__FILENAME = filename
		self.__METADATA = self.__get_meta(filename)

	def read(self):
		"""Read file and close the file."""
		with open(self.__FILENAME, 'r') as f:
			return f.read()

	def get_formated_name(self, items):
		return "-".join([self.get_meta_contents(item) for item in items])

	def get_meta_contents(self, item):
		if item in self.__METADATA:
			return self.__METADATA[item]
		else:
			return ''

	def get_meta(self):
		return self.__METADATA

	def __get_meta(self, filename):
		date_content = os.path.basename(filename).split('.')[0]
		match = re.search(r'^(?:(\d\d\d\d-\d\d-\d\d)-)?(.+)$', date_content)
		date = match.group(1) or '1970-01-01'
		unique_id = '{}'.format(zlib.crc32(str.encode( match.group(1) or '1970-01-01' + match.group(2))))[:3]
		short_name = match.group(2)
		return {
			'markdown': filename.endswith(('.md', '.mkd', '.mkdn', '.mdown', '.markdown')),
			'date': date,
			'rfc_2822_date': self.__format_to_rfc_2822(date),
			'short_name': short_name,
			'unique_id': unique_id,
			'formated_name': "-".join([unique_id, short_name])
		}

	def __format_to_rfc_2822(self, date):
		d = datetime.datetime.strptime(date, '%Y-%m-%d')
		return d.strftime('%a, %d %b %Y %H:%M:%S +0000')

	def save(self,content):
		"""Write content to file and close the file."""
		basedir = os.path.dirname(self.__FILENAME)
		if not os.path.isdir(basedir):
			os.makedirs(basedir)

		with open(self.__FILENAME, 'w') as f:
			f.write(content)

class Render():
	def __init__(self, template, params):
		self.__RENDER = self.__render_page(template, params)

	def __render_page(self, template, params):
		return re.sub(r'{{\s*([^}\s]+)\s*}}',
				  lambda match: str(params.get(match.group(1), match.group(0))),
				  template)		

	def get_result(self):
		return self.__RENDER

class Content_Container():
	"""docstring for ClassName"""
	def __init__(self, file: File_Container, params):
		self.__PARAMS = params
		self.__SOURCE = file.read()
		self.__HEADERS = {**self.__get_headers(self.__SOURCE), **file.get_meta()}
		self.__HEADERS['content'] = self.__get_clean_raw(self.__SOURCE, self.__HEADERS['end_pointer'])
		self.__HEADERS['words_count'] = self.__get_words_count(self.__HEADERS['content'])
		self.__HEADERS['reading_time'] = self.__get_reading_time(self.__HEADERS['words_count'])
	
		if 'truncate' in self.__PARAMS and int(self.__PARAMS['truncate']) > 1:
			self.__HEADERS['truncated'] = self.__truncate(self.__HEADERS['content'], self.__PARAMS['truncate'])

		if self.__HEADERS['markdown']:
			self.__HEADERS['content'] = self.__parse_markdown(self.__HEADERS['content'])
		self.__HEADERS.pop('end_pointer')

	def get_data(self):
		return self.__HEADERS

	def get_tags(self):
		return self.__HEADERS['tags'].split(', ')

	def __get_headers(self, content):
		output = {
			"language": "en",
			"tags": "blog"
		}
		for match in re.finditer(r'\s*<!--\s*(.+?)\s*:\s*(.+?)\s*-->\s*|.+', content):
			if not match.group(1):
				break
			if match.group(1) == 'tags' and len(match.group(2)) < 2:
				break
			output[match.group(1)] = match.group(2)
			output['end_pointer'] = match.end()
		return output
		
	def __get_words_count(self, content):
		return len(content.split())

	def __get_reading_time(self, words):
		reading_time = int(words/130)
		if reading_time == 0:
			return 1
		else:
			return reading_time

	def __parse_markdown(self, content, toc_header = "<h1>Table of Contents</h1>\n"):
		if content.find('#') != -1:
			return markdown.markdown(toc_header + "[TOC]\n" + content, extensions=[TocExtension(baselevel=2)])
		else:
			return markdown.markdown(content)

	def __get_clean_raw(self, content, pointer):
		return re.sub('<\!-- .* -->','', content[pointer:])

	def __truncate(self, content, words=25):
		text = re.sub('#|(<h(1|2 id=".*")>.*<\/h(1|2)>|<\!-- .* -->|<div class=\"toc\">(.|\s)*?<\/div>)','', content)
		return ' '.join(re.sub('(?s)<.*?>', ' ', text).split()[:words])


class Layout_Container():
	def __init__(self, path_to_layouts):
		self.__LAYOUTS = self.__get_layouts(path_to_layouts)

	def get_list(self):
		return self.__LAYOUTS

	def read_item(self, item):
		if item in self.__LAYOUTS:
			return File_Container(self.__LAYOUTS[item]).read()
		else:
			return ''

	def __get_layouts(self, path_to_layouts):
		return {os.path.basename(src_path).split('.')[0]: src_path for src_path in glob.glob(path_to_layouts)}

class Content_Helper():
	def __init__(self, settings: Settings, paths: Path_Container):
		self.__CONTENT_LIST = self.__iterate_content(settings, paths)

	def get_content_list(self):
		return self.__CONTENT_LIST

	def __iterate_content(self, settings, paths):
		return [{**settings.get(), **Content_Container(File_Container(path), {"truncate":25}).get_data(), **{"base_path":paths.get()["path_relative_root"], "path_orig":paths.get()["path_orig"]}} for path in paths.get()['content_pathnames']]

class Render_Helper():
	def __init__(self):
		self.__RENDERED = ''
		self.__COUNT = 0

	def stage(self, params, template = ''):
		if self.__COUNT != 0:
			self.__RENDERED = Render(self.__RENDERED, params).get_result()
		else:
			self.__COUNT+=1
			self.__RENDERED = Render(template, params).get_result()

	def get_rendered(self):
		return self.__RENDERED

def render_list(layout: File_Container, content: Content_Helper):
	for content in content.get_content_list():
		render = Render_Helper()
		render.stage({'content':File_Container(layout.get_item('list')).read()}, File_Container(layout.get_item('page')).read())
		render.stage(content)
		File_Container('_site'+content["path_orig"]+content['formated_name']+'/index.html').save(render.get_rendered())
		print('LIST.. ' + content['short_name'])

class Main():
	def __init__(self, settings: Settings):
		self.__SETTINGS = settings
		self.__LAYOUTS = {}
		self.__PATHS = {}
		self.__CONTENT_CONTAINER_LIST = {}

	def add_layout_list(self, layouts_path, name = 'html'):
		self.__LAYOUTS[name] = Layout_Container(layouts_path)

	def add_paths_container(self, name, path_orig, content_path, recursive=False):
		self.__PATHS[name] = Path_Container(path_orig, content_path, recursive)

	def add_content_container(self, path_container_name):
		self.__CONTENT_CONTAINER_LIST[path_container_name] = Content_Helper(self.__SETTINGS, self.__PATHS[path_container_name])

	def render_post(self, content_container_name, layout_container_name = 'html', layout_page_name = 'page', layout_post_name = 'post'):
		for content in self.__CONTENT_CONTAINER_LIST[content_container_name].get_content_list():
			render = Render_Helper()
			render.stage({'content':self.__LAYOUTS[layout_container_name].read_item(layout_post_name)}, self.__LAYOUTS[layout_container_name].read_item(layout_page_name))
			render.stage(content)
			File_Container('_site'+content["path_orig"]+content['formated_name']+'/index.html').save(render.get_rendered())
			print('Rendered.. ' + content['short_name'])

	def render_list(self, content_container_name, layout_container_name = 'html', layout_page_name = 'page', layout_item_name = 'item', layout_list_name = 'list'):
		render_main = Render_Helper()
		render_main.stage({'content':self.__LAYOUTS[layout_container_name].read_item(layout_list_name)}, self.__LAYOUTS[layout_container_name].read_item(layout_page_name))
		items = ''
		list_container = self.__CONTENT_CONTAINER_LIST[content_container_name].get_content_list()
		for content in list_container:
			render = Render_Helper()
			render.stage(content, self.__LAYOUTS[layout_container_name].read_item(layout_item_name))
			items+=render.get_rendered()
		render_main.stage({**list_container[0],"content":items})
		File_Container('_site'+self.__PATHS[content_container_name].get()["path_orig"]+'/index.html').save(render_main.get_rendered())
		print('Rendered list.. ' + content_container_name)