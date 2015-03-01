#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
(c) 2013,2015 by Philipp Klaus <philipp.l.klaus →AT→ web.de>.
Check <https://github.com/pklaus/backup-wordpress-blog> for newer versions.
"""

try:
    from wordpress_xmlrpc import Client
    from wordpress_xmlrpc.methods import posts
    from wordpress_xmlrpc.methods import users
    from wordpress_xmlrpc.methods import media
    from wordpress_xmlrpc.exceptions import InvalidCredentialsError

    import unidecode
except ImportError:
    print("You need to install python-wordpress-xmlrpc and unidecode using pip first. Exiting")
    import sys; sys.exit(1)

import datetime as dt
import json
from urllib.parse import urlparse
from urllib.request import urlopen
import shutil
import argparse, os, errno, sys, time, re

def login(site, user, password=None):
    if not user:
        user = input('Please enter the username for the blog %s: ' % site)
    if not password:
        password = input('Please enter the password for the user %s: ' % user)
    return Client(site, user, password)

def sanitize_url(url):
    if not (url.startswith('http://') or url.startswith('https://')):
        url = 'http://' + url
    if not url.endswith('xmlrpc.php'):
        if not url.endswith('/'):
            url += '/'
        url += 'xmlrpc.php'
    return url

def ensure_folder_exists(folder):
    try:
        os.makedirs(folder)
    except OSError as e:
        if not e.errno == errno.EEXIST:
            raise

def post_file_name(post, short=True, extension='txt'):
    status = post.post_status
    slug = post.slug
    if len(slug) == 0 and len(post.title) > 0:
        title = post.title
        # http://stackoverflow.com/a/8366771/183995
        slug = re.sub(r'\W+', '-', unidecode.unidecode(title).lower())
    if short:
        stati = {'draft': 'd', 'private': 'pr', 'publish': 'p'}
        try:
            status = stati[status]
        except:
            pass
        when = post.date.date().isoformat().replace('-','')
        return '%s_%s_%s.%s' % (status, when, slug[:22], extension)
    else:
        when = post.date.isoformat().replace('T','_').replace(':','-')
        return '%s_%s_%s.%s' % (status, when, slug, extension)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Backing up the blog posts of a Wordpress blog to your local file system.')
    parser.add_argument('url', metavar='BLOG_URL',
                        help='The URL of your Wordpress Blog')
    parser.add_argument('--username', '-u',
                        help='Username used to login to your blog.')
    parser.add_argument('--password', '-p',
                        help='Password used to login to your blog.')
    parser.add_argument('--folder', '-f', default='./',
                        help='Folder to store the backups of the blog posts (./).')
    parser.add_argument('--number', '-n', type=int, default=4000,
                        help='Number of blog posts to back up (default is 4000).')
    parser.add_argument('--long-filenames', '-l', action='store_true',
                        help='Use extended filenames for the blog post backup files.')
    parser.add_argument('--media', action='store_true',
                        help='Also backup media files and their metadata.')
    parser.add_argument('--debug', '-d', action='store_true',
                        help='Run in debug mode (used by the developer).')
    parser.add_argument('--extension', '-e', default='txt',
                        help='The file extension of the backed up blog post files (default is txt).')
    args = parser.parse_args()

    site = sanitize_url(args.url)

    wp = login(site, args.username, args.password)

    try:
        wp.call(users.GetUserInfo())
    except InvalidCredentialsError:
        print("Invalid credentials")
        sys.exit(1)

    folder = os.path.abspath(args.folder)
    #folder = os.path.join(folder, dt.date.today().isoformat())

    ensure_folder_exists(folder)

    if args.media:
        media_path = os.path.join(folder, 'media')

        ensure_folder_exists(media_path)

        if args.debug: print("Fetching media library list...")
        media_list = wp.call(media.GetMediaLibrary({}))
        if args.debug: print("The media library contains {} items. Saving them now...".format(len(media_list)))

        for m in media_list:
            m_path = '.' + urlparse(m.link).path
            m_full_path = os.path.join(folder, m_path)
            m_dict = {
              'id': m.id,
              'parent': m.parent,
              'title': m.title,
              'description': m.description,
              'caption': m.caption,
              'date_created': m.date_created.isoformat(),
              'link': m.link,
              'thumbnail': m.thumbnail,
              'metadata': m.metadata,
              'path': m_path
            }
            m_file = open(os.path.join(media_path, '{}.json'.format(m.id)), 'w')
            m_file.write(json.dumps(m_dict))
            m_file.close()
            ensure_folder_exists(os.path.dirname(m_full_path))
            if args.debug: print("Downloading media file {}...".format(m.link))
            with urlopen(m.link) as response, open(m_full_path, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)

    if args.debug: print("Fetching posts now...")
    posts = wp.call(posts.GetPosts({'number': args.number,}))
    if args.debug: print("Fetched {} posts. Saving them now...".format(len(posts)))

    for post in posts:
        tags = [t.name for t in post.terms if t.taxonomy == 'post_tag']
        categories = [t.name for t in post.terms if t.taxonomy == 'category']
        fname = post_file_name(post, short=(not args.long_filenames), extension=args.extension)
        fname = os.path.join(folder, fname)
        f = open(fname, 'w')
        # Alternative: YAML Style Frontmatter
        # inspired by http://egonschiele.github.io/mdpress/
        # See http://jekyllrb.com/docs/frontmatter/
        # and http://en.wikipedia.org/wiki/YAML#Lists
        f.write('# %s\n\n' % post.title)
        f.write('* Categories: %s\n' % ', '.join(categories))
        f.write('* Tags: %s\n' % ', '.join(tags))
        f.write('* Creation Date: %s\n' % post.date.isoformat())
        f.write('* Modification Date: %s\n' % post.date_modified.isoformat())
        f.write('* Link: <%s>\n' % post.link)
        f.write('\n### Content\n\n')
        f.write(post.content)
        f.close()
        cr_time = time.mktime(post.date.timetuple())
        os.utime(fname, (cr_time, cr_time))

    print("Successfully backed up %d blog posts." % len(posts))
