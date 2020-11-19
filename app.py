import otsu

settings = otsu.Settings()
otsu = otsu.Main(settings)
otsu.add_layout_list('themes/default/layout/*.html', 'html')
otsu.add_layout_list('themes/default/layout/*.xml', 'xml')
otsu.add_paths_container('blog_path', '/blog/', 'content/posts/**/*.md', True)
otsu.add_content_container('blog_path')
otsu.render_post('blog_path')
otsu.render_list('blog_path')